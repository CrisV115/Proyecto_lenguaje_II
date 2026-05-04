from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone

from certifications.models import Certificate
from courses.models import Course, CourseActivity
from leveling.models import LevelingRecord
from tests_academic.models import Result, Test
from tests_academic.utils import (
    get_course_students_for_teacher,
    get_student_accessible_courses,
    MANAGED_TEST_TYPES,
    get_student_managed_results_queryset,
    get_student_managed_tests_queryset,
    get_teacher_managed_tests_queryset,
    student_has_approved_diagnostic,
)
from tracking.models import Progress
from tracking.services import get_student_progress_entries, sync_student_induction_progress

from .forms import PrimerIngresoPasswordForm
from .models import Usuario


def redirect_user_dashboard(user):
    if getattr(user, "debe_cambiar_password", False):
        return redirect("force_password_change")
    if getattr(user, "tipo_usuario", "") == "profesor":
        return redirect("teacher_dashboard")
    return redirect("student_dashboard")


def home(request):
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)
    return render(request, "home.html")


def register(request):
    messages.warning(
        request,
        "El registro publico esta deshabilitado temporalmente. Los usuarios solo pueden cargarse desde los archivos CSV autorizados.",
    )
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)

    if request.method == "POST":
        login_identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not login_identifier or not password:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("login")

        username = login_identifier
        usuario = Usuario.objects.filter(email__iexact=login_identifier).first()
        if usuario is None:
            usuario = Usuario.objects.filter(cedula=login_identifier).first()
        if usuario is not None:
            username = usuario.username

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuario o contrasena incorrectos.")
            return redirect("login")

        login(request, user)
        request.session.set_expiry(0)
        return redirect_user_dashboard(user)

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Sesion cerrada correctamente.")
    return redirect("home")


@login_required
def force_password_change(request):
    if not request.user.debe_cambiar_password:
        return redirect_user_dashboard(request.user)

    if request.method == "POST":
        form = PrimerIngresoPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.debe_cambiar_password = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contrasena actualizada correctamente.")
            return redirect_user_dashboard(user)
        messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PrimerIngresoPasswordForm(request.user)

    return render(request, "force_password_change.html", {"form": form})


def password_reset_security(request):
    context = {}

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        respuesta = request.POST.get("respuesta_seguridad", "").strip()
        nueva_password = request.POST.get("nueva_password", "")

        usuario = Usuario.objects.filter(email=email).first() if email else None

        if "respuesta_seguridad" not in request.POST:
            if not email:
                messages.error(request, "Debe ingresar un correo.")
                return redirect("password_reset")

            if not usuario:
                messages.error(request, "No existe un usuario con ese correo.")
                return redirect("password_reset")

            context["usuario"] = usuario
            return render(request, "password_reset.html", context)

        if not usuario:
            messages.error(request, "No existe un usuario con ese correo.")
            return redirect("password_reset")

        context["usuario"] = usuario

        if not respuesta or not nueva_password:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "password_reset.html", context)

        if usuario.respuesta_seguridad.lower() != respuesta.lower():
            messages.error(request, "La respuesta no coincide.")
            return render(request, "password_reset.html", context)

        usuario.set_password(nueva_password)
        usuario.save()
        messages.success(request, "Contrasena cambiada correctamente.")
        return redirect("login")

    return render(request, "password_reset.html", context)


def meme(request):
    return render(request, "meme.html")


@login_required
def role_dashboard(request):
    return redirect_user_dashboard(request.user)


@login_required
def student_dashboard(request):
    if request.user.tipo_usuario != "estudiante":
        return redirect_user_dashboard(request.user)

    diagnostic_approved = student_has_approved_diagnostic(request.user)
    sync_student_induction_progress(request.user)
    latest_result = get_student_managed_results_queryset(request.user).select_related("test").first()
    progress_entries = get_student_progress_entries(request.user)
    student_tests = (
        get_student_managed_tests_queryset(request.user)
        .filter(is_active=True)
        .select_related("course")
        .distinct()
        .order_by("available_date", "opening_time", "name")
    )
    now = timezone.localtime()
    active_test = next((test for test in student_tests if _is_test_open_now(test, now)), None)
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()
    calendar_events = _build_student_calendar_events(
        request.user,
        diagnostic_approved=diagnostic_approved,
    )

    return render(
        request,
        "estudiantes.html",
        {
            "latest_result": latest_result,
            "progress_entries": progress_entries,
            "active_test": active_test,
            "certificate": certificate,
            "calendar_events": calendar_events,
            "diagnostic_approved": diagnostic_approved,
        },
    )


@login_required
def teacher_dashboard(request):
    if request.user.tipo_usuario != "profesor":
        return redirect_user_dashboard(request.user)

    teacher_courses = list(
        Course.objects.filter(teachers=request.user)
        .prefetch_related("students")
        .order_by("name")
    )
    course_students = _get_teacher_related_students(request.user, teacher_courses=teacher_courses)

    managed_tests = get_teacher_managed_tests_queryset(request.user)
    tests = managed_tests.select_related("created_by").prefetch_related("questions")[:5]
    recent_results = (
        Result.objects.filter(test__in=managed_tests, student__in=course_students)
        .select_related("student", "test")[:8]
    )
    students = course_students[:8]

    context = {
        "tests_count": managed_tests.count(),
        "active_tests_count": managed_tests.filter(is_active=True).count(),
        "students_count": course_students.count(),
        "results_count": Result.objects.filter(test__in=managed_tests).count(),
        "tests": tests,
        "recent_results": recent_results,
        "students": students,
    }
    return render(request, "teachers/dashboard.html", context)


@login_required
def teacher_test_monitor(request):
    if request.user.tipo_usuario != "profesor":
        return redirect_user_dashboard(request.user)

    teacher_courses = list(
        Course.objects.filter(teachers=request.user)
        .prefetch_related("students")
        .order_by("name")
    )
    students = list(_get_teacher_related_students(request.user, teacher_courses=teacher_courses))
    if not students:
        return render(
            request,
            "teachers/test_monitor.html",
            {
                "rows": [],
                "students_count": 0,
                "diagnostic_taken_count": 0,
                "diagnostic_passed_count": 0,
                "leveling_passed_count": 0,
            },
        )

    course_names_by_student_id = {}
    for course in teacher_courses:
        for student in get_course_students_for_teacher(course, request.user):
            course_names_by_student_id.setdefault(student.id, []).append(course.name)

    for student in students:
        student.assigned_course_names = course_names_by_student_id.get(student.id, [])

    student_ids = [student.id for student in students]

    diagnostic_results = (
        Result.objects.filter(
            student_id__in=student_ids,
            test__type__in=MANAGED_TEST_TYPES,
            test__course__isnull=True,
        )
        .select_related("student", "test")
        .order_by("student_id", "-submitted_at")
    )
    latest_result_by_student = {}
    for result in diagnostic_results:
        latest_result_by_student.setdefault(result.student_id, result)

    leveling_records = {
        record.student_id: record
        for record in LevelingRecord.objects.filter(student_id__in=student_ids).select_related("student")
    }
    leveling_progress_map = {
        progress.student_id: progress
        for progress in Progress.objects.filter(
            student_id__in=student_ids,
            phase=Progress.Phases.LEVELING,
        )
    }

    rows = []
    for student in sorted(students, key=lambda item: item.username.lower()):
        diagnostic_result = latest_result_by_student.get(student.id)
        leveling_record = leveling_records.get(student.id)
        leveling_progress = leveling_progress_map.get(student.id)

        if diagnostic_result is None:
            diagnostic_status = "Sin rendir"
        elif diagnostic_result.passed:
            diagnostic_status = "Aprobado"
        else:
            diagnostic_status = "No aprobado"

        if diagnostic_result is None:
            leveling_status = "No aplica"
        elif diagnostic_result.passed:
            leveling_status = "No requerida"
        elif leveling_record and leveling_record.ready_for_completion:
            leveling_status = "Aprobada"
        elif leveling_record or leveling_progress:
            leveling_status = "En proceso"
        else:
            leveling_status = "Pendiente"

        rows.append(
            {
                "student": student,
                "course_names": ", ".join(student.assigned_course_names) or student.carrera or "Sin carrera",
                "diagnostic_result": diagnostic_result,
                "diagnostic_status": diagnostic_status,
                "leveling_record": leveling_record,
                "leveling_progress": leveling_progress,
                "leveling_status": leveling_status,
            }
        )

    context = {
        "rows": rows,
        "students_count": len(rows),
        "diagnostic_taken_count": sum(1 for row in rows if row["diagnostic_result"]),
        "diagnostic_passed_count": sum(1 for row in rows if row["diagnostic_status"] == "Aprobado"),
        "leveling_passed_count": sum(1 for row in rows if row["leveling_status"] == "Aprobada"),
    }
    return render(request, "teachers/test_monitor.html", context)


def _build_student_calendar_events(student, diagnostic_approved=None):
    now_date = timezone.localdate()
    accessible_courses = get_student_accessible_courses(
        student,
        diagnostic_approved=diagnostic_approved,
    )

    activities = (
        CourseActivity.objects.filter(course__in=accessible_courses, due_date__gte=now_date)
        .select_related("course")
        .distinct()
        .order_by("due_date", "opening_time")[:12]
    )
    tests = (
        Test.objects.filter(available_date__gte=now_date)
        .filter(Q(course__in=accessible_courses) | Q(course__isnull=True))
        .select_related("course")
        .distinct()
        .order_by("available_date", "opening_time", "name")[:12]
    )

    events = []
    for activity in activities:
        events.append(
            {
                "kind": "Actividad",
                "course_name": activity.course.name,
                "title": activity.title,
                "date": activity.due_date,
                "opening_time": activity.opening_time,
                "closing_time": activity.closing_time,
                "url": reverse(
                    "course_activity_submission_module",
                    args=[activity.course.id, activity.id],
                ),
            }
        )
    for test in tests:
        events.append(
            {
                "kind": "Test",
                "course_name": test.course.name if test.course else "Sin nivelacion",
                "title": test.name,
                "date": test.available_date,
                "opening_time": test.opening_time,
                "closing_time": test.closing_time,
                "url": "",
            }
        )

    events.sort(
        key=lambda event: (
            event["date"] or now_date,
            event["opening_time"] or datetime.min.time(),
        )
    )
    return events[:15]


def _get_teacher_related_students(teacher, teacher_courses=None):
    teacher_courses = teacher_courses or []
    course_student_ids = {
        student.id
        for course in teacher_courses
        for student in get_course_students_for_teacher(course, teacher)
    }

    if not course_student_ids:
        return Usuario.objects.none()

    return (
        Usuario.objects.filter(
            tipo_usuario="estudiante",
            id__in=course_student_ids,
        )
        .distinct()
        .order_by("username")
    )


def _is_test_open_now(test, now):
    if not test.available_date or not test.opening_time or not test.closing_time:
        return True
    if now.date() != test.available_date:
        return False
    opening_dt = timezone.make_aware(
        datetime.combine(test.available_date, test.opening_time),
        timezone.get_current_timezone(),
    )
    closing_dt = timezone.make_aware(
        datetime.combine(test.available_date, test.closing_time),
        timezone.get_current_timezone(),
    )
    return opening_dt <= now <= closing_dt

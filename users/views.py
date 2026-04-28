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
from tests_academic.models import Result, Test
from tracking.models import Progress

from .forms import PrimerIngresoPasswordForm, RegistroForm
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
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.email = form.cleaned_data["email"]
            usuario.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("login")

        messages.error(request, "Corrija los errores del formulario.")
    else:
        form = RegistroForm()

    return render(request, "register.html", {"form": form})


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

    latest_result = Result.objects.filter(student=request.user).select_related("test").first()
    progress_entries = Progress.objects.filter(student=request.user).order_by("phase")
    student_tests = (
        Test.objects.filter(is_active=True)
        .filter(Q(course__students=request.user) | Q(course__isnull=True))
        .select_related("course")
        .distinct()
        .order_by("available_date", "opening_time", "name")
    )
    now = timezone.localtime()
    active_test = next((test for test in student_tests if _is_test_open_now(test, now)), None)
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()
    calendar_events = _build_student_calendar_events(request.user)

    return render(
        request,
        "estudiantes.html",
        {
            "latest_result": latest_result,
            "progress_entries": progress_entries,
            "active_test": active_test,
            "certificate": certificate,
            "calendar_events": calendar_events,
        },
    )


@login_required
def teacher_dashboard(request):
    if request.user.tipo_usuario != "profesor":
        return redirect_user_dashboard(request.user)

    teacher_courses = Course.objects.filter(teachers=request.user)
    course_students = (
        Usuario.objects.filter(courses_enrolled__in=teacher_courses, tipo_usuario="estudiante")
        .distinct()
        .order_by("username")
    )

    tests = (
        Test.objects.filter(created_by=request.user)
        .select_related("created_by")
        .prefetch_related("questions")[:5]
    )
    recent_results = (
        Result.objects.filter(test__created_by=request.user)
        .select_related("student", "test")[:8]
    )
    students = course_students[:8]

    context = {
        "tests_count": Test.objects.filter(created_by=request.user).count(),
        "active_tests_count": Test.objects.filter(
            created_by=request.user,
            is_active=True,
        ).count(),
        "students_count": course_students.count(),
        "results_count": Result.objects.filter(test__created_by=request.user).count(),
        "tests": tests,
        "recent_results": recent_results,
        "students": students,
    }
    return render(request, "teachers/dashboard.html", context)


def _build_student_calendar_events(student):
    now_date = timezone.localdate()

    activities = (
        CourseActivity.objects.filter(course__students=student, due_date__gte=now_date)
        .select_related("course")
        .distinct()
        .order_by("due_date", "opening_time")[:12]
    )
    tests = (
        Test.objects.filter(available_date__gte=now_date)
        .filter(Q(course__students=student) | Q(course__isnull=True))
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
                "course_name": test.course.name if test.course else "Sin curso",
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

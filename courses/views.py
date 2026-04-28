from datetime import datetime

from django.contrib import messages
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from tests_academic.models import Result
from tests_academic.utils import get_student_visible_courses, student_has_approved_diagnostic
from users.decorators import role_required
from users.models import Usuario

from .forms import (
    CourseActivityForm,
    CourseActivityGradeForm,
    CourseActivitySubmissionForm,
    CourseClassSessionForm,
)
from .models import (
    Course,
    CourseActivity,
    CourseActivitySubmission,
    CourseClassAttendance,
    CourseClassSession,
)


@role_required("estudiante")
def student_courses(request):
    diagnostic_approved = student_has_approved_diagnostic(request.user)
    courses = get_student_visible_courses(
        request.user,
        diagnostic_approved=diagnostic_approved,
    )
    course_cards = []
    for course in courses:
        progress = _calculate_course_completion(course, request.user)
        course_cards.append(
            {
                "course": course,
                "progress": progress,
            }
        )
    return render(
        request,
        "courses/student_courses.html",
        {
            "course_cards": course_cards,
            "diagnostic_approved": diagnostic_approved,
        },
    )


@role_required("profesor")
def teacher_courses(request):
    courses = request.user.courses_taught.order_by("name")
    return render(request, "courses/teacher_courses.html", {"courses": courses})


@role_required("estudiante", "profesor")
def course_detail(request, course_id):
    course = _get_course_for_user(request.user, course_id)

    students = course.students.order_by("username")
    teachers = course.teachers.order_by("username")
    activities = list(
        course.activities.select_related("created_by")
        .prefetch_related("submissions__student")
        .order_by("due_date", "opening_time")
    )
    tests = course.tests.order_by("available_date", "opening_time", "name")
    if request.user.tipo_usuario == "estudiante":
        tests = tests.filter(is_active=True)

    student_progress = None
    student_submissions = {}
    teacher_progress_rows = []
    if request.user.tipo_usuario == "estudiante":
        student_progress = _calculate_course_completion(course, request.user)
        student_submissions = {
            submission.activity_id: submission
            for submission in CourseActivitySubmission.objects.filter(
                activity__course=course,
                student=request.user,
            )
        }
        for activity in activities:
            activity.student_submission = student_submissions.get(activity.id)
    else:
        teacher_progress_rows = _build_teacher_progress_rows(course, students)

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "students": students,
            "teachers": teachers,
            "activities": activities,
            "tests": tests,
            "student_progress": student_progress,
            "teacher_progress_rows": teacher_progress_rows,
        },
    )


@role_required("estudiante", "profesor")
def course_activities_module(request, course_id):
    course = _get_course_for_user(request.user, course_id)
    activities = list(
        course.activities.select_related("created_by")
        .prefetch_related("submissions__student")
        .order_by("due_date", "opening_time", "id")
    )

    if request.user.tipo_usuario == "estudiante":
        student_submissions = {
            submission.activity_id: submission
            for submission in CourseActivitySubmission.objects.filter(
                activity__course=course,
                student=request.user,
            )
        }
        for activity in activities:
            activity.student_submission = student_submissions.get(activity.id)

    return render(
        request,
        "courses/course_activities_module.html",
        {
            "course": course,
            "activities": activities,
            "activity_form": CourseActivityForm(),
        },
    )


@role_required("estudiante", "profesor")
def course_activity_detail(request, course_id, activity_id):
    return redirect(
        "course_activity_submission_module",
        course_id=course_id,
        activity_id=activity_id,
    )


@role_required("estudiante", "profesor")
def course_activity_submission_module(request, course_id, activity_id):
    course = _get_course_for_user(request.user, course_id)
    activity = get_object_or_404(
        CourseActivity.objects.select_related("course", "created_by"),
        id=activity_id,
        course=course,
    )

    if request.user.tipo_usuario == "estudiante":
        submission = CourseActivitySubmission.objects.filter(
            activity=activity,
            student=request.user,
        ).first()
        submission_form = CourseActivitySubmissionForm(instance=submission)
        student_progress = _calculate_course_completion(course, request.user)
        return render(
            request,
            "courses/course_activity_detail.html",
            {
                "course": course,
                "activity": activity,
                "submission": submission,
                "submission_form": submission_form,
                "student_progress": student_progress,
            },
        )

    submissions = list(
        activity.submissions.select_related("student", "graded_by").order_by("-submitted_at")
    )
    for submission in submissions:
        submission.grade_form = CourseActivityGradeForm(
            prefix=f"submission-{submission.id}",
            instance=submission,
        )
    return render(
        request,
        "courses/course_activity_detail.html",
        {
            "course": course,
            "activity": activity,
            "submissions": submissions,
        },
    )


@role_required("profesor")
def create_course_activity(request, course_id):
    course = get_object_or_404(Course, id=course_id, teachers=request.user)
    if request.method != "POST":
        return redirect("course_activities_module", course_id=course.id)

    form = CourseActivityForm(request.POST, request.FILES)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.course = course
        activity.created_by = request.user
        activity.save()
        messages.success(request, "Actividad creada correctamente.")
    else:
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)

    return redirect("course_activities_module", course_id=course.id)


@role_required("estudiante")
def submit_course_activity(request, course_id, activity_id):
    if request.method != "POST":
        return redirect(
            "course_activity_submission_module",
            course_id=course_id,
            activity_id=activity_id,
        )

    activity = get_object_or_404(
        CourseActivity.objects.select_related("course"),
        id=activity_id,
        course_id=course_id,
        course__in=get_student_visible_courses(request.user),
    )
    form = CourseActivitySubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)
        return redirect(
            "course_activity_submission_module",
            course_id=course_id,
            activity_id=activity_id,
        )

    defaults = {
        "submission_text": form.cleaned_data["submission_text"],
        "submission_url": form.cleaned_data["submission_url"],
    }
    if form.cleaned_data.get("attachment"):
        defaults["attachment"] = form.cleaned_data["attachment"]

    submission, created = CourseActivitySubmission.objects.get_or_create(
        activity=activity,
        student=request.user,
        defaults=defaults,
    )
    if not created:
        submission.submission_text = form.cleaned_data["submission_text"]
        submission.submission_url = form.cleaned_data["submission_url"]
        if form.cleaned_data.get("attachment"):
            submission.attachment = form.cleaned_data["attachment"]
        submission.full_clean()
        submission.save()

    messages.success(
        request,
        "Entrega registrada correctamente." if created else "Entrega actualizada correctamente.",
    )
    return redirect(
        "course_activity_submission_module",
        course_id=course_id,
        activity_id=activity_id,
    )


@role_required("profesor")
def grade_course_activity_submission(request, course_id, activity_id, submission_id):
    if request.method != "POST":
        return redirect(
            "course_activity_submission_module",
            course_id=course_id,
            activity_id=activity_id,
        )

    submission = get_object_or_404(
        CourseActivitySubmission.objects.select_related("activity__course", "student"),
        id=submission_id,
        activity_id=activity_id,
        activity__course_id=course_id,
        activity__course__teachers=request.user,
    )
    form = CourseActivityGradeForm(
        request.POST,
        instance=submission,
        prefix=f"submission-{submission.id}",
    )
    if not form.is_valid():
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)
        return redirect(
            "course_activity_submission_module",
            course_id=course_id,
            activity_id=activity_id,
        )

    graded_submission = form.save(commit=False)
    if graded_submission.grade is not None or graded_submission.teacher_comment:
        graded_submission.graded_by = request.user
        graded_submission.graded_at = timezone.now()
    else:
        graded_submission.graded_by = None
        graded_submission.graded_at = None
    graded_submission.save()
    messages.success(request, f"Calificacion guardada para {submission.student.username}.")
    return redirect(
        "course_activity_submission_module",
        course_id=course_id,
        activity_id=activity_id,
    )


@role_required("profesor")
def course_attendance_module(request, course_id):
    course = get_object_or_404(Course, id=course_id, teachers=request.user)
    students = list(course.students.order_by("last_name", "first_name", "username"))
    sessions = list(course.class_sessions.order_by("session_number", "class_date", "id"))

    if request.method == "POST":
        form = CourseClassSessionForm(request.POST)
        if form.is_valid():
            raw_dates = form.cleaned_data["class_dates"]
            tokens = [item.strip() for item in raw_dates.replace("\n", ",").split(",") if item.strip()]
            if not tokens:
                messages.error(request, "Debes ingresar al menos una fecha de clase.")
                return redirect("course_attendance_module", course_id=course.id)

            parsed_dates = []
            for token in tokens:
                try:
                    parsed_date = datetime.strptime(token, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(request, f"La fecha '{token}' no tiene el formato YYYY-MM-DD.")
                    return redirect("course_attendance_module", course_id=course.id)
                parsed_dates.append(parsed_date)

            existing_dates = set(
                course.class_sessions.filter(class_date__in=parsed_dates).values_list("class_date", flat=True)
            )
            new_dates = sorted(set(parsed_dates) - existing_dates)
            if not new_dates:
                messages.info(request, "No se agregaron clases nuevas. Esas fechas ya estaban registradas.")
                return redirect("course_attendance_module", course_id=course.id)

            next_session_number = (
                course.class_sessions.order_by("-session_number").values_list("session_number", flat=True).first() or 0
            ) + 1
            for class_date in new_dates:
                class_session = CourseClassSession.objects.create(
                    course=course,
                    session_number=next_session_number,
                    class_date=class_date,
                    created_by=request.user,
                )
                attendances = [
                    CourseClassAttendance(
                        class_session=class_session,
                        student=student,
                    )
                    for student in students
                ]
                CourseClassAttendance.objects.bulk_create(attendances)
                next_session_number += 1

            messages.success(request, f"Se registraron {len(new_dates)} clases correctamente.")
            return redirect("course_attendance_module", course_id=course.id)
    else:
        form = CourseClassSessionForm()

    for session in sessions:
        present_count = session.attendances.filter(present=True).count()
        total_students = len(students)
        session.present_count = present_count
        session.total_students = total_students
        session.attendance_percentage = round((present_count * 100 / total_students), 2) if total_students else 0

    return render(
        request,
        "courses/course_attendance_module.html",
        {
            "course": course,
            "session_form": form,
            "sessions": sessions,
        },
    )


@role_required("profesor")
def course_attendance_session_detail(request, course_id, session_id):
    course = get_object_or_404(Course, id=course_id, teachers=request.user)
    session = get_object_or_404(
        CourseClassSession.objects.select_related("course"),
        id=session_id,
        course=course,
    )
    attendances = list(
        session.attendances.select_related("student").order_by("student__last_name", "student__first_name", "student__username")
    )

    if request.method == "POST":
        selected_ids = {
            int(value)
            for value in request.POST.getlist("present_students")
            if value.isdigit()
        }
        changed = 0
        now = timezone.now()
        for attendance in attendances:
            new_value = attendance.student_id in selected_ids
            if attendance.present != new_value:
                changed += 1
            attendance.present = new_value
            attendance.marked_by = request.user
            attendance.marked_at = now
        CourseClassAttendance.objects.bulk_update(
            attendances,
            ["present", "marked_by", "marked_at"],
        )
        messages.success(
            request,
            f"Asistencia guardada correctamente. Registros actualizados: {changed}.",
        )
        return redirect(
            "course_attendance_session_detail",
            course_id=course.id,
            session_id=session.id,
        )

    present_count = sum(1 for attendance in attendances if attendance.present)
    total_students = len(attendances)
    attendance_percentage = round((present_count * 100 / total_students), 2) if total_students else 0

    return render(
        request,
        "courses/course_attendance_session_detail.html",
        {
            "course": course,
            "session": session,
            "attendances": attendances,
            "present_count": present_count,
            "total_students": total_students,
            "attendance_percentage": attendance_percentage,
        },
    )


@role_required("profesor")
def teacher_student_course_detail(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id, teachers=request.user)
    student = get_object_or_404(
        Usuario,
        id=student_id,
        tipo_usuario="estudiante",
        courses_enrolled=course,
    )
    progress = _calculate_course_completion(course, student)

    activities = list(
        course.activities.select_related("created_by")
        .order_by("due_date", "opening_time", "id")
    )
    submissions = {
        submission.activity_id: submission
        for submission in CourseActivitySubmission.objects.filter(
            activity__course=course,
            student=student,
        ).select_related("activity")
    }
    activity_rows = []
    for activity in activities:
        submission = submissions.get(activity.id)
        activity_rows.append(
            {
                "activity": activity,
                "submission": submission,
            }
        )

    tests = list(
        course.tests.order_by("available_date", "opening_time", "name", "id")
    )
    results = {
        result.test_id: result
        for result in Result.objects.filter(
            test__course=course,
            student=student,
        ).select_related("test")
    }
    test_rows = []
    for test in tests:
        result = results.get(test.id)
        test_rows.append(
            {
                "test": test,
                "result": result,
            }
        )

    return render(
        request,
        "courses/teacher_student_detail.html",
        {
            "course": course,
            "student": student,
            "progress": progress,
            "activity_rows": activity_rows,
            "test_rows": test_rows,
        },
    )


def _calculate_course_completion(course, student):
    total_activities = course.activities.count()
    total_tests = course.tests.filter(is_active=True).count()
    total_items = total_activities + total_tests

    completed_activities = CourseActivitySubmission.objects.filter(
        activity__course=course,
        student=student,
    ).count()
    completed_tests = Result.objects.filter(
        test__course=course,
        test__is_active=True,
        student=student,
    ).count()
    completed_items = completed_activities + completed_tests
    percentage = round((completed_items * 100 / total_items), 2) if total_items else 0
    return {
        "total_activities": total_activities,
        "total_tests": total_tests,
        "total_items": total_items,
        "completed_activities": completed_activities,
        "completed_tests": completed_tests,
        "completed_items": completed_items,
        "percentage": percentage,
    }


def _build_teacher_progress_rows(course, students_queryset):
    students = list(students_queryset)
    if not students:
        return []

    total_activities = course.activities.count()
    total_tests = course.tests.filter(is_active=True).count()
    total_items = total_activities + total_tests

    activity_counts = {
        item["student_id"]: item["total"]
        for item in CourseActivitySubmission.objects.filter(
            activity__course=course,
            student__in=students,
        )
        .values("student_id")
        .annotate(total=Count("id"))
    }
    test_counts = {
        item["student_id"]: item["total"]
        for item in Result.objects.filter(
            test__course=course,
            test__is_active=True,
            student__in=students,
        )
        .values("student_id")
        .annotate(total=Count("id"))
    }

    rows = []
    for student in students:
        completed_activities = activity_counts.get(student.id, 0)
        completed_tests = test_counts.get(student.id, 0)
        completed_items = completed_activities + completed_tests
        percentage = round((completed_items * 100 / total_items), 2) if total_items else 0
        rows.append(
            {
                "student": student,
                "completed_activities": completed_activities,
                "completed_tests": completed_tests,
                "completed_items": completed_items,
                "total_items": total_items,
                "percentage": percentage,
            }
        )
    return rows


def _get_course_for_user(user, course_id):
    if user.tipo_usuario == "estudiante":
        visible_courses = get_student_visible_courses(user)
        return get_object_or_404(visible_courses, id=course_id)
    if user.tipo_usuario == "profesor":
        return get_object_or_404(Course, id=course_id, teachers=user)
    raise Http404("No tienes permisos para este curso.")

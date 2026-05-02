from django.db.models import Q

from courses.models import Course

from .models import Result, Test


APPROVED_DIAGNOSTIC_SCORE = 70
MANAGED_TEST_TYPES = ("conocimientos", "vocacional")
COURSE_TEST_TYPE = "curso"


def student_has_approved_diagnostic(student):
    if not getattr(student, "is_authenticated", False):
        return False
    return get_student_managed_results_queryset(student).filter(
        score__gte=APPROVED_DIAGNOSTIC_SCORE,
    ).exists()


def student_has_failed_diagnostic(student):
    if not getattr(student, "is_authenticated", False):
        return False
    student_results = get_student_managed_results_queryset(student)
    return student_results.exists() and not student_results.filter(
        score__gte=APPROVED_DIAGNOSTIC_SCORE,
    ).exists()


def get_student_visible_courses(student, diagnostic_approved=None):
    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    if diagnostic_approved:
        return student.courses_enrolled.filter(is_training=False).none()
    sync_student_course_assignments(student, diagnostic_approved=diagnostic_approved)
    return get_student_leveling_courses(student)


def get_student_training_courses(student):
    if not getattr(student, "is_authenticated", False):
        return Course.objects.none()
    _ensure_training_course_assignments(student)
    return Course.objects.filter(is_training=True).distinct().order_by("name")


def get_student_leveling_courses(student):
    if not getattr(student, "is_authenticated", False):
        return Course.objects.none()

    courses = student.courses_enrolled.filter(is_training=False)
    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return courses.order_by("name")

    matching_courses = courses.filter(
        teachers__tipo_usuario="profesor",
        teachers__carrera__iexact=student.carrera,
    ).distinct()
    if matching_courses.exists():
        return matching_courses.order_by("name")
    return courses.order_by("name")


def get_student_accessible_courses(student, diagnostic_approved=None):
    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    sync_student_course_assignments(student, diagnostic_approved=diagnostic_approved)

    training_courses = get_student_training_courses(student)
    if diagnostic_approved:
        return training_courses

    visible_courses = get_student_leveling_courses(student)
    return Course.objects.filter(
        Q(id__in=visible_courses.values("id"))
        | Q(id__in=training_courses.values("id"))
    ).distinct().order_by("name")


def get_course_teachers_for_student(course, student):
    teachers = course.teachers.filter(tipo_usuario="profesor")
    if course.is_training:
        return teachers.order_by("username")

    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return teachers.order_by("username")

    matching_teachers = teachers.filter(carrera__iexact=student.carrera)
    if matching_teachers.exists():
        return matching_teachers.order_by("username")
    return teachers.order_by("username")


def get_course_students_for_teacher(course, teacher):
    students = course.students.filter(tipo_usuario="estudiante")
    if course.is_training:
        return students.order_by("username")

    teacher_career = _normalize_career(getattr(teacher, "carrera", ""))
    if not teacher_career:
        return students.order_by("username")

    matching_students = students.filter(carrera__iexact=teacher.carrera)
    if matching_students.exists():
        return matching_students.order_by("username")
    return students.order_by("username")


def sync_student_course_assignments(student, diagnostic_approved=None):
    if not getattr(student, "is_authenticated", False):
        return

    _ensure_training_course_assignments(student)
    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    if diagnostic_approved or not student_has_failed_diagnostic(student):
        return
    _ensure_leveling_course_assignments(student)


def _ensure_training_course_assignments(student):
    _enroll_student_in_courses(
        student,
        Course.objects.filter(is_training=True),
    )


def _ensure_leveling_course_assignments(student):
    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return
    _enroll_student_in_courses(
        student,
        Course.objects.filter(
            is_training=False,
            teachers__tipo_usuario="profesor",
            teachers__carrera__iexact=student.carrera,
        ).distinct(),
    )


def _enroll_student_in_courses(student, courses_queryset):
    course_ids = list(courses_queryset.values_list("id", flat=True))
    if course_ids:
        student.courses_enrolled.add(*course_ids)


def _normalize_career(value):
    return (value or "").strip().casefold()


def get_teacher_managed_tests_queryset(user):
    return Test.objects.filter(
        created_by=user,
        type__in=MANAGED_TEST_TYPES,
        course__isnull=True,
    )


def get_teacher_course_tests_queryset(user):
    return Test.objects.filter(course__teachers=user).distinct()


def get_teacher_editable_tests_queryset(user):
    return Test.objects.filter(
        Q(created_by=user, type__in=MANAGED_TEST_TYPES, course__isnull=True)
        | Q(course__teachers=user)
    ).distinct()


def get_student_managed_results_queryset(student):
    return Result.objects.filter(
        student=student,
        test__type__in=MANAGED_TEST_TYPES,
        test__course__isnull=True,
    )


def get_student_managed_tests_queryset(student=None):
    queryset = Test.objects.filter(
        type__in=MANAGED_TEST_TYPES,
        course__isnull=True,
    )
    if student is None:
        return queryset

    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return queryset.none()

    return queryset.filter(created_by__carrera__iexact=student.carrera)

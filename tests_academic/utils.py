from django.db.models import Q

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


def get_student_visible_courses(student, diagnostic_approved=None):
    courses = student.courses_enrolled.order_by("name")
    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    if diagnostic_approved:
        return courses.none()
    return courses


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


def get_student_managed_tests_queryset():
    return Test.objects.filter(
        type__in=MANAGED_TEST_TYPES,
        course__isnull=True,
    )

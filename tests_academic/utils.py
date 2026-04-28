from .models import Result


APPROVED_DIAGNOSTIC_SCORE = 70


def student_has_approved_diagnostic(student):
    if not getattr(student, "is_authenticated", False):
        return False
    return Result.objects.filter(
        student=student,
        score__gte=APPROVED_DIAGNOSTIC_SCORE,
    ).exists()


def get_student_visible_courses(student, diagnostic_approved=None):
    courses = student.courses_enrolled.order_by("name")
    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    if diagnostic_approved:
        return courses.none()
    return courses

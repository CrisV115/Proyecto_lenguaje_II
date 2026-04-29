from django.db.models import Case
from django.db.models import IntegerField
from django.db.models import Value
from django.db.models import When

from courses.models import CourseActivity, CourseActivitySubmission
from tests_academic.models import Result, Test
from tests_academic.utils import get_student_training_courses

from .models import Progress


def get_progress_phase_order():
    return Case(
        When(phase=Progress.Phases.TEST, then=Value(1)),
        When(phase=Progress.Phases.INDUCTION, then=Value(2)),
        When(phase=Progress.Phases.LEVELING, then=Value(3)),
        default=Value(99),
        output_field=IntegerField(),
    )


def get_student_progress_entries(student):
    return (
        Progress.objects.filter(student=student)
        .annotate(phase_order=get_progress_phase_order())
        .order_by("phase_order", "updated_at")
    )


def sync_student_induction_progress(student):
    training_course_ids = list(
        get_student_training_courses(student).values_list("id", flat=True)
    )

    if not training_course_ids:
        Progress.objects.filter(
            student=student,
            phase=Progress.Phases.INDUCTION,
        ).delete()
        return None

    total_activities = CourseActivity.objects.filter(
        course_id__in=training_course_ids
    ).count()
    total_tests = Test.objects.filter(
        course_id__in=training_course_ids,
        is_active=True,
    ).count()
    completed_activities = CourseActivitySubmission.objects.filter(
        activity__course_id__in=training_course_ids,
        student=student,
    ).count()
    completed_tests = Result.objects.filter(
        test__course_id__in=training_course_ids,
        test__is_active=True,
        student=student,
    ).count()

    total_items = total_activities + total_tests
    completed_items = completed_activities + completed_tests
    percentage = round((completed_items * 100 / total_items), 2) if total_items else 0

    progress, _ = Progress.objects.update_or_create(
        student=student,
        phase=Progress.Phases.INDUCTION,
        defaults={
            "completed": total_items > 0 and completed_items >= total_items,
            "percentage": percentage,
        },
    )
    return progress

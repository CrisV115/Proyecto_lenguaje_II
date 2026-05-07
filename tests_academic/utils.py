from django.db.models import Q

from courses.models import Course
from users.career_utils import get_active_teacher_career

from .models import Result, Test


APPROVED_DIAGNOSTIC_SCORE = 70
MANAGED_TEST_TYPES = ("conocimientos", "vocacional")
COURSE_TEST_TYPE = "curso"
DEFAULT_LEVELING_COURSE_NAMES = (
    "Logica Matematica",
    "Linguistica",
    "Geometria",
    "Abstracto",
)


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
    sync_student_course_assignments(student, diagnostic_approved=diagnostic_approved)
    if diagnostic_approved:
        return Course.objects.none()
    return get_student_leveling_courses(student)


def get_student_training_courses(student):
    if not getattr(student, "is_authenticated", False):
        return Course.objects.none()
    _ensure_training_course_assignments(student)
    return Course.objects.filter(is_training=True).distinct().order_by("name")


def get_student_leveling_courses(student):
    if not getattr(student, "is_authenticated", False):
        return Course.objects.none()

    return (
        student.courses_enrolled.filter(
            is_training=False,
            classroom__students=student,
        )
        .select_related("classroom")
        .distinct()
        .order_by("classroom__name", "name")
    )


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

    return teachers.order_by("username")


def get_course_students_for_teacher(course, teacher):
    students = course.students.filter(tipo_usuario="estudiante")
    if course.is_training:
        return students.order_by("username")

    return students.order_by("username")


def sync_student_course_assignments(student, diagnostic_approved=None):
    if not getattr(student, "is_authenticated", False):
        return

    _ensure_default_leveling_courses()

    if diagnostic_approved is None:
        diagnostic_approved = student_has_approved_diagnostic(student)
    current_course_ids = set(student.courses_enrolled.values_list("id", flat=True))
    training_course_ids = set(
        Course.objects.filter(is_training=True).values_list("id", flat=True)
    )

    desired_leveling_ids = set()
    if not diagnostic_approved and student_has_failed_diagnostic(student):
        desired_leveling_ids = set(
            _get_automatic_leveling_courses_queryset(student).values_list("id", flat=True)
        )

    current_leveling_ids = set(
        student.courses_enrolled.filter(is_training=False).values_list("id", flat=True)
    )
    target_course_ids = training_course_ids | desired_leveling_ids
    add_ids = target_course_ids - current_course_ids
    remove_ids = current_leveling_ids - desired_leveling_ids

    if add_ids:
        student.courses_enrolled.add(*add_ids)
    if remove_ids:
        student.courses_enrolled.remove(*remove_ids)


def _ensure_training_course_assignments(student):
    _enroll_student_in_courses(
        student,
        Course.objects.filter(is_training=True),
    )


def _ensure_leveling_course_assignments(student):
    _enroll_student_in_courses(
        student,
        _get_automatic_leveling_courses_queryset(student),
    )


def sync_course_student_assignments(course):
    from users.models import Usuario

    if course.is_training:
        student_ids = list(
            Usuario.objects.filter(tipo_usuario="estudiante").values_list("id", flat=True)
        )
        if student_ids:
            course.students.add(*student_ids)
        return

    if not course.classroom_id:
        course.students.clear()
        return

    candidate_ids = set(
        course.classroom.students.filter(tipo_usuario="estudiante").values_list("id", flat=True)
    )
    course.students.set(candidate_ids)

    for student in Usuario.objects.filter(tipo_usuario="estudiante", id__in=candidate_ids).order_by("id"):
        sync_student_course_assignments(student)


def _enroll_student_in_courses(student, courses_queryset):
    course_ids = list(courses_queryset.values_list("id", flat=True))
    if course_ids:
        student.courses_enrolled.add(*course_ids)


def _get_automatic_leveling_courses_queryset(student):
    classroom_ids = list(student.classrooms.values_list("id", flat=True))
    if not classroom_ids:
        return Course.objects.none()
    return Course.objects.filter(
        is_training=False,
        classroom_id__in=classroom_ids,
    ).distinct()


def _normalize_career(value):
    return (value or "").strip().casefold()


def _ensure_default_leveling_courses():
    default_ids = set()
    for course_name in DEFAULT_LEVELING_COURSE_NAMES:
        course = Course.objects.filter(
            name=course_name,
            is_training=False,
            classroom__isnull=True,
        ).first()
        if course is None:
            course = Course.objects.create(
                name=course_name,
                career="",
                description="",
                is_training=False,
                welcome_message="Bienvenido a este curso.",
            )
        updated_fields = []
        if course.is_training:
            course.is_training = False
            updated_fields.append("is_training")
        if course.career:
            course.career = ""
            updated_fields.append("career")
        if course.classroom_id:
            course.classroom = None
            updated_fields.append("classroom")
        if updated_fields:
            course.save(update_fields=updated_fields)
        default_ids.add(course.id)
    return default_ids


def _get_student_default_leveling_courses(student):
    return (
        student.courses_enrolled.filter(
            is_training=False,
            name__in=DEFAULT_LEVELING_COURSE_NAMES,
        )
        .distinct()
        .order_by("name")
    )


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
        return queryset

    matching_ids = []
    for test in queryset.select_related("created_by"):
        target_career = _normalize_career(getattr(test, "target_career", ""))
        if target_career:
            if target_career == student_career:
                matching_ids.append(test.id)
        elif test.created_by and test.created_by.has_career(student_career):
            matching_ids.append(test.id)
    return queryset.filter(id__in=matching_ids)

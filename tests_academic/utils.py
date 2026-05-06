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
        return _get_student_default_leveling_courses(student)
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

    matching_ids = []
    for course in courses.prefetch_related("teachers"):
        course_career = _normalize_career(getattr(course, "career", ""))
        if course_career and course_career == student_career:
            matching_ids.append(course.id)
            continue
        if any(
            teacher.has_career(student_career)
            for teacher in course.teachers.filter(tipo_usuario="profesor")
        ):
            matching_ids.append(course.id)
    matching_courses = courses.filter(id__in=matching_ids).distinct()
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

    course_career = _normalize_career(getattr(course, "career", ""))
    if course_career:
        return teachers.order_by("username")

    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return teachers.order_by("username")

    matching_teacher_ids = [
        teacher.id for teacher in teachers if teacher.has_career(student_career)
    ]
    if matching_teacher_ids:
        return teachers.filter(id__in=matching_teacher_ids).order_by("username")
    return teachers.order_by("username")


def get_course_students_for_teacher(course, teacher):
    students = course.students.filter(tipo_usuario="estudiante")
    if course.is_training:
        return students.order_by("username")

    course_career = _normalize_career(getattr(course, "career", ""))
    if course_career:
        return students.filter(carrera__iexact=course.career).order_by("username")

    teacher_career = _normalize_career(
        getattr(teacher, "active_career", "") or getattr(teacher, "carrera", "")
    )
    if not teacher_career:
        return students.order_by("username")

    matching_students = students.filter(carrera__iexact=teacher_career)
    if matching_students.exists():
        return matching_students.order_by("username")
    return students.order_by("username")


def sync_student_course_assignments(student, diagnostic_approved=None):
    if not getattr(student, "is_authenticated", False):
        return

    default_leveling_ids = _ensure_default_leveling_courses()

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

    legacy_leveling_ids = set(
        student.courses_enrolled.filter(is_training=False)
        .filter(Q(career__isnull=True) | Q(career=""))
        .values_list("id", flat=True)
    )
    managed_leveling_ids = set(
        student.courses_enrolled.filter(is_training=False)
        .exclude(Q(career__isnull=True) | Q(career=""))
        .values_list("id", flat=True)
    )

    target_course_ids = (
        training_course_ids
        | legacy_leveling_ids
        | desired_leveling_ids
        | default_leveling_ids
    )
    add_ids = target_course_ids - current_course_ids
    remove_ids = managed_leveling_ids - (desired_leveling_ids | default_leveling_ids)

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

    candidate_ids = set(
        course.students.filter(tipo_usuario="estudiante").values_list("id", flat=True)
    )
    course_career = _normalize_career(getattr(course, "career", ""))
    if course_career:
        candidate_ids.update(
            Usuario.objects.filter(
                tipo_usuario="estudiante",
                carrera__iexact=course.career,
            ).values_list("id", flat=True)
        )

    if not candidate_ids:
        return

    for student in Usuario.objects.filter(
        tipo_usuario="estudiante",
        id__in=candidate_ids,
    ).order_by("id"):
        sync_student_course_assignments(student)


def _enroll_student_in_courses(student, courses_queryset):
    course_ids = list(courses_queryset.values_list("id", flat=True))
    if course_ids:
        student.courses_enrolled.add(*course_ids)


def _get_automatic_leveling_courses_queryset(student):
    student_career = _normalize_career(getattr(student, "carrera", ""))
    if not student_career:
        return Course.objects.none()

    matching_ids = set(
        Course.objects.filter(
            is_training=False,
            career__iexact=student.carrera,
        ).values_list("id", flat=True)
    )
    legacy_courses = Course.objects.filter(
        is_training=False,
    ).filter(Q(career__isnull=True) | Q(career="")).prefetch_related("teachers")
    for course in legacy_courses:
        if any(
            teacher.has_career(student_career)
            for teacher in course.teachers.filter(tipo_usuario="profesor")
        ):
            matching_ids.add(course.id)
    return Course.objects.filter(id__in=matching_ids).distinct()


def _normalize_career(value):
    return (value or "").strip().casefold()


def _ensure_default_leveling_courses():
    default_ids = set()
    for course_name in DEFAULT_LEVELING_COURSE_NAMES:
        course, _ = Course.objects.get_or_create(
            name=course_name,
            defaults={
                "career": "",
                "description": "",
                "is_training": False,
                "welcome_message": "Bienvenido a este curso.",
            },
        )
        updated_fields = []
        if course.is_training:
            course.is_training = False
            updated_fields.append("is_training")
        if course.career:
            course.career = ""
            updated_fields.append("career")
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
    queryset = Test.objects.filter(
        created_by=user,
        type__in=MANAGED_TEST_TYPES,
        course__isnull=True,
    )
    active_career = get_active_teacher_career(user)
    active_career = _normalize_career(getattr(user, "active_career", "") or active_career)
    if active_career:
        queryset = queryset.filter(Q(target_career__iexact=active_career) | Q(target_career=""))
    return queryset


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

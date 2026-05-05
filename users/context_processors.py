from tests_academic.utils import get_student_managed_results_queryset
from .career_utils import get_active_teacher_career, get_available_teacher_careers


def leveling_navigation(request):
    show_student_leveling_menu = False

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and getattr(user, "tipo_usuario", "") == "estudiante":
        latest_result = get_student_managed_results_queryset(user).only("score").first()
        show_student_leveling_menu = bool(latest_result and latest_result.score < 70)

    return {
        "show_student_leveling_menu": show_student_leveling_menu,
        "teacher_active_career": get_active_teacher_career(user, request)
        if getattr(user, "is_authenticated", False) and getattr(user, "tipo_usuario", "") == "profesor"
        else "",
        "teacher_available_careers": get_available_teacher_careers(user)
        if getattr(user, "is_authenticated", False) and getattr(user, "tipo_usuario", "") == "profesor"
        else [],
    }

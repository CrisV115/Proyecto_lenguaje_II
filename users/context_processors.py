from tests_academic.utils import get_student_managed_results_queryset


def leveling_navigation(request):
    show_student_leveling_menu = False

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and getattr(user, "tipo_usuario", "") == "estudiante":
        latest_result = get_student_managed_results_queryset(user).only("score").first()
        show_student_leveling_menu = bool(latest_result and latest_result.score < 70)

    return {
        "show_student_leveling_menu": show_student_leveling_menu,
    }

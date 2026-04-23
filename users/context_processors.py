from tests_academic.models import Result


def leveling_navigation(request):
    show_student_leveling_menu = False

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and getattr(user, "tipo_usuario", "") == "estudiante":
        latest_result = Result.objects.filter(student=user).only("score").first()
        show_student_leveling_menu = bool(latest_result and latest_result.score < 70)

    return {
        "show_student_leveling_menu": show_student_leveling_menu,
    }

from typing import Iterable


ACTIVE_TEACHER_CAREER_SESSION_KEY = "active_teacher_career"


def get_available_teacher_careers(user):
    if getattr(user, "tipo_usuario", "") != "profesor":
        return []
    return list(user.get_carreras())


def get_active_teacher_career(user, request=None):
    careers = get_available_teacher_careers(user)
    if not careers:
        return ""

    selected = ""
    if request is not None:
        selected = request.session.get(ACTIVE_TEACHER_CAREER_SESSION_KEY, "")
    if selected in careers:
        return selected
    return careers[0]


def set_active_teacher_career(request, user, career):
    normalized = user.normalize_carrera(career)
    careers = get_available_teacher_careers(user)
    if normalized in careers:
        request.session[ACTIVE_TEACHER_CAREER_SESSION_KEY] = normalized
        return normalized
    return get_active_teacher_career(user, request)


def user_has_career(user, career):
    normalized = user.normalize_carrera(career)
    return normalized in set(user.get_carreras())


def filter_users_by_career(users: Iterable, career):
    return [user for user in users if user_has_career(user, career)]

from django.urls import path

from . import views


urlpatterns = [
    path("estudiante/", views.student_courses, name="student_courses"),
    path("profesor/", views.teacher_courses, name="teacher_courses"),
    path("<int:course_id>/actividades/", views.course_activities_module, name="course_activities_module"),
    path("<int:course_id>/asistencias/", views.course_attendance_module, name="course_attendance_module"),
    path(
        "<int:course_id>/asistencias/clase/<int:session_id>/",
        views.course_attendance_session_detail,
        name="course_attendance_session_detail",
    ),
    path("<int:course_id>/actividades/crear/", views.create_course_activity, name="create_course_activity"),
    path(
        "<int:course_id>/actividades/<int:activity_id>/",
        views.course_activity_detail,
        name="course_activity_detail",
    ),
    path(
        "<int:course_id>/actividades/<int:activity_id>/modulo/",
        views.course_activity_submission_module,
        name="course_activity_submission_module",
    ),
    path(
        "<int:course_id>/actividades/<int:activity_id>/entregar/",
        views.submit_course_activity,
        name="submit_course_activity",
    ),
    path(
        "<int:course_id>/actividades/<int:activity_id>/entregas/<int:submission_id>/calificar/",
        views.grade_course_activity_submission,
        name="grade_course_activity_submission",
    ),
    path(
        "<int:course_id>/estudiantes/<int:student_id>/",
        views.teacher_student_course_detail,
        name="teacher_student_course_detail",
    ),
    path("<int:course_id>/", views.course_detail, name="course_detail"),
]

from django.urls import path

from . import views


urlpatterns = [
    path("estudiante/", views.student_courses, name="student_courses"),
    path("profesor/", views.teacher_courses, name="teacher_courses"),
    path("<int:course_id>/actividades/crear/", views.create_course_activity, name="create_course_activity"),
    path("<int:course_id>/", views.course_detail, name="course_detail"),
]

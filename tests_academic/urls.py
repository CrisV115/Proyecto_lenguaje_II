from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="tests_index"),
    path("take/<int:test_id>/", views.take_test, name="take_test"),
    path("result/<int:test_id>/", views.test_result, name="test_result"),
    path("profesor/tests/", views.teacher_tests, name="teacher_tests"),
    path("profesor/tests/crear/", views.teacher_test_create, name="teacher_test_create"),
    path("profesor/tests/<int:test_id>/editar/", views.teacher_test_edit, name="teacher_test_edit"),
    path("profesor/resultados/", views.teacher_results, name="teacher_results"),
    path("profesor/resultados/<int:result_id>/", views.teacher_result_detail, name="teacher_result_detail"),
    path("profesor/estudiantes/", views.teacher_students, name="teacher_students"),
]

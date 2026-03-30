from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="tests_index"),
    path("take/<int:test_id>/", views.take_test, name="take_test"),
    path("result/<int:test_id>/", views.test_result, name="test_result"),
]

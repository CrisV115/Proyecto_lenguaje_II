from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="leveling_dashboard"),
    path("complete/", views.complete_leveling, name="complete_leveling"),
    path("profesor/", views.teacher_dashboard, name="teacher_leveling_dashboard"),
]

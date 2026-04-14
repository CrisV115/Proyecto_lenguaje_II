from django.urls import path

from . import views


urlpatterns = [
    path("", views.overview, name="tracking_overview"),
    path("induction/", views.induction_dashboard, name="induction_dashboard"),
    path("induction/complete/", views.complete_induction, name="complete_induction"),
    path("induction/constancy/", views.induction_constancy_detail, name="induction_constancy_detail"),
    path("certificate/", views.current_certificate, name="current_certificate"),
    path("report/", views.teacher_report, name="teacher_report"),
]

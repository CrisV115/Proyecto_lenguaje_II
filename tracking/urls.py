from django.urls import path

from . import views


urlpatterns = [
    path("", views.overview, name="tracking_overview"),
    path("certificate/", views.current_certificate, name="current_certificate"),
    path("report/", views.teacher_report, name="teacher_report"),
    path("report/pdf/", views.teacher_report_pdf, name="teacher_report_pdf"),
]

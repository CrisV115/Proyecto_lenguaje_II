from django.urls import path

from . import views


urlpatterns = [
    path("", views.overview, name="tracking_overview"),
    path("induction/", views.induction_dashboard, name="induction_dashboard"),
    path("induction/complete/", views.complete_induction, name="complete_induction"),
    path("certificate/", views.current_certificate, name="current_certificate"),
]

from django.urls import path

from . import views


urlpatterns = [
    path("generate/", views.generate_certificate, name="generate_certificate"),
    path("download/pdf/", views.download_certificate_pdf, name="download_certificate_pdf"),
    path("verify/<uuid:code>/", views.verify_certificate, name="verify_certificate"),
    path("<int:certificate_id>/", views.certificate_detail, name="certificate_detail"),
]

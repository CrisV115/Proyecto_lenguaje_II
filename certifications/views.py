from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import role_required

from .models import Certificate
from .services import (
    build_certificate_pdf,
    get_or_create_completion_certificate,
    get_student_certificate_status,
)


@role_required("estudiante")
def generate_certificate(request):
    certificate_status = get_student_certificate_status(request.user)
    if not certificate_status["eligible"]:
        messages.warning(
            request,
            "Todavia no cumples las condiciones para generar el certificado academico final.",
        )
        return redirect("tracking_overview")

    certificate = get_or_create_completion_certificate(request.user)
    messages.success(request, "Certificado listo para descarga.")

    return render(
        request,
        "certifications/certificate.html",
        {
            "certificate": certificate,
            "certificate_status": certificate_status,
        },
    )


@role_required("estudiante")
def certificate_detail(request, certificate_id):
    certificate = get_object_or_404(
        Certificate,
        id=certificate_id,
        student=request.user,
    )
    return render(
        request,
        "certifications/certificate.html",
        {
            "certificate": certificate,
            "certificate_status": get_student_certificate_status(request.user),
        },
    )


@role_required("estudiante")
def download_certificate_pdf(request):
    certificate_status = get_student_certificate_status(request.user)
    if not certificate_status["eligible"]:
        messages.warning(
            request,
            "Todavia no puedes descargar el certificado. Primero debes aprobar el test diagnostico o, si no lo apruebas, aprobar la nivelacion.",
        )
        return redirect("tracking_overview")

    certificate = get_or_create_completion_certificate(request.user)
    pdf_buffer = build_certificate_pdf(request.user, certificate, request)
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="certificado_{request.user.username}.pdf"'
    )
    return response


def verify_certificate(request, code):
    certificate = Certificate.objects.filter(code=code).select_related("student").first()
    return render(
        request,
        "certifications/verify_certificate.html",
        {"certificate": certificate},
    )

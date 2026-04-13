from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from tracking.models import Progress
from users.decorators import role_required

from .models import Certificate


@role_required("estudiante")
def generate_certificate(request):
    induction_ready = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.INDUCTION,
        completed=True,
    ).exists()
    leveling_ready = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.LEVELING,
        completed=True,
    ).exists()

    if not induction_ready and not leveling_ready:
        messages.warning(
            request,
            "Todavia no cumples las condiciones para generar el certificado.",
        )
        return redirect("student_dashboard")

    source_phase = (
        Progress.Phases.INDUCTION if induction_ready else Progress.Phases.LEVELING
    )

    certificate, created = Certificate.objects.get_or_create(
        student=request.user,
        valid=True,
        defaults={"source_phase": source_phase},
    )
    if not created and certificate.source_phase != source_phase:
        certificate.source_phase = source_phase
        certificate.save(update_fields=["source_phase"])

    if created:
        messages.success(request, "Certificado generado correctamente.")

    return render(
        request,
        "certifications/certificate.html",
        {"certificate": certificate},
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
        {"certificate": certificate},
    )

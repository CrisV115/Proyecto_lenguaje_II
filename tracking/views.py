from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from certifications.models import Certificate

from .models import Progress


@login_required
def overview(request):
    progress_entries = Progress.objects.filter(student=request.user).order_by("phase")
    return render(
        request,
        "tracking/overview.html",
        {"progress_entries": progress_entries},
    )


@login_required
def induction_dashboard(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.INDUCTION,
    ).first()
    if progress is None:
        messages.info(request, "Aun no tienes la fase de induccion habilitada.")
        return redirect("student_dashboard")
    return render(request, "tracking/induction.html", {"progress": progress})


@login_required
def complete_induction(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.INDUCTION,
    ).first()
    if progress is None:
        messages.warning(request, "No existe una fase de induccion para completar.")
        return redirect("student_dashboard")
    progress.percentage = 100
    progress.completed = True
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    messages.success(request, "Induccion completada correctamente.")
    return redirect("generate_certificate")


@login_required
def current_certificate(request):
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()
    if certificate is None:
        messages.info(
            request,
            "Todavia no tienes un certificado generado. Completa tu ruta academica primero.",
        )
        return redirect("student_dashboard")
    return redirect("certificate_detail", certificate_id=certificate.id)

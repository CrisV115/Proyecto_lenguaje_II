from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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
    progress = get_object_or_404(
        Progress,
        student=request.user,
        phase=Progress.Phases.INDUCTION,
    )
    return render(request, "tracking/induction.html", {"progress": progress})


@login_required
def complete_induction(request):
    progress = get_object_or_404(
        Progress,
        student=request.user,
        phase=Progress.Phases.INDUCTION,
    )
    progress.percentage = 100
    progress.completed = True
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    messages.success(request, "Inducción completada correctamente.")
    return redirect("generate_certificate")


@login_required
def current_certificate(request):
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()
    if certificate is None:
        messages.info(
            request,
            "Todavía no tienes un certificado generado. Completa tu ruta académica primero.",
        )
        return redirect("student_dashboard")
    return redirect("certificate_detail", certificate_id=certificate.id)

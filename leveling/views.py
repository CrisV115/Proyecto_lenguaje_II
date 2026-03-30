from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from tracking.models import Progress


@login_required
def dashboard(request):
    progress = get_object_or_404(
        Progress,
        student=request.user,
        phase=Progress.Phases.LEVELING,
    )
    return render(request, "leveling/dashboard.html", {"progress": progress})


@login_required
def complete_leveling(request):
    progress = get_object_or_404(
        Progress,
        student=request.user,
        phase=Progress.Phases.LEVELING,
    )
    progress.percentage = 100
    progress.completed = True
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    messages.success(request, "Nivelación completada correctamente.")
    return redirect("generate_certificate")

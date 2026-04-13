from django.contrib import messages
from django.shortcuts import redirect, render

from tracking.models import Progress
from users.decorators import role_required


@role_required("estudiante")
def dashboard(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.LEVELING,
    ).first()
    if progress is None:
        messages.info(request, "Aun no tienes la fase de nivelacion habilitada.")
        return redirect("student_dashboard")
    return render(request, "leveling/dashboard.html", {"progress": progress})


@role_required("estudiante")
def complete_leveling(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.LEVELING,
    ).first()
    if progress is None:
        messages.warning(request, "No existe una fase de nivelacion para completar.")
        return redirect("student_dashboard")
    progress.percentage = 100
    progress.completed = True
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    messages.success(request, "Nivelacion completada correctamente.")
    return redirect("generate_certificate")

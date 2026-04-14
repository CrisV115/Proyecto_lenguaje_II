from django.contrib import messages
from django.shortcuts import redirect, render

from tracking.models import Progress
from users.decorators import role_required

from .models import LevelingRecord


@role_required("estudiante")
def dashboard(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.LEVELING,
    ).first()
    if progress is None:
        messages.info(request, "Aun no tienes la fase de nivelacion habilitada.")
        return redirect("student_dashboard")

    record, _ = LevelingRecord.objects.get_or_create(student=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "sync_attendance":
            if record.synchronous_sessions_attended < record.synchronous_sessions_total:
                record.synchronous_sessions_attended += 1
                messages.success(request, "Asistencia sincronica registrada.")
            else:
                messages.info(request, "Ya registraste todas las sesiones sincronicas requeridas.")
        elif action == "async_activity":
            if record.asynchronous_activities_completed < record.asynchronous_activities_total:
                record.asynchronous_activities_completed += 1
                messages.success(request, "Actividad asincronica registrada.")
            else:
                messages.info(request, "Ya registraste todas las actividades asincronicas.")
        elif action == "exam_score":
            try:
                exam_score = float(request.POST.get("final_exam_score", 0))
            except (TypeError, ValueError):
                exam_score = 0
            record.final_exam_score = max(0, min(100, exam_score))
            messages.success(request, "Resultado del examen final actualizado.")

        record.save()
        return redirect("leveling_dashboard")

    progress.percentage = record.participation_percentage
    progress.completed = record.ready_for_completion
    progress.save(update_fields=["percentage", "completed", "updated_at"])

    return render(
        request,
        "leveling/dashboard.html",
        {"progress": progress, "record": record},
    )


@role_required("estudiante")
def complete_leveling(request):
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.LEVELING,
    ).first()
    if progress is None:
        messages.warning(request, "No existe una fase de nivelacion para completar.")
        return redirect("student_dashboard")

    record = LevelingRecord.objects.filter(student=request.user).first()
    if record is None or not record.ready_for_completion:
        messages.warning(
            request,
            "Para completar nivelacion debes alcanzar al menos 70% de participacion y aprobar el examen final.",
        )
        return redirect("leveling_dashboard")

    progress.percentage = 100
    progress.completed = True
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    messages.success(request, "Nivelacion completada correctamente.")
    return redirect("generate_certificate")

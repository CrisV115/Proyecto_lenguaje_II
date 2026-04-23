from django.contrib import messages
from django.db.models import OuterRef, Subquery
from django.shortcuts import redirect, render

from tests_academic.models import Result
from tracking.models import Progress
from users.decorators import role_required
from users.models import Usuario

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


@role_required("profesor")
def teacher_dashboard(request):
    latest_results = Result.objects.filter(student=OuterRef("pk")).order_by("-submitted_at")
    leveling_progress = Progress.objects.filter(
        student=OuterRef("pk"),
        phase=Progress.Phases.LEVELING,
    )

    students = (
        Usuario.objects.filter(tipo_usuario="estudiante")
        .annotate(
            latest_score=Subquery(latest_results.values("score")[:1]),
            latest_test_name=Subquery(latest_results.values("test__name")[:1]),
            leveling_percentage=Subquery(leveling_progress.values("percentage")[:1]),
            leveling_completed=Subquery(leveling_progress.values("completed")[:1]),
        )
        .order_by("username")
    )

    students_in_leveling = []
    for student in students:
        if student.latest_score is None or student.latest_score >= 70:
            continue

        record = LevelingRecord.objects.filter(student=student).first()
        students_in_leveling.append(
            {
                "student": student,
                "latest_score": round(student.latest_score / 10, 2),
                "latest_test_name": student.latest_test_name,
                "leveling_percentage": student.leveling_percentage or 0,
                "leveling_completed": bool(student.leveling_completed),
                "record": record,
            }
        )

    return render(
        request,
        "leveling/teacher_dashboard.html",
        {
            "students_in_leveling": students_in_leveling,
        },
    )

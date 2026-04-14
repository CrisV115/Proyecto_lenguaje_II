from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from certifications.models import Certificate
from leveling.models import LevelingRecord
from tests_academic.models import Result
from users.decorators import role_required
from users.models import Usuario

from .models import (
    InductionConstancy,
    InductionModule,
    InductionParticipation,
    Progress,
)


@role_required("estudiante")
def overview(request):
    progress_entries = Progress.objects.filter(student=request.user).order_by("phase")
    return render(
        request,
        "tracking/overview.html",
        {"progress_entries": progress_entries},
    )


@role_required("estudiante")
def induction_dashboard(request):
    _ensure_default_induction_modules()
    progress = Progress.objects.filter(
        student=request.user,
        phase=Progress.Phases.INDUCTION,
    ).first()
    if progress is None:
        messages.info(request, "Aun no tienes la fase de induccion habilitada.")
        return redirect("student_dashboard")

    if request.method == "POST":
        module = get_object_or_404(InductionModule, id=request.POST.get("module_id"))
        participation, _ = InductionParticipation.objects.get_or_create(
            student=request.user,
            module=module,
        )
        action = request.POST.get("action")

        if action == "attend":
            participation.attended = True
            participation.attended_at = timezone.now()
            participation.save(update_fields=["attended", "attended_at"])
            messages.success(request, "Asistencia registrada correctamente.")
        elif action == "complete":
            if not participation.attended:
                messages.warning(
                    request,
                    "Primero debes registrar la asistencia del modulo antes de completar la participacion.",
                )
            else:
                participation.completed = True
                participation.completed_at = timezone.now()
                participation.save(update_fields=["completed", "completed_at"])
                messages.success(request, "Participacion registrada correctamente.")

        return redirect("induction_dashboard")

    modules = list(
        InductionModule.objects.prefetch_related(
            Prefetch(
                "participations",
                queryset=InductionParticipation.objects.filter(student=request.user),
            )
        )
    )
    completed_required = 0
    required_total = sum(1 for module in modules if module.required)

    for module in modules:
        participation = next(iter(module.participations.all()), None)
        module.student_participation = participation
        module.student_attended = bool(participation and participation.attended)
        module.student_completed = bool(participation and participation.completed)
        if module.required and module.student_attended and module.student_completed:
            completed_required += 1

    percentage = round((completed_required / required_total) * 100, 2) if required_total else 0
    is_completed = required_total > 0 and completed_required == required_total

    progress.percentage = percentage
    progress.completed = is_completed
    progress.save(update_fields=["percentage", "completed", "updated_at"])

    constancy = None
    if is_completed:
        constancy, _ = InductionConstancy.objects.get_or_create(student=request.user, valid=True)

    context = {
        "progress": progress,
        "modules": modules,
        "required_total": required_total,
        "completed_required": completed_required,
        "constancy": constancy,
    }
    return render(request, "tracking/induction.html", context)


@role_required("estudiante")
def complete_induction(request):
    messages.info(
        request,
        "La induccion se completa registrando asistencia y participacion en todos los modulos obligatorios.",
    )
    return redirect("induction_dashboard")


@role_required("estudiante")
def current_certificate(request):
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()
    if certificate is None:
        messages.info(
            request,
            "Todavia no tienes un certificado generado. Completa tu ruta academica primero.",
        )
        return redirect("student_dashboard")
    return redirect("certificate_detail", certificate_id=certificate.id)


@role_required("estudiante")
def induction_constancy_detail(request):
    constancy = InductionConstancy.objects.filter(student=request.user, valid=True).first()
    if constancy is None:
        messages.info(
            request,
            "Completa todos los modulos de induccion para generar tu constancia automatica.",
        )
        return redirect("induction_dashboard")
    return render(
        request,
        "tracking/induction_constancy.html",
        {"constancy": constancy},
    )


@role_required("profesor")
def teacher_report(request):
    students = list(
        Usuario.objects.filter(tipo_usuario="estudiante")
        .order_by("username")
        .prefetch_related(
            Prefetch("results", queryset=Result.objects.select_related("test").order_by("-submitted_at")),
            Prefetch("progress_entries", queryset=Progress.objects.order_by("phase")),
            Prefetch(
                "induction_participations",
                queryset=InductionParticipation.objects.select_related("module"),
            ),
            Prefetch("induction_constancies", queryset=InductionConstancy.objects.filter(valid=True)),
            Prefetch("certificates", queryset=Certificate.objects.filter(valid=True)),
        )
    )

    leveling_records = {
        record.student_id: record
        for record in LevelingRecord.objects.select_related("student")
    }

    report_rows = []
    for student in students:
        latest_result = student.results.all()[0] if student.results.all() else None
        progress_map = {entry.phase: entry for entry in student.progress_entries.all()}
        induction_required = sum(
            1
            for item in student.induction_participations.all()
            if item.module.required
        )
        induction_completed = sum(
            1
            for item in student.induction_participations.all()
            if item.module.required and item.attended and item.completed
        )
        constancy = student.induction_constancies.all()[0] if student.induction_constancies.all() else None
        certificate = student.certificates.all()[0] if student.certificates.all() else None
        leveling_record = leveling_records.get(student.id)

        report_rows.append(
            {
                "student": student,
                "latest_result": latest_result,
                "test_progress": progress_map.get(Progress.Phases.TEST),
                "induction_progress": progress_map.get(Progress.Phases.INDUCTION),
                "induction_required": induction_required,
                "induction_completed": induction_completed,
                "constancy": constancy,
                "leveling_progress": progress_map.get(Progress.Phases.LEVELING),
                "leveling_record": leveling_record,
                "certificate": certificate,
            }
        )

    context = {
        "report_rows": report_rows,
        "students_count": len(report_rows),
        "certified_count": sum(1 for row in report_rows if row["certificate"]),
        "induction_completed_count": sum(
            1 for row in report_rows if row["induction_progress"] and row["induction_progress"].completed
        ),
        "leveling_completed_count": sum(
            1 for row in report_rows if row["leveling_progress"] and row["leveling_progress"].completed
        ),
    }
    return render(request, "tracking/teacher_report.html", context)


def _ensure_default_induction_modules():
    if InductionModule.objects.exists():
        return

    modules = [
        {
            "title": "Bienvenida institucional",
            "description": "Presentacion del instituto, servicios estudiantiles y normativa basica de ingreso.",
            "modality": InductionModule.Modalities.SYNCHRONOUS,
            "order": 1,
        },
        {
            "title": "Uso de plataformas academicas",
            "description": "Recorrido guiado por PAO, SGA y Microsoft Teams con registro de asistencia digital.",
            "modality": InductionModule.Modalities.SYNCHRONOUS,
            "order": 2,
        },
        {
            "title": "Ruta academica y acompanamiento",
            "description": "Actividad asincronica para revisar procesos, calendario y canales oficiales de soporte.",
            "modality": InductionModule.Modalities.ASYNCHRONOUS,
            "order": 3,
        },
        {
            "title": "Confirmacion final de induccion",
            "description": "Cierre del proceso con lectura de lineamientos y validacion final de participacion.",
            "modality": InductionModule.Modalities.ASYNCHRONOUS,
            "order": 4,
        },
    ]
    for module_data in modules:
        InductionModule.objects.create(**module_data)

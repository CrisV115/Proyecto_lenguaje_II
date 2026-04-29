from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import redirect, render

from certifications.models import Certificate
from certifications.services import get_student_certificate_status
from leveling.models import LevelingRecord
from tests_academic.models import Result
from tests_academic.utils import MANAGED_TEST_TYPES
from users.decorators import role_required
from users.models import Usuario

from .models import Progress
from .services import get_student_progress_entries, sync_student_induction_progress


@role_required("estudiante")
def overview(request):
    sync_student_induction_progress(request.user)
    progress_entries = get_student_progress_entries(request.user)
    certificate_status = get_student_certificate_status(request.user)
    return render(
        request,
        "tracking/overview.html",
        {
            "progress_entries": progress_entries,
            "certificate_status": certificate_status,
        },
    )


@role_required("estudiante")
def current_certificate(request):
    certificate = (
        Certificate.objects.filter(
            student=request.user,
            valid=True,
            source_phase="completion",
        ).first()
        or Certificate.objects.filter(student=request.user, valid=True).first()
    )
    if certificate is None:
        messages.info(
            request,
            "Todavia no tienes un certificado generado. Completa tu ruta academica primero.",
        )
        return redirect("student_dashboard")
    return redirect("certificate_detail", certificate_id=certificate.id)


@role_required("profesor")
def teacher_report(request):
    students = list(
        Usuario.objects.filter(tipo_usuario="estudiante")
        .order_by("username")
        .prefetch_related(
            Prefetch(
                "results",
                queryset=Result.objects.select_related("test")
                .filter(test__type__in=MANAGED_TEST_TYPES, test__course__isnull=True)
                .order_by("-submitted_at"),
            ),
            Prefetch("progress_entries", queryset=Progress.objects.order_by("phase")),
            Prefetch("certificates", queryset=Certificate.objects.filter(valid=True)),
        )
    )

    leveling_records = {
        record.student_id: record
        for record in LevelingRecord.objects.select_related("student")
    }

    report_rows = []
    for student in students:
        student_results = list(student.results.all())
        student_certificates = list(student.certificates.all())
        latest_result = student_results[0] if student_results else None
        progress_map = {entry.phase: entry for entry in student.progress_entries.all()}
        certificate = student_certificates[0] if student_certificates else None
        leveling_record = leveling_records.get(student.id)

        report_rows.append(
            {
                "student": student,
                "latest_result": latest_result,
                "initial_result_approved": bool(latest_result and latest_result.passed),
                "leveling_progress": progress_map.get(Progress.Phases.LEVELING),
                "leveling_record": leveling_record,
                "certificate": certificate,
            }
        )

    context = {
        "report_rows": report_rows,
        "students_count": len(report_rows),
        "certified_count": sum(1 for row in report_rows if row["certificate"]),
        "approved_initial_count": sum(
            1 for row in report_rows if row["initial_result_approved"]
        ),
        "leveling_completed_count": sum(
            1 for row in report_rows if row["leveling_progress"] and row["leveling_progress"].completed
        ),
    }
    return render(request, "tracking/teacher_report.html", context)

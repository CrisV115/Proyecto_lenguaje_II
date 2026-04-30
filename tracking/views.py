from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.utils import timezone

from certifications.models import Certificate
from certifications.services import get_student_certificate_status
from leveling.models import LevelingRecord
from tests_academic.models import Result
from users.decorators import role_required
from users.models import Usuario

from .models import Progress
from .services import (
    build_teacher_report_pdf,
    get_student_progress_entries,
    sync_student_induction_progress,
)


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
    return render(
        request,
        "tracking/teacher_report.html",
        _build_teacher_report_context(),
    )


@role_required("profesor")
def teacher_report_pdf(request):
    context = _build_teacher_report_context()
    generated_at = timezone.localtime().strftime("%d/%m/%Y %H:%M")
    pdf_buffer = build_teacher_report_pdf(context["report_rows"], generated_at)
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_seguimiento_docente.pdf"'
    return response


def _build_teacher_report_context():
    students = list(
        Usuario.objects.filter(tipo_usuario="estudiante")
        .order_by("last_name", "first_name", "username")
        .prefetch_related(
            Prefetch(
                "results",
                queryset=Result.objects.select_related("test")
                .filter(
                    test__type="conocimientos",
                    test__course__isnull=True,
                )
                .order_by("-submitted_at"),
                to_attr="diagnostic_results",
            )
        )
    )

    report_rows = []
    for student in students:
        latest_result = student.diagnostic_results[0] if student.diagnostic_results else None
        if latest_result is None:
            continue

        report_rows.append(
            {
                "student": student,
                "cedula": student.cedula or "-",
                "first_name": student.first_name or student.username,
                "last_name": student.last_name or "-",
                "diagnostic_result": latest_result,
                "status_label": "Aprobado" if latest_result.passed else "Reprobado",
            }
        )

    approved_count = sum(
        1 for row in report_rows if row["diagnostic_result"].passed
    )
    failed_count = len(report_rows) - approved_count

    return {
        "report_rows": report_rows,
        "students_count": len(report_rows),
        "approved_count": approved_count,
        "failed_count": failed_count,
    }

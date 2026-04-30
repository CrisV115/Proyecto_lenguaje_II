from io import BytesIO
from pathlib import Path

import qrcode
from qrcode.image.svg import SvgImage
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from leveling.models import LevelingRecord
from tests_academic.utils import get_student_managed_results_queryset
from tracking.models import Progress

from .models import Certificate


COMPLETION_SOURCE_PHASE = "completion"
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def get_student_certificate_status(student):
    diagnostic_results = get_student_managed_results_queryset(student).select_related("test")
    diagnostic_result = diagnostic_results.first()
    approved_diagnostic_result = diagnostic_results.filter(passed=True).first()
    diagnostic_attempted = diagnostic_result is not None
    diagnostic_passed = approved_diagnostic_result is not None

    leveling_progress = Progress.objects.filter(
        student=student,
        phase=Progress.Phases.LEVELING,
    ).first()
    leveling_record = LevelingRecord.objects.filter(student=student).first()

    leveling_attempted = False
    if leveling_record is not None:
        leveling_attempted = any(
            [
                leveling_record.synchronous_sessions_attended > 0,
                leveling_record.asynchronous_activities_completed > 0,
                leveling_record.final_exam_score > 0,
            ]
        )
    leveling_passed = bool(
        (leveling_progress and leveling_progress.completed)
        or (leveling_record and leveling_record.ready_for_completion)
    )

    needs_leveling = diagnostic_attempted and not diagnostic_passed

    missing_items = []
    if not diagnostic_attempted:
        missing_items.append("rendir el test diagnostico")
    elif needs_leveling and not leveling_attempted:
        missing_items.append("completar la nivelacion")

    pending_items = []
    if needs_leveling and leveling_attempted and not leveling_passed:
        pending_items.append("aprobar la nivelacion")

    eligible = diagnostic_passed or (needs_leveling and leveling_passed)
    qualifying_path = ""
    if diagnostic_passed:
        qualifying_path = "diagnostico"
    elif eligible:
        qualifying_path = "nivelacion"

    return {
        "diagnostic_result": approved_diagnostic_result or diagnostic_result,
        "diagnostic_attempted": diagnostic_attempted,
        "diagnostic_passed": diagnostic_passed,
        "leveling_progress": leveling_progress,
        "leveling_record": leveling_record,
        "leveling_attempted": leveling_attempted,
        "leveling_passed": leveling_passed,
        "needs_leveling": needs_leveling,
        "eligible": eligible,
        "qualifying_path": qualifying_path,
        "missing_items": missing_items,
        "pending_items": pending_items,
    }


def get_or_create_completion_certificate(student):
    certificate, _ = Certificate.objects.get_or_create(
        student=student,
        valid=True,
        source_phase=COMPLETION_SOURCE_PHASE,
    )
    return certificate


def build_certificate_pdf(student, certificate, request):
    from reportlab.graphics import renderPDF
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from svglib.svglib import svg2rlg

    primary = colors.HexColor("#7c3aed")
    primary_deep = colors.HexColor("#5b21b6")
    header_bg = colors.HexColor("#52347e")
    muted = colors.HexColor("#6f6291")
    surface = colors.HexColor("#fffdf4")
    text = colors.HexColor("#24143f")

    try:
        return _build_styled_certificate_pdf(student, certificate, request)
    except Exception:
        return _build_basic_pdf(student, certificate, request)


def _build_styled_certificate_pdf(student, certificate, request):
    _register_pdf_fonts()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle("Certificado academico")
    pdf.setAuthor("Universitario Japon")

    status = get_student_certificate_status(student)
    path_label = "Test diagnostico" if status["qualifying_path"] == "diagnostico" else "Nivelacion"

    pdf.setFillColor(surface)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#f6f0ff"))
    pdf.circle(width - 24 * mm, height - 24 * mm, 22 * mm, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#fef3c7"))
    pdf.circle(28 * mm, height - 40 * mm, 14 * mm, stroke=0, fill=1)

    pdf.setFillColor(header_bg)
    pdf.roundRect(22 * mm, height - 76 * mm, width - 44 * mm, 48 * mm, 8 * mm, stroke=0, fill=1)

    logo_path = Path(settings.BASE_DIR) / "static" / "img" / "channels4_profile.jpg"
    if logo_path.exists():
        pdf.drawImage(
            ImageReader(str(logo_path)),
            28 * mm,
            height - 67 * mm,
            28 * mm,
            28 * mm,
            mask="auto",
        )

    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 25)
    pdf.drawString(62 * mm, height - 46 * mm, "Certificado academico")
    pdf.setFont(FONT_REGULAR, 11)
    pdf.drawString(62 * mm, height - 55 * mm, "Universitario Japon")
    pdf.drawString(62 * mm, height - 62 * mm, f"Ruta habilitada por: {path_label}")

    pdf.setFillColor(text)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawCentredString(width / 2, height - 96 * mm, "Felicitaciones")

    full_name = student.get_full_name().strip() or student.display_name or student.username
    pdf.setFont(FONT_REGULAR, 12)
    pdf.drawCentredString(
        width / 2,
        height - 108 * mm,
        f"Se certifica que {full_name} cumplio satisfactoriamente su ruta academica.",
    )

    left_x = 30 * mm
    top_y = height - 146 * mm
    line_gap = 8 * mm

    pdf.setFillColor(colors.white)
    pdf.roundRect(24 * mm, height - 236 * mm, 94 * mm, 96 * mm, 6 * mm, stroke=0, fill=1)
    pdf.roundRect(136 * mm, height - 224 * mm, 40 * mm, 40 * mm, 6 * mm, stroke=0, fill=1)
    pdf.setStrokeColor(colors.HexColor("#eadfff"))
    pdf.roundRect(24 * mm, height - 236 * mm, 94 * mm, 96 * mm, 6 * mm, stroke=1, fill=0)
    pdf.roundRect(136 * mm, height - 224 * mm, 40 * mm, 40 * mm, 6 * mm, stroke=1, fill=0)

    pdf.setFillColor(primary_deep)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(left_x, top_y, "Datos del estudiante")
    pdf.setFillColor(text)
    pdf.setFont(FONT_BOLD, 10)
    value_x = left_x + 34 * mm

    student_rows = [
        ("Nombre", full_name),
        ("Cedula", student.cedula or "No registrada"),
        ("Carrera", student.carrera or "No registrada"),
        ("Correo", student.email or "No registrado"),
        ("Fecha de emision", timezone.localtime(certificate.issue_date).strftime("%d/%m/%Y %H:%M")),
    ]
    for index, (label, value) in enumerate(student_rows, start=1):
        current_y = top_y - index * line_gap
        pdf.drawString(left_x, current_y, f"{label}:")
        pdf.setFillColor(muted)
        pdf.setFont(FONT_REGULAR, 10)
        pdf.drawString(value_x, current_y, str(value))
        pdf.setFillColor(text)
        pdf.setFont(FONT_BOLD, 10)

    validation_url = request.build_absolute_uri(
        reverse("verify_certificate", args=[certificate.code])
    )
    pdf.setFillColor(primary_deep)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(left_x, top_y - 7.7 * line_gap, "Codigo de validacion")
    pdf.setFillColor(text)
    pdf.setFont(FONT_REGULAR, 9.5)
    pdf.drawString(left_x, top_y - 8.9 * line_gap, str(certificate.code))

    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(validation_url)
    qr.make(fit=True)
    qr_image = qr.make_image(image_factory=SvgImage)
    qr_buffer = BytesIO()
    qr_image.save(qr_buffer)
    qr_buffer.seek(0)

    qr_size = 30 * mm
    qr_x = 141 * mm
    qr_y = height - 218 * mm
    qr_drawing = svg2rlg(qr_buffer)
    if qr_drawing:
        source_width = float(qr_drawing.width or 1)
        source_height = float(qr_drawing.height or 1)
        scale_x = qr_size / source_width
        scale_y = qr_size / source_height
        pdf.saveState()
        pdf.translate(qr_x, qr_y)
        pdf.scale(scale_x, scale_y)
        renderPDF.draw(qr_drawing, pdf, 0, 0)
        pdf.restoreState()

    pdf.setStrokeColor(colors.HexColor("#d9cdf2"))
    pdf.line(28 * mm, 42 * mm, width - 28 * mm, 42 * mm)
    pdf.setFillColor(muted)
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawString(28 * mm, 34 * mm, "Universitario Japon")
    pdf.drawRightString(width - 28 * mm, 34 * mm, validation_url)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def _register_pdf_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    global FONT_REGULAR, FONT_BOLD

    if "SegoeUI" in pdfmetrics.getRegisteredFontNames():
        FONT_REGULAR = "SegoeUI"
        FONT_BOLD = "SegoeUI-Bold"
        return

    regular_path = Path("C:/Windows/Fonts/segoeui.ttf")
    bold_path = Path("C:/Windows/Fonts/segoeuib.ttf")
    if regular_path.exists() and bold_path.exists():
        pdfmetrics.registerFont(TTFont("SegoeUI", str(regular_path)))
        pdfmetrics.registerFont(TTFont("SegoeUI-Bold", str(bold_path)))
        FONT_REGULAR = "SegoeUI"
        FONT_BOLD = "SegoeUI-Bold"

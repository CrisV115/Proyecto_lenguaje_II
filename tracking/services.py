from io import BytesIO

from django.db.models import Case
from django.db.models import IntegerField
from django.db.models import Value
from django.db.models import When

from courses.models import CourseActivity, CourseActivitySubmission
from tests_academic.models import Result, Test
from tests_academic.utils import get_student_training_courses

from .models import Progress

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except ModuleNotFoundError:
    TRACKING_REPORTLAB_AVAILABLE = False
    colors = None
    A4 = None
    mm = None
    canvas = None
else:
    TRACKING_REPORTLAB_AVAILABLE = True


def get_progress_phase_order():
    return Case(
        When(phase=Progress.Phases.TEST, then=Value(1)),
        When(phase=Progress.Phases.INDUCTION, then=Value(2)),
        When(phase=Progress.Phases.LEVELING, then=Value(3)),
        default=Value(99),
        output_field=IntegerField(),
    )


def get_student_progress_entries(student):
    return (
        Progress.objects.filter(student=student)
        .annotate(phase_order=get_progress_phase_order())
        .order_by("phase_order", "updated_at")
    )


def sync_student_induction_progress(student):
    training_course_ids = list(
        get_student_training_courses(student).values_list("id", flat=True)
    )

    if not training_course_ids:
        Progress.objects.filter(
            student=student,
            phase=Progress.Phases.INDUCTION,
        ).delete()
        return None

    total_activities = CourseActivity.objects.filter(
        course_id__in=training_course_ids
    ).count()
    total_tests = Test.objects.filter(
        course_id__in=training_course_ids,
        is_active=True,
    ).count()
    completed_activities = CourseActivitySubmission.objects.filter(
        activity__course_id__in=training_course_ids,
        student=student,
    ).count()
    completed_tests = Result.objects.filter(
        test__course_id__in=training_course_ids,
        test__is_active=True,
        student=student,
    ).count()

    total_items = total_activities + total_tests
    completed_items = completed_activities + completed_tests
    percentage = round((completed_items * 100 / total_items), 2) if total_items else 0

    progress, _ = Progress.objects.update_or_create(
        student=student,
        phase=Progress.Phases.INDUCTION,
        defaults={
            "completed": total_items > 0 and completed_items >= total_items,
            "percentage": percentage,
        },
    )
    return progress


def build_teacher_report_pdf(report_rows, generated_at):
    if TRACKING_REPORTLAB_AVAILABLE:
        return _build_teacher_report_styled_pdf(report_rows, generated_at)
    return _build_teacher_report_basic_pdf(report_rows, generated_at)


def _build_teacher_report_styled_pdf(report_rows, generated_at):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def draw_page_header():
        pdf.setTitle("Reporte del test diagnostico")
        pdf.setAuthor("Universitario Japon")
        pdf.setFillColor(colors.HexColor("#52347e"))
        pdf.roundRect(20 * mm, height - 38 * mm, width - 40 * mm, 22 * mm, 5 * mm, stroke=0, fill=1)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(26 * mm, height - 26 * mm, "Reporte del test diagnostico")
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(
            width - 26 * mm,
            height - 26 * mm,
            f"Generado: {generated_at}",
        )

    def draw_table_header(y_position):
        pdf.setFillColor(colors.HexColor("#ede9fe"))
        pdf.roundRect(20 * mm, y_position - 6 * mm, width - 40 * mm, 10 * mm, 2 * mm, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#24143f"))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(24 * mm, y_position, "Cedula")
        pdf.drawString(58 * mm, y_position, "Nombres")
        pdf.drawString(112 * mm, y_position, "Apellidos")
        pdf.drawString(166 * mm, y_position, "Estado")

    draw_page_header()
    pdf.setFillColor(colors.HexColor("#6f6291"))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, height - 46 * mm, f"Estudiantes evaluados: {len(report_rows)}")

    y_position = height - 58 * mm
    draw_table_header(y_position)
    y_position -= 10 * mm

    for row in report_rows:
        if y_position < 24 * mm:
            pdf.showPage()
            draw_page_header()
            y_position = height - 28 * mm
            draw_table_header(y_position)
            y_position -= 10 * mm

        pdf.setStrokeColor(colors.HexColor("#ddd6fe"))
        pdf.line(20 * mm, y_position - 3 * mm, width - 20 * mm, y_position - 3 * mm)
        pdf.setFillColor(colors.HexColor("#24143f"))
        pdf.setFont("Helvetica", 9)
        pdf.drawString(24 * mm, y_position, _truncate_pdf_text(row["cedula"], 18))
        pdf.drawString(58 * mm, y_position, _truncate_pdf_text(row["first_name"], 26))
        pdf.drawString(112 * mm, y_position, _truncate_pdf_text(row["last_name"], 26))
        pdf.drawString(166 * mm, y_position, row["status_label"])
        y_position -= 8 * mm

    if not report_rows:
        pdf.setFillColor(colors.HexColor("#6f6291"))
        pdf.setFont("Helvetica", 11)
        pdf.drawString(
            20 * mm,
            y_position,
            "El reporte se habilita cuando los estudiantes rindan el test diagnostico.",
        )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def _build_teacher_report_basic_pdf(report_rows, generated_at):
    buffer = BytesIO()
    lines = [
        "Reporte del test diagnostico",
        f"Generado: {generated_at}",
        "",
        "Cedula | Nombres | Apellidos | Estado",
    ]

    if report_rows:
        lines.extend(
            [
                f'{row["cedula"]} | {row["first_name"]} | {row["last_name"]} | {row["status_label"]}'
                for row in report_rows
            ]
        )
    else:
        lines.append("El reporte se habilita cuando los estudiantes rindan el test diagnostico.")

    stream_lines = ["BT", "/F1 12 Tf", "50 800 Td"]
    current_y = 800
    for index, line in enumerate(lines):
        escaped_line = _escape_pdf_text(line)
        if index == 0:
            stream_lines.append(f"({escaped_line}) Tj")
            continue
        current_y -= 18
        stream_lines.extend([f"50 {current_y} Td", f"({escaped_line}) Tj"])
    stream_lines.append("ET")
    content = "\n".join(stream_lines).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
    ]

    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(obj)
        buffer.write(b"\nendobj\n")

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("ascii")
    )
    buffer.seek(0)
    return buffer


def _truncate_pdf_text(value, limit):
    text = str(value or "-")
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _escape_pdf_text(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )

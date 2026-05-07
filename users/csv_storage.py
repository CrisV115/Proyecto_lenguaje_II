import csv
from pathlib import Path

from django.conf import settings


BASE_HEADERS = [
    "Cedula",
    "Nombres",
    "Apellidos",
    "Correo",
    "Carrera",
    "Carreras",
    "Telefono",
    "Username",
    "TipoUsuario",
    "Aula",
]

FAILED_STUDENTS_FILENAME = "estudiantes_reprobados.csv"


def save_user_registration_to_csv(user):
    filename = "estudiantes.csv" if user.tipo_usuario == "estudiante" else "profesores.csv"
    cedula = _resolve_user_cedula(user)
    row = {
        "Cedula": cedula,
        "Nombres": user.first_name or "",
        "Apellidos": user.last_name or "",
        "Correo": user.email or "",
        "Carrera": user.carrera or "",
        "Carreras": ", ".join(user.get_carreras()),
        "Telefono": user.telefono or "",
        "Username": user.username or "",
        "TipoUsuario": user.tipo_usuario or "",
        "Aula": _resolve_user_classrooms(user),
    }

    for path in _csv_targets(filename):
        _upsert_csv_row(path, row)


def _resolve_user_cedula(user):
    cedula = (getattr(user, "cedula", "") or "").strip()
    telefono = (getattr(user, "telefono", "") or "").strip()
    username = (getattr(user, "username", "") or "").strip()

    if cedula and cedula != telefono:
        return cedula
    if username.isdigit() and len(username) == 10 and username != telefono:
        return username
    if cedula:
        return cedula
    return ""


def _csv_targets(filename):
    return [
        settings.BASE_DIR / filename,
        settings.BASE_DIR / "data" / "csv" / filename,
    ]


def rewrite_failed_students_csv():
    from tests_academic.models import Result
    from users.models import Usuario

    failed_students = (
        Usuario.objects.filter(
            tipo_usuario="estudiante",
            results__test__type="conocimientos",
            results__test__course__isnull=True,
            results__passed=False,
        )
        .exclude(
            results__test__type="conocimientos",
            results__test__course__isnull=True,
            results__passed=True,
        )
        .distinct()
        .order_by("last_name", "first_name", "cedula", "username")
    )
    failed_student_ids = set(failed_students.values_list("id", flat=True))
    if not failed_student_ids:
        rows = []
    else:
        latest_results = {}
        for result in (
            Result.objects.filter(
                student_id__in=failed_student_ids,
                test__type="conocimientos",
                test__course__isnull=True,
            )
            .select_related("student")
            .order_by("student_id", "-submitted_at", "-id")
        ):
            latest_results.setdefault(result.student_id, result)

        rows = [
            _build_user_row(student)
            for student in failed_students
            if latest_results.get(student.id) and not latest_results[student.id].passed
        ]

    for path in _csv_targets(FAILED_STUDENTS_FILENAME):
        _write_csv_rows(path, rows)


def _build_user_row(user):
    return {
        "Cedula": _resolve_user_cedula(user),
        "Nombres": user.first_name or "",
        "Apellidos": user.last_name or "",
        "Correo": user.email or "",
        "Carrera": user.carrera or "",
        "Carreras": ", ".join(user.get_carreras()),
        "Telefono": user.telefono or "",
        "Username": user.username or "",
        "TipoUsuario": user.tipo_usuario or "",
        "Aula": _resolve_user_classrooms(user),
    }


def _resolve_user_classrooms(user):
    if not getattr(user, "pk", None):
        return ""
    return ", ".join(user.classrooms.order_by("name").values_list("name", flat=True))


def _upsert_csv_row(path: Path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=";")
            headers = list(reader.fieldnames or [])
            for existing in reader:
                rows.append({header: existing.get(header, "") for header in headers})
    else:
        headers = []

    headers = _merge_headers(headers)
    updated = False
    row_key = (row.get("Cedula", "").strip(), row.get("Correo", "").strip().lower())
    normalized_rows = []

    for existing in rows:
        existing_key = (
            (existing.get("Cedula") or "").strip(),
            (existing.get("Correo") or "").strip().lower(),
        )
        if row_key == existing_key and any(row_key):
            merged = {header: existing.get(header, "") for header in headers}
            merged.update(row)
            normalized_rows.append(merged)
            updated = True
        else:
            normalized_rows.append({header: existing.get(header, "") for header in headers})

    if not updated:
        normalized_rows.append({header: row.get(header, "") for header in headers})

    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized_rows)


def _write_csv_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = _merge_headers([])
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter=";")
        writer.writeheader()
        writer.writerows(
            {header: row.get(header, "") for header in headers}
            for row in rows
        )


def _merge_headers(existing_headers):
    merged = list(existing_headers or [])
    for header in BASE_HEADERS:
        if header not in merged:
            merged.append(header)
    return merged

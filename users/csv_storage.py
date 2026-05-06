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
]


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


def _merge_headers(existing_headers):
    merged = list(existing_headers or [])
    for header in BASE_HEADERS:
        if header not in merged:
            merged.append(header)
    return merged

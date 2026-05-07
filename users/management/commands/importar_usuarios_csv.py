import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tests_academic.utils import sync_student_course_assignments


class Command(BaseCommand):
    help = "Importa estudiantes y profesores desde archivos CSV separados por punto y coma."

    base_required_columns = {"Cedula", "Correo", "Carrera"}
    first_name_candidates = ("Nombres", "Nombre")
    last_name_candidates = ("Apellidos", "Apellido")
    default_estudiantes_path = settings.BASE_DIR / "estudiantes.csv"
    default_profesores_path = settings.BASE_DIR / "profesores.csv"
    legacy_estudiantes_path = settings.BASE_DIR / "data" / "csv" / "estudiantes.csv"
    legacy_profesores_path = settings.BASE_DIR / "data" / "csv" / "profesores.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--estudiantes",
            default=str(self._resolve_default_path("estudiantes")),
            help="Ruta al archivo CSV de estudiantes.",
        )
        parser.add_argument(
            "--profesores",
            default=str(self._resolve_default_path("profesores")),
            help="Ruta al archivo CSV de profesores.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()

        summary = []
        with transaction.atomic():
            summary.append(
                self._import_file(
                    user_model=user_model,
                    csv_path=options["estudiantes"],
                    role="estudiante",
                )
            )
            summary.append(
                self._import_file(
                    user_model=user_model,
                    csv_path=options["profesores"],
                    role="profesor",
                )
            )

        for role, created, updated, skipped in summary:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{role.title()}: creados={created}, actualizados={updated}, vacios={skipped}"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "Todos los usuarios importados usan su numero de cedula como clave temporal y deben cambiarla en el primer ingreso."
            )
        )

    def _import_file(self, *, user_model, csv_path, role):
        path = Path(csv_path)
        if not path.exists():
            raise CommandError(f"No existe el archivo: {path}")

        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=";")
            fieldnames = set(reader.fieldnames or [])
            missing = self.base_required_columns - fieldnames
            if missing:
                missing_display = ", ".join(sorted(missing))
                raise CommandError(
                    f"El archivo {path} no tiene todas las columnas requeridas: {missing_display}"
                )
            first_name_column = self._pick_column(fieldnames, self.first_name_candidates)
            last_name_column = self._pick_column(fieldnames, self.last_name_candidates)
            if first_name_column is None or last_name_column is None:
                raise CommandError(
                    f"El archivo {path} debe incluir una columna para nombres ({', '.join(self.first_name_candidates)}) "
                    f"y una para apellidos ({', '.join(self.last_name_candidates)})."
                )

            created = 0
            updated = 0
            skipped = 0

            for row in reader:
                normalized = {key: (value or "").strip() for key, value in row.items()}
                if not any(normalized.values()):
                    skipped += 1
                    continue

                cedula = normalized["Cedula"]
                nombre = normalized[first_name_column]
                apellido = normalized[last_name_column]
                correo = normalized["Correo"].lower()
                carrera = user_model.normalize_carrera(normalized["Carrera"])

                if not cedula or not nombre or not apellido or not correo:
                    raise CommandError(
                        f"Fila incompleta en {path}. Cada registro debe incluir Cedula, Nombre, Apellido y Correo."
                    )

                defaults = {
                    "username": cedula,
                    "first_name": nombre,
                    "last_name": apellido,
                    "email": correo,
                    "carrera": carrera,
                    "telefono": normalized.get("Telefono", ""),
                    "tipo_usuario": role,
                    "debe_cambiar_password": True,
                    "pregunta_seguridad": "ciudad",
                    "respuesta_seguridad": cedula,
                    "is_active": True,
                }

                user = (
                    user_model.objects.filter(cedula=cedula).first()
                    or user_model.objects.filter(email__iexact=correo).first()
                    or user_model.objects.filter(username=cedula).first()
                )

                if user is not None:
                    email_owner = (
                        user_model.objects.filter(email__iexact=correo)
                        .exclude(pk=user.pk)
                        .first()
                    )
                    if email_owner is not None:
                        raise CommandError(
                            f"El correo {correo} ya pertenece a otro usuario ({email_owner.username})."
                        )

                    username_owner = (
                        user_model.objects.filter(username=cedula)
                        .exclude(pk=user.pk)
                        .first()
                    )
                    if username_owner is not None:
                        raise CommandError(
                            f"La cedula {cedula} no se puede usar como username porque ya pertenece a otro usuario ({username_owner.email})."
                        )

                    for field, value in defaults.items():
                        setattr(user, field, value)
                    user.cedula = cedula
                    was_created = False
                else:
                    user = user_model(cedula=cedula, **defaults)
                    was_created = True

                if was_created:
                    user.set_password(cedula)
                    user.save()
                    created += 1
                else:
                    user.set_password(cedula)
                    user.debe_cambiar_password = True
                    user.save()
                    updated += 1

                if role == "estudiante":
                    sync_student_course_assignments(user)

        return role, created, updated, skipped

    def _pick_column(self, fieldnames, candidates):
        for candidate in candidates:
            if candidate in fieldnames:
                return candidate
        return None

    def _resolve_default_path(self, file_type):
        if file_type == "estudiantes":
            if self.default_estudiantes_path.exists():
                return self.default_estudiantes_path
            return self.legacy_estudiantes_path

        if self.default_profesores_path.exists():
            return self.default_profesores_path
        return self.legacy_profesores_path

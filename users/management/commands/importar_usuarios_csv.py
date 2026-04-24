import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Importa estudiantes y profesores desde archivos CSV separados por punto y coma."

    base_required_columns = {"Cedula", "Correo", "Carrera"}
    first_name_candidates = ("Nombres", "Nombre")
    last_name_candidates = ("Apellidos", "Apellido")

    def add_arguments(self, parser):
        parser.add_argument(
            "--estudiantes",
            default="C:\\estudiantes.csv",
            help="Ruta al archivo CSV de estudiantes.",
        )
        parser.add_argument(
            "--profesores",
            default="C:\\profesores.csv",
            help="Ruta al archivo CSV de profesores.",
        )
        parser.add_argument(
            "--password-por-defecto",
            default="Cambiar123!",
            help="Clave temporal que se asignara a los usuarios importados.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        temp_password = options["password_por_defecto"]

        summary = []
        with transaction.atomic():
            summary.append(
                self._import_file(
                    user_model=user_model,
                    csv_path=options["estudiantes"],
                    role="estudiante",
                    temp_password=temp_password,
                )
            )
            summary.append(
                self._import_file(
                    user_model=user_model,
                    csv_path=options["profesores"],
                    role="profesor",
                    temp_password=temp_password,
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
                "Todos los usuarios importados usan la clave temporal indicada. Cambiala despues de la primera carga."
            )
        )

    def _import_file(self, *, user_model, csv_path, role, temp_password):
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
                carrera = normalized["Carrera"]

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
                    "telefono": "",
                    "tipo_usuario": role,
                    "pregunta_seguridad": "ciudad",
                    "respuesta_seguridad": cedula,
                    "is_active": True,
                }

                user, was_created = user_model.objects.update_or_create(
                    cedula=cedula,
                    defaults=defaults,
                )

                if was_created:
                    user.set_password(temp_password)
                    user.save(update_fields=["password"])
                    created += 1
                else:
                    if not user.has_usable_password():
                        user.set_password(temp_password)
                        user.save(update_fields=["password"])
                    updated += 1

        return role, created, updated, skipped

    def _pick_column(self, fieldnames, candidates):
        for candidate in candidates:
            if candidate in fieldnames:
                return candidate
        return None

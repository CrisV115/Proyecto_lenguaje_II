import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class UsersImportTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.temp_dir = settings.BASE_DIR / "test_artifacts_users"
        self.temp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_command_accepts_empty_csv_with_headers(self):
        estudiantes = self.temp_dir / "estudiantes_vacio.csv"
        profesores = self.temp_dir / "profesores_vacio.csv"
        estudiantes.write_text(
            "Cedula;Nombres;Apellidos;Correo;Carrera\n",
            encoding="utf-8",
        )
        profesores.write_text(
            "Cedula;Nombres;Apellidos;Carrera;Correo\n",
            encoding="utf-8",
        )

        call_command(
            "importar_usuarios_csv",
            estudiantes=str(estudiantes),
            profesores=str(profesores),
        )

        self.assertEqual(self.user_model.objects.count(), 0)

    def test_import_command_creates_users_from_csv(self):
        estudiantes = self.temp_dir / "estudiantes_con_datos.csv"
        profesores = self.temp_dir / "profesores_con_datos.csv"
        estudiantes.write_text(
            "Cedula;Nombres;Apellidos;Correo;Carrera\n"
            "0102030405;Ana;Perez;ana@example.com;Software\n",
            encoding="utf-8",
        )
        profesores.write_text(
            "Cedula;Nombres;Apellidos;Carrera;Correo\n"
            "1111111111;Luis;Lopez;Software;luis@example.com\n",
            encoding="utf-8",
        )

        call_command(
            "importar_usuarios_csv",
            estudiantes=str(estudiantes),
            profesores=str(profesores),
            password_por_defecto="Temporal123!",
        )

        ana = self.user_model.objects.get(cedula="0102030405")
        self.assertEqual(ana.username, "0102030405")
        self.assertEqual(ana.tipo_usuario, "estudiante")
        self.assertEqual(ana.carrera, "Software")
        self.assertTrue(ana.check_password("Temporal123!"))

        luis = self.user_model.objects.get(cedula="1111111111")
        self.assertEqual(luis.tipo_usuario, "profesor")
        self.assertEqual(luis.email, "luis@example.com")


class LoginIdentifierTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="alumno_demo",
            password="ClaveSegura123",
            email="alumno@example.com",
            cedula="0101010101",
            carrera="Software",
            telefono="0991234567",
            tipo_usuario="estudiante",
            pregunta_seguridad="mascota",
            respuesta_seguridad="luna",
        )

    def test_login_accepts_email_or_cedula(self):
        response = self.client.post(
            reverse("login"),
            {"username": "alumno@example.com", "password": "ClaveSegura123"},
        )
        self.assertRedirects(response, reverse("student_dashboard"))

        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "0101010101", "password": "ClaveSegura123"},
        )
        self.assertRedirects(response, reverse("student_dashboard"))

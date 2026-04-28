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
        )

        ana = self.user_model.objects.get(cedula="0102030405")
        self.assertEqual(ana.username, "0102030405")
        self.assertEqual(ana.tipo_usuario, "estudiante")
        self.assertEqual(ana.carrera, "Software")
        self.assertTrue(ana.check_password("0102030405"))
        self.assertTrue(ana.debe_cambiar_password)

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
            first_name="Karen Adriana",
            last_name="Garcia Hernandez",
            cedula="0101010101",
            carrera="Software",
            telefono="0991234567",
            tipo_usuario="estudiante",
            pregunta_seguridad="mascota",
            respuesta_seguridad="luna",
        )

    def test_display_name_uses_first_name_and_first_last_name(self):
        self.assertEqual(self.user.display_name, "Karen Garcia")

    def test_display_name_falls_back_to_username(self):
        user = self.user_model.objects.create_user(
            username="sin_nombre",
            password="ClaveSegura123",
            email="sin_nombre@example.com",
            cedula="0202020202",
            carrera="Software",
            telefono="0997654321",
            tipo_usuario="estudiante",
            pregunta_seguridad="madre",
            respuesta_seguridad="maria",
        )

        self.assertEqual(user.display_name, "sin_nombre")

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

    def test_user_with_pending_password_change_is_redirected(self):
        self.user.debe_cambiar_password = True
        self.user.save(update_fields=["debe_cambiar_password"])

        response = self.client.post(
            reverse("login"),
            {"username": "0101010101", "password": "ClaveSegura123"},
        )
        self.assertRedirects(response, reverse("force_password_change"))

    def test_user_can_change_password_on_first_login(self):
        self.user.set_password("0101010101")
        self.user.debe_cambiar_password = True
        self.user.save(update_fields=["password", "debe_cambiar_password"])

        login_response = self.client.post(
            reverse("login"),
            {"username": "0101010101", "password": "0101010101"},
        )
        self.assertRedirects(login_response, reverse("force_password_change"))

        response = self.client.post(
            reverse("force_password_change"),
            {
                "old_password": "0101010101",
                "new_password1": "NuevaClave123!",
                "new_password2": "NuevaClave123!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.debe_cambiar_password)
        self.assertTrue(self.user.check_password("NuevaClave123!"))

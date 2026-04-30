from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from certifications.models import Certificate
from certifications.services import COMPLETION_SOURCE_PHASE
from courses.models import Course, CourseActivity, CourseActivitySubmission
from leveling.models import LevelingRecord
from tests_academic.models import Result, Test
from tracking.models import Progress


class TrackingCertificateTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.student = self.user_model.objects.create_user(
            username="estudiante_demo",
            password="ClaveSegura123",
            email="estudiante@example.com",
            first_name="Ana Maria",
            last_name="Lopez Perez",
            cedula="0101010101",
            carrera="Software",
            telefono="0999999999",
            tipo_usuario="estudiante",
            pregunta_seguridad="mascota",
            respuesta_seguridad="luna",
        )
        self.client.login(username="estudiante_demo", password="ClaveSegura123")
        self.professor = self.user_model.objects.create_user(
            username="profesor_demo",
            password="ClaveSegura123",
            email="profesor@example.com",
            first_name="Luis",
            last_name="Morales",
            cedula="0202020202",
            carrera="Docencia",
            telefono="0988888888",
            tipo_usuario="profesor",
            pregunta_seguridad="madre",
            respuesta_seguridad="rosa",
        )

    def test_tracking_overview_shows_missing_requirements_and_disabled_button(self):
        response = self.client.get(reverse("tracking_overview"))

        self.assertContains(response, "Primero debes rendir el test diagnostico.")
        self.assertContains(response, "Descargar certificado PDF")
        self.assertNotContains(response, f'href="{reverse("download_certificate_pdf")}"')

    def test_download_certificate_pdf_returns_pdf_when_student_passes_diagnostic(self):
        diagnostic_test = Test.objects.create(
            name="Diagnostico principal",
            type="conocimientos",
            duration=30,
            passing_score=70,
            is_active=True,
        )
        Result.objects.create(
            student=self.student,
            test=diagnostic_test,
            score=90,
            passed=True,
        )

        response = self.client.get(reverse("download_certificate_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            Certificate.objects.filter(
                student=self.student,
                source_phase=COMPLETION_SOURCE_PHASE,
                valid=True,
            ).exists()
        )

    def test_download_certificate_pdf_returns_pdf_when_student_fails_diagnostic_but_passes_leveling(self):
        diagnostic_test = Test.objects.create(
            name="Diagnostico principal",
            type="conocimientos",
            duration=30,
            passing_score=70,
            is_active=True,
        )
        Result.objects.create(
            student=self.student,
            test=diagnostic_test,
            score=45,
            passed=False,
        )
        Progress.objects.create(
            student=self.student,
            phase=Progress.Phases.LEVELING,
            completed=True,
            percentage=100,
        )
        LevelingRecord.objects.create(
            student=self.student,
            synchronous_sessions_attended=3,
            asynchronous_activities_completed=4,
            final_exam_score=95,
        )

        response = self.client.get(reverse("download_certificate_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_certificate_pdf_redirects_when_requirements_are_not_met(self):
        response = self.client.get(reverse("download_certificate_pdf"))

        self.assertRedirects(response, reverse("tracking_overview"))
        self.assertFalse(Certificate.objects.filter(student=self.student).exists())

    def test_tracking_overview_restores_induction_progress_from_training_courses(self):
        training_course = Course.objects.create(
            name="Capacitacion Office",
            description="Herramientas base",
            is_training=True,
        )
        training_course.students.add(self.student)

        activity = CourseActivity.objects.create(
            course=training_course,
            title="Tutorial inicial",
            description="Completar tutorial",
            due_date=self.student.date_joined.date(),
            opening_time=time(8, 0),
            closing_time=time(10, 0),
        )
        CourseActivitySubmission.objects.create(
            activity=activity,
            student=self.student,
            submission_text="Completado",
        )

        response = self.client.get(reverse("tracking_overview"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Induccion")
        self.assertTrue(
            Progress.objects.filter(
                student=self.student,
                phase=Progress.Phases.INDUCTION,
                percentage=100,
                completed=True,
            ).exists()
        )

    def test_teacher_report_only_shows_students_with_diagnostic_result(self):
        another_student = self.user_model.objects.create_user(
            username="estudiante_sin_resultado",
            password="ClaveSegura123",
            email="sinresultado@example.com",
            first_name="Pablo",
            last_name="Rojas",
            cedula="0303030303",
            carrera="Marketing",
            telefono="0977777777",
            tipo_usuario="estudiante",
            pregunta_seguridad="mascota",
            respuesta_seguridad="sol",
        )
        diagnostic_test = Test.objects.create(
            name="Diagnostico general",
            type="conocimientos",
            duration=30,
            passing_score=70,
            is_active=True,
            created_by=self.professor,
        )
        Result.objects.create(
            student=self.student,
            test=diagnostic_test,
            score=88,
            passed=True,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reporte del test diagnostico")
        self.assertContains(response, self.student.cedula)
        self.assertContains(response, self.student.first_name)
        self.assertContains(response, self.student.last_name)
        self.assertContains(response, "Aprobado")
        self.assertNotContains(response, another_student.username)

    def test_teacher_report_pdf_downloads_successfully(self):
        diagnostic_test = Test.objects.create(
            name="Diagnostico general",
            type="conocimientos",
            duration=30,
            passing_score=70,
            is_active=True,
            created_by=self.professor,
        )
        Result.objects.create(
            student=self.student,
            test=diagnostic_test,
            score=55,
            passed=False,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_report_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("reporte_seguimiento_docente.pdf", response["Content-Disposition"])

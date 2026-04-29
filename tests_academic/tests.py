from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from certifications.models import Certificate
from certifications.services import COMPLETION_SOURCE_PHASE
from courses.models import Course, CourseActivity
from leveling.models import LevelingRecord
from tracking.models import Progress

from .models import Answer, Question, Result, StudentAnswer, Test


class AcademicFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="estudiante_demo",
            password="ClaveSegura123",
            email="estudiante_demo@example.com",
            telefono="0991234567",
            tipo_usuario="estudiante",
            pregunta_seguridad="mascota",
            respuesta_seguridad="firulais",
        )
        self.professor = self.user_model.objects.create_user(
            username="profesor_demo",
            password="ClaveSegura123",
            email="profesor_demo@example.com",
            telefono="0987654321",
            tipo_usuario="profesor",
            pregunta_seguridad="madre",
            respuesta_seguridad="maria",
        )
        self.test = Test.objects.create(
            name="Test demo",
            type="conocimientos",
            duration=20,
            created_by=self.professor,
        )
        self.question_one = Question.objects.create(
            test=self.test,
            text="2 + 2 = ?",
            order=1,
        )
        self.question_two = Question.objects.create(
            test=self.test,
            text="Capital de Ecuador",
            order=2,
        )
        self.correct_one = Answer.objects.create(
            question=self.question_one,
            text="4",
            is_correct=True,
        )
        self.wrong_one = Answer.objects.create(
            question=self.question_one,
            text="5",
            is_correct=False,
        )
        self.correct_two = Answer.objects.create(
            question=self.question_two,
            text="Quito",
            is_correct=True,
        )
        self.wrong_two = Answer.objects.create(
            question=self.question_two,
            text="Guayaquil",
            is_correct=False,
        )
        self.client.login(username="estudiante_demo", password="ClaveSegura123")

    def test_correct_submission_creates_result_answers_and_test_progress(self):
        response = self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.correct_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        result = Result.objects.get(student=self.user, test=self.test)
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 100)
        self.assertEqual(StudentAnswer.objects.filter(result=result).count(), 2)

        test_progress = Progress.objects.get(student=self.user, phase=Progress.Phases.TEST)
        self.assertTrue(test_progress.completed)
        self.assertEqual(test_progress.percentage, 100)
        self.assertFalse(
            Progress.objects.filter(
                student=self.user,
                phase=Progress.Phases.LEVELING,
            ).exists()
        )

    def test_multiple_attempts_are_blocked(self):
        Result.objects.create(
            student=self.user,
            test=self.test,
            score=80,
            passed=True,
        )

        response = self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.correct_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Result.objects.filter(student=self.user, test=self.test).count(), 1)

    def test_leveling_completion_generates_certificate(self):
        self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.wrong_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        leveling_progress = Progress.objects.get(
            student=self.user,
            phase=Progress.Phases.LEVELING,
        )
        self.assertFalse(leveling_progress.completed)

        for _ in range(3):
            self.client.post(reverse("leveling_dashboard"), {"action": "sync_attendance"}, follow=True)
        for _ in range(4):
            self.client.post(reverse("leveling_dashboard"), {"action": "async_activity"}, follow=True)
        self.client.post(
            reverse("leveling_dashboard"),
            {"action": "exam_score", "final_exam_score": "85"},
            follow=True,
        )

        response = self.client.get(reverse("complete_leveling"), follow=True)
        self.assertEqual(response.status_code, 200)

        certificate = Certificate.objects.get(student=self.user)
        self.assertEqual(certificate.source_phase, COMPLETION_SOURCE_PHASE)
        self.assertTrue(certificate.valid)
        record = LevelingRecord.objects.get(student=self.user)
        self.assertTrue(record.ready_for_completion)

    def test_passing_diagnostic_enables_certificate_without_additional_phase(self):
        self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.correct_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        response = self.client.get(reverse("generate_certificate"), follow=True)
        self.assertEqual(response.status_code, 200)

        certificate = Certificate.objects.get(student=self.user)
        self.assertEqual(certificate.source_phase, COMPLETION_SOURCE_PHASE)
        self.assertTrue(certificate.valid)
        self.assertFalse(
            Progress.objects.filter(
                student=self.user,
                phase=Progress.Phases.LEVELING,
            ).exists()
        )

    def test_public_certificate_verification_page(self):
        self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.correct_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        self.client.get(reverse("generate_certificate"), follow=True)

        certificate = Certificate.objects.get(student=self.user)

        self.client.logout()
        response = self.client.get(reverse("verify_certificate", args=[certificate.code]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificado valido")

    def test_login_redirects_user_by_role(self):
        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {"username": "estudiante_demo", "password": "ClaveSegura123"},
        )
        self.assertRedirects(response, reverse("student_dashboard"))

        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "profesor_demo", "password": "ClaveSegura123"},
        )
        self.assertRedirects(response, reverse("teacher_dashboard"))

    def test_teacher_can_manage_tests_and_review_student_results(self):
        Result.objects.create(
            student=self.user,
            test=self.test,
            score=100,
            passed=True,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        dashboard_response = self.client.get(reverse("teacher_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "Gestion de tests diagnosticos y vocacionales")

        tests_response = self.client.get(reverse("teacher_tests"))
        self.assertEqual(tests_response.status_code, 200)
        self.assertContains(tests_response, self.test.name)

        results_response = self.client.get(reverse("teacher_results"))
        self.assertEqual(results_response.status_code, 200)
        self.assertContains(results_response, self.user.username)

    def test_student_leveling_menu_only_appears_with_score_below_seven(self):
        Result.objects.create(
            student=self.user,
            test=self.test,
            score=60,
            passed=False,
        )

        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Requiere nivelacion")

        Result.objects.filter(student=self.user, test=self.test).delete()
        Result.objects.create(
            student=self.user,
            test=self.test,
            score=80,
            passed=True,
        )

        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Requiere nivelacion")

    def test_teacher_can_open_leveling_dashboard(self):
        Result.objects.create(
            student=self.user,
            test=self.test,
            score=60,
            passed=False,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_leveling_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seguimiento de nivelacion")
        self.assertContains(response, self.user.username)

    def test_student_sees_active_teacher_test_in_dashboard_and_list(self):
        dashboard_response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, reverse("take_test", args=[self.test.id]))

        tests_response = self.client.get(reverse("tests_index"))
        self.assertEqual(tests_response.status_code, 200)
        self.assertContains(tests_response, self.test.name)

    def test_approved_student_no_longer_sees_assigned_leveling(self):
        self.test.delete()
        course = Course.objects.create(
            name="Nivelacion Algebra",
            description="Refuerzo base",
        )
        course.students.add(self.user)
        course.teachers.add(self.professor)

        diagnostic_test = Test.objects.create(
            name="Diagnostico Algebra",
            type="conocimientos",
            duration=20,
            created_by=self.professor,
        )
        follow_up_test = Test.objects.create(
            name="Test de refuerzo",
            type="curso",
            duration=20,
            created_by=self.professor,
            course=course,
        )
        CourseActivity.objects.create(
            course=course,
            title="Guia 1",
            description="Resolver ejercicios",
            due_date=timezone.localdate() + timedelta(days=1),
            opening_time=time(8, 0),
            closing_time=time(10, 0),
            created_by=self.professor,
        )
        Result.objects.create(
            student=self.user,
            test=diagnostic_test,
            score=80,
            passed=True,
        )

        dashboard_response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(
            dashboard_response,
            "No tienes actividades ni tests pendientes porque aprobaste el diagnostico.",
        )
        self.assertNotContains(dashboard_response, course.name)
        self.assertNotContains(dashboard_response, "Guia 1")
        self.assertNotContains(
            dashboard_response,
            reverse("take_test", args=[follow_up_test.id]),
        )

        student_courses_response = self.client.get(reverse("student_courses"))
        self.assertEqual(student_courses_response.status_code, 200)
        self.assertContains(
            student_courses_response,
            "No tienes ninguna nivelacion asignada porque aprobaste el test diagnostico.",
        )
        self.assertNotContains(student_courses_response, course.name)

        tests_response = self.client.get(reverse("tests_index"))
        self.assertEqual(tests_response.status_code, 200)
        self.assertNotContains(tests_response, follow_up_test.name)
        self.assertContains(tests_response, diagnostic_test.name)

        course_detail_response = self.client.get(reverse("course_detail", args=[course.id]))
        self.assertEqual(course_detail_response.status_code, 404)

    def test_student_leveling_views_use_nivelacion_labels(self):
        course = Course.objects.create(
            name="Nivelacion Programacion",
            description="Fundamentos",
        )
        course.students.add(self.user)

        response = self.client.get(reverse("student_courses"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nivelaciones asignadas")
        self.assertContains(response, "Entrar a la nivelacion")

    def test_teacher_management_only_lists_diagnostic_and_vocational_tests(self):
        unsupported_test = Test.objects.create(
            name="Test libre",
            type="libre",
            duration=10,
            created_by=self.professor,
        )
        vocational_test = Test.objects.create(
            name="Test vocacional",
            type="vocacional",
            duration=15,
            created_by=self.professor,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_tests"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test.name)
        self.assertContains(response, vocational_test.name)
        self.assertContains(response, "Diagnostico")
        self.assertContains(response, "Vocacional")
        self.assertNotContains(response, unsupported_test.name)

    def test_teacher_test_form_allows_selecting_diagnostic_or_vocational_type(self):
        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_test_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tipo de test")
        self.assertContains(response, "Diagnostico")
        self.assertContains(response, "Vocacional")
        self.assertNotContains(response, 'id="id_course"', html=False)

    def test_teacher_cannot_edit_test_outside_managed_types(self):
        unsupported_test = Test.objects.create(
            name="Test libre",
            type="libre",
            duration=10,
            created_by=self.professor,
        )

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_test_edit", args=[unsupported_test.id]))
        self.assertEqual(response.status_code, 404)

    def test_course_test_form_shows_course_and_hides_management_type(self):
        course = Course.objects.create(
            name="Nivelacion Base",
            description="Refuerzo",
        )
        course.teachers.add(self.professor)

        self.client.logout()
        self.client.login(username="profesor_demo", password="ClaveSegura123")

        response = self.client.get(reverse("teacher_test_create") + f"?course={course.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crear test del curso")
        self.assertContains(response, 'id="id_course"', html=False)
        self.assertContains(response, str(course.id))
        self.assertNotContains(response, 'id="id_type"', html=False)

    def test_course_test_submission_does_not_update_diagnostic_progress(self):
        course = Course.objects.create(
            name="Nivelacion Logica",
            description="Refuerzo",
        )
        course.students.add(self.user)
        course.teachers.add(self.professor)
        course_test = Test.objects.create(
            name="Evaluacion de nivelacion",
            type="curso",
            duration=20,
            created_by=self.professor,
            course=course,
        )
        question = Question.objects.create(
            test=course_test,
            text="5 + 5 = ?",
            order=1,
        )
        correct_answer = Answer.objects.create(
            question=question,
            text="10",
            is_correct=True,
        )

        response = self.client.post(
            reverse("take_test", args=[course_test.id]),
            {
                f"question_{question.id}": str(correct_answer.id),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aprobado en el test del curso.")
        self.assertContains(response, reverse("course_detail", args=[course.id]))
        self.assertEqual(Progress.objects.filter(student=self.user).count(), 0)

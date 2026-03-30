from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from certifications.models import Certificate
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
        self.test = Test.objects.create(
            name="Test demo",
            type="conocimientos",
            duration=20,
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

    def test_correct_submission_creates_result_answers_and_induction_progress(self):
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
        induction_progress = Progress.objects.get(
            student=self.user,
            phase=Progress.Phases.INDUCTION,
        )
        self.assertTrue(test_progress.completed)
        self.assertEqual(test_progress.percentage, 100)
        self.assertFalse(induction_progress.completed)

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

        response = self.client.get(reverse("complete_leveling"), follow=True)
        self.assertEqual(response.status_code, 200)

        certificate = Certificate.objects.get(student=self.user)
        self.assertEqual(certificate.source_phase, Progress.Phases.LEVELING)
        self.assertTrue(certificate.valid)

    def test_induction_completion_generates_certificate(self):
        self.client.post(
            reverse("take_test", args=[self.test.id]),
            {
                f"question_{self.question_one.id}": str(self.correct_one.id),
                f"question_{self.question_two.id}": str(self.correct_two.id),
            },
            follow=True,
        )

        response = self.client.get(reverse("complete_induction"), follow=True)
        self.assertEqual(response.status_code, 200)

        certificate = Certificate.objects.get(student=self.user)
        self.assertEqual(certificate.source_phase, Progress.Phases.INDUCTION)
        self.assertTrue(certificate.valid)

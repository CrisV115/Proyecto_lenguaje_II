from django.contrib import messages
from django.db.models import Count, Prefetch
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from tracking.models import Progress
from users.decorators import role_required
from users.models import Usuario

from .forms import TeacherTestForm, TestForm
from .models import Answer, Question, Result, StudentAnswer, Test


@role_required("estudiante")
def index(request):
    tests = Test.objects.filter(is_active=True).order_by("name")
    completed_test_ids = set(
        Result.objects.filter(student=request.user).values_list("test_id", flat=True)
    )
    return render(
        request,
        "tests_academic/index.html",
        {
            "tests": tests,
            "completed_test_ids": completed_test_ids,
        },
    )


@role_required("estudiante")
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_active=True)

    if Result.objects.filter(student=request.user, test=test).exists():
        messages.warning(
            request,
            "Ya registraste un intento para este test. No se permiten multiples intentos.",
        )
        return redirect("test_result", test_id=test.id)

    if not test.questions.exists():
        messages.warning(request, "Este test todavia no tiene preguntas configuradas.")
        return redirect("tests_index")

    if request.method == "POST":
        form = TestForm(request.POST, test=test)
        if form.is_valid():
            total = len(form.cleaned_data)
            correctas = 0
            respuestas = []

            with transaction.atomic():
                for answer_id in form.cleaned_data.values():
                    answer = Answer.objects.select_related("question").get(id=answer_id)
                    if answer.is_correct:
                        correctas += 1
                    respuestas.append(answer)

                final_score = (correctas / total) * 100 if total else 0
                passed = final_score >= test.passing_score

                result = Result.objects.create(
                    student=request.user,
                    test=test,
                    score=final_score,
                    passed=passed,
                )

                StudentAnswer.objects.bulk_create(
                    [
                        StudentAnswer(
                            result=result,
                            student=request.user,
                            question=answer.question,
                            answer=answer,
                        )
                        for answer in respuestas
                    ]
                )

                Progress.objects.update_or_create(
                    student=request.user,
                    phase=Progress.Phases.TEST,
                    defaults={"completed": True, "percentage": 100},
                )

                if passed:
                    Progress.objects.update_or_create(
                        student=request.user,
                        phase=Progress.Phases.INDUCTION,
                        defaults={"completed": False, "percentage": 0},
                    )
                else:
                    Progress.objects.update_or_create(
                        student=request.user,
                        phase=Progress.Phases.LEVELING,
                        defaults={"completed": False, "percentage": 0},
                    )

            messages.success(request, "Test enviado y calificado correctamente.")
            return redirect("test_result", test_id=test.id)
    else:
        form = TestForm(test=test)

    return render(
        request,
        "tests_academic/take_test.html",
        {
            "form": form,
            "test": test,
        },
    )


@role_required("estudiante")
def test_result(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    result = get_object_or_404(Result, student=request.user, test=test)
    return render(
        request,
        "tests_academic/result.html",
        {
            "result": result,
            "test": test,
        },
    )


@role_required("profesor")
def teacher_tests(request):
    tests = (
        Test.objects.select_related("created_by")
        .annotate(
            questions_count=Count("questions", distinct=True),
            results_count=Count("results", distinct=True),
        )
        .order_by("-created_at")
    )
    return render(request, "tests_academic/teacher_tests.html", {"tests": tests})


@role_required("profesor")
def teacher_test_create(request):
    if request.method == "POST":
        form = TeacherTestForm(request.POST)
        if form.is_valid():
            _save_test_with_questions(form, request.user)
            messages.success(request, "Test creado correctamente.")
            return redirect("teacher_tests")
    else:
        form = TeacherTestForm()

    return render(
        request,
        "tests_academic/teacher_test_form.html",
        {"form": form, "page_title": "Crear test diagnostico"},
    )


@role_required("profesor")
def teacher_test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if request.method == "POST":
        form = TeacherTestForm(request.POST, instance=test)
        if form.is_valid():
            _save_test_with_questions(form, request.user)
            messages.success(request, "Test actualizado correctamente.")
            return redirect("teacher_tests")
    else:
        form = TeacherTestForm(instance=test)

    return render(
        request,
        "tests_academic/teacher_test_form.html",
        {"form": form, "page_title": "Editar test diagnostico", "test": test},
    )


@role_required("profesor")
def teacher_results(request):
    results = Result.objects.select_related("student", "test").order_by("-submitted_at")
    return render(request, "tests_academic/teacher_results.html", {"results": results})


@role_required("profesor")
def teacher_result_detail(request, result_id):
    result = get_object_or_404(
        Result.objects.select_related("student", "test").prefetch_related(
            Prefetch(
                "student_answers",
                queryset=StudentAnswer.objects.select_related("question", "answer").order_by(
                    "question__order", "question__id"
                ),
            )
        ),
        id=result_id,
    )
    return render(
        request,
        "tests_academic/teacher_result_detail.html",
        {"result": result},
    )


@role_required("profesor")
def teacher_students(request):
    students = (
        Usuario.objects.filter(tipo_usuario="estudiante")
        .annotate(results_count=Count("results", distinct=True))
        .order_by("username")
    )
    return render(request, "tests_academic/teacher_students.html", {"students": students})


def _save_test_with_questions(form, user):
    with transaction.atomic():
        test = form.save(commit=False)
        if not test.created_by:
            test.created_by = user
        test.save()

        test.questions.all().delete()
        questions = []
        answers = []

        for order, parsed_question in enumerate(form.parsed_questions, start=1):
            question = Question.objects.create(
                test=test,
                text=parsed_question["text"],
                order=order,
            )
            questions.append(question)
            answers.extend(
                [
                    Answer(
                        question=question,
                        text=answer_data["text"],
                        is_correct=answer_data["is_correct"],
                    )
                    for answer_data in parsed_question["answers"]
                ]
            )

        if answers:
            Answer.objects.bulk_create(answers)

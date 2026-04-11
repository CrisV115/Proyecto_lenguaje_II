from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from tracking.models import Progress

from .forms import TestForm
from .models import Answer, Result, StudentAnswer, Test


@login_required
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


@login_required
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


@login_required
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

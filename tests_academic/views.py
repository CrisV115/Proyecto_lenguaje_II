from datetime import datetime

from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course
from tracking.models import Progress
from users.decorators import role_required
from users.models import Usuario

from .forms import TeacherTestForm, TestForm
from .models import Answer, Question, Result, StudentAnswer, Test


@role_required("estudiante")
def index(request):
    tests = (
        Test.objects.filter(
            is_active=True,
        )
        .filter(
            Q(course__students=request.user) | Q(course__isnull=True)
        )
        .select_related("course")
        .distinct()
        .order_by("name")
    )
    completed_test_ids = set(
        Result.objects.filter(student=request.user).values_list("test_id", flat=True)
    )
    now = timezone.localtime()
    available_now_ids = {test.id for test in tests if _is_test_open(test, now)}
    return render(
        request,
        "tests_academic/index.html",
        {
            "tests": tests,
            "completed_test_ids": completed_test_ids,
            "available_now_ids": available_now_ids,
        },
    )


@role_required("estudiante")
def take_test(request, test_id):
    test = get_object_or_404(
        Test,
        id=test_id,
        is_active=True,
    )
    if test.course and not test.course.students.filter(id=request.user.id).exists():
        return redirect("tests_index")

    if not _is_test_open(test, timezone.localtime()):
        messages.warning(
            request,
            "Este test no esta disponible en este momento segun su fecha y horario.",
        )
        return redirect("tests_index")

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
            total = len(form.fields)
            correctas = 0
            student_answers = []

            with transaction.atomic():
                for field_name, value in form.cleaned_data.items():
                    question_id = int(field_name.split("_")[1])
                    question = form.question_map[question_id]
                    answer_data, is_correct = _build_student_answer(question, value)
                    if is_correct:
                        correctas += 1
                    student_answers.append(
                        StudentAnswer(
                            student=request.user,
                            question=question,
                            **answer_data,
                            is_correct=is_correct,
                        )
                    )

                final_score = (correctas / total) * 100 if total else 0
                passed = final_score >= test.passing_score

                result = Result.objects.create(
                    student=request.user,
                    test=test,
                    score=final_score,
                    passed=passed,
                )

                for student_answer in student_answers:
                    student_answer.result = result
                StudentAnswer.objects.bulk_create(student_answers)

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
    course_id = request.GET.get("course")
    tests = (
        Test.objects.filter(created_by=request.user)
        .select_related("created_by")
        .annotate(
            questions_count=Count("questions", distinct=True),
            results_count=Count("results", distinct=True),
        )
        .order_by("-created_at")
    )
    if course_id:
        tests = tests.filter(course_id=course_id)
    return render(
        request,
        "tests_academic/teacher_tests.html",
        {"tests": tests, "course_id": course_id},
    )


@role_required("profesor")
def teacher_test_create(request):
    initial_course = _resolve_course_for_teacher(request, request.GET.get("course"))
    if request.method == "POST":
        form = TeacherTestForm(request.POST)
        form.fields["course"].queryset = _teacher_courses_queryset(request.user)
        if form.is_valid() and _validate_teacher_course(form, request.user):
            _save_test_with_questions(form, request.user)
            messages.success(request, "Test creado correctamente.")
            if form.cleaned_data.get("course"):
                return redirect("course_detail", course_id=form.cleaned_data["course"].id)
            return redirect("teacher_tests")
    else:
        form = TeacherTestForm(initial={"course": initial_course} if initial_course else None)
        form.fields["course"].queryset = _teacher_courses_queryset(request.user)

    return render(
        request,
        "tests_academic/teacher_test_form.html",
        {"form": form, "page_title": "Crear test diagnostico", "from_course": initial_course},
    )


@role_required("profesor")
def teacher_test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id, created_by=request.user)

    if request.method == "POST":
        form = TeacherTestForm(request.POST, instance=test)
        form.fields["course"].queryset = _teacher_courses_queryset(request.user)
        if form.is_valid() and _validate_teacher_course(form, request.user):
            _save_test_with_questions(form, request.user)
            messages.success(request, "Test actualizado correctamente.")
            if form.cleaned_data.get("course"):
                return redirect("course_detail", course_id=form.cleaned_data["course"].id)
            return redirect("teacher_tests")
    else:
        form = TeacherTestForm(instance=test)
        form.fields["course"].queryset = _teacher_courses_queryset(request.user)

    return render(
        request,
        "tests_academic/teacher_test_form.html",
        {"form": form, "page_title": "Editar test diagnostico", "test": test},
    )


@role_required("profesor")
def teacher_results(request):
    results = (
        Result.objects.filter(test__created_by=request.user)
        .select_related("student", "test")
        .order_by("-submitted_at")
    )
    return render(request, "tests_academic/teacher_results.html", {"results": results})


@role_required("profesor")
def teacher_result_detail(request, result_id):
    result = get_object_or_404(
        Result.objects.select_related("student", "test").prefetch_related(
            Prefetch(
                "student_answers",
                queryset=StudentAnswer.objects.select_related("question", "answer")
                .prefetch_related("question__answers")
                .order_by("question__order", "question__id"),
            )
        ),
        id=result_id,
        test__created_by=request.user,
    )
    return render(
        request,
        "tests_academic/teacher_result_detail.html",
        {"result": result},
    )


@role_required("profesor")
def teacher_students(request):
    teacher_courses = Course.objects.filter(teachers=request.user)
    students = (
        Usuario.objects.filter(
            tipo_usuario="estudiante",
            courses_enrolled__in=teacher_courses,
        )
        .distinct()
        .annotate(results_count=Count("results", distinct=True))
        .order_by("username")
    )
    return render(request, "tests_academic/teacher_students.html", {"students": students})


def _save_test_with_questions(form, user):
    with transaction.atomic():
        test = form.save(commit=False)
        if not test.created_by:
            test.created_by = user
        if not test.type:
            test.type = "conocimientos"
        test.save()

        test.questions.all().delete()
        questions = []
        answers = []

        for order, parsed_question in enumerate(form.parsed_questions, start=1):
            question = Question.objects.create(
                test=test,
                text=parsed_question["text"],
                question_type=parsed_question["question_type"],
                required=parsed_question["required"],
                order=order,
            )
            answers.extend(
                [
                    Answer(
                        question=question,
                        text=answer_data["text"],
                        is_correct=answer_data["is_correct"],
                        order=answer_data["order"],
                    )
                    for answer_data in parsed_question["answers"]
                ]
            )

        if answers:
            Answer.objects.bulk_create(answers)


def _build_student_answer(question, value):
    if question.question_type in {"multiple_choice", "dropdown"}:
        answer = question.answers.get(id=int(value))
        return {"answer": answer, "text_response": "", "selected_answer_ids": []}, answer.is_correct

    if question.question_type == "checkboxes":
        selected_ids = [int(answer_id) for answer_id in value]
        selected_answers = list(question.answers.filter(id__in=selected_ids))
        correct_ids = set(
            question.answers.filter(is_correct=True).values_list("id", flat=True)
        )
        return {
            "answer": None,
            "text_response": "",
            "selected_answer_ids": selected_ids,
        }, set(selected_ids) == correct_ids and bool(correct_ids)

    expected_answer = question.answers.filter(is_correct=True).first()
    normalized_value = (value or "").strip()
    expected_text = expected_answer.text.strip() if expected_answer else ""
    return {
        "answer": None,
        "text_response": normalized_value,
        "selected_answer_ids": [],
    }, normalized_value.lower() == expected_text.lower()


def _is_test_open(test, now):
    if not test.available_date or not test.opening_time or not test.closing_time:
        return True
    if now.date() != test.available_date:
        return False

    opening_dt = timezone.make_aware(
        datetime.combine(test.available_date, test.opening_time),
        timezone.get_current_timezone(),
    )
    closing_dt = timezone.make_aware(
        datetime.combine(test.available_date, test.closing_time),
        timezone.get_current_timezone(),
    )
    return opening_dt <= now <= closing_dt


def _teacher_courses_queryset(user):
    return Course.objects.filter(teachers=user).order_by("name")


def _resolve_course_for_teacher(request, course_id):
    if not course_id:
        return None
    return (
        Course.objects.filter(id=course_id, teachers=request.user)
        .order_by("name")
        .first()
    )


def _validate_teacher_course(form, user):
    course = form.cleaned_data.get("course")
    if course and not course.teachers.filter(id=user.id).exists():
        form.add_error("course", "Solo puedes asignar tests a cursos donde eres docente.")
        return False
    return True

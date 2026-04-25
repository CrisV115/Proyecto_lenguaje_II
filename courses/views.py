from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import role_required

from .forms import CourseActivityForm
from .models import Course


@role_required("estudiante")
def student_courses(request):
    courses = request.user.courses_enrolled.order_by("name")
    return render(request, "courses/student_courses.html", {"courses": courses})


@role_required("profesor")
def teacher_courses(request):
    courses = request.user.courses_taught.order_by("name")
    return render(request, "courses/teacher_courses.html", {"courses": courses})


@role_required("estudiante", "profesor")
def course_detail(request, course_id):
    if request.user.tipo_usuario == "estudiante":
        course = get_object_or_404(Course, id=course_id, students=request.user)
    else:
        course = get_object_or_404(Course, id=course_id, teachers=request.user)

    students = course.students.order_by("username")
    teachers = course.teachers.order_by("username")
    activities = course.activities.select_related("created_by").order_by("due_date", "opening_time")
    tests = course.tests.order_by("available_date", "opening_time", "name")
    if request.user.tipo_usuario == "estudiante":
        tests = tests.filter(is_active=True)

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "students": students,
            "teachers": teachers,
            "activities": activities,
            "tests": tests,
            "activity_form": CourseActivityForm(),
        },
    )


@role_required("profesor")
def create_course_activity(request, course_id):
    course = get_object_or_404(Course, id=course_id, teachers=request.user)
    if request.method != "POST":
        return redirect("course_detail", course_id=course.id)

    form = CourseActivityForm(request.POST, request.FILES)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.course = course
        activity.created_by = request.user
        activity.save()
        messages.success(request, "Actividad creada correctamente.")
    else:
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)

    return redirect("course_detail", course_id=course.id)

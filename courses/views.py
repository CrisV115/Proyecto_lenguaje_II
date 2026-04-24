from django.shortcuts import get_object_or_404, render

from users.decorators import role_required

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

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "students": students,
            "teachers": teachers,
        },
    )

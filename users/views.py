from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from certifications.models import Certificate
from tests_academic.models import Result, Test
from tracking.models import Progress

from .forms import RegistroForm
from .models import Usuario


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.email = form.cleaned_data["email"]
            usuario.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("login")

        messages.error(request, "Corrija los errores del formulario.")
    else:
        form = RegistroForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return redirect("login")

        login(request, user)
        return redirect("student_dashboard")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("home")


def password_reset_security(request):
    context = {}

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        respuesta = request.POST.get("respuesta_seguridad", "").strip()
        nueva_password = request.POST.get("nueva_password", "")

        usuario = Usuario.objects.filter(email=email).first() if email else None

        if "respuesta_seguridad" not in request.POST:
            if not email:
                messages.error(request, "Debe ingresar un correo.")
                return redirect("password_reset")

            if not usuario:
                messages.error(request, "No existe un usuario con ese correo.")
                return redirect("password_reset")

            context["usuario"] = usuario
            return render(request, "password_reset.html", context)

        if not usuario:
            messages.error(request, "No existe un usuario con ese correo.")
            return redirect("password_reset")

        context["usuario"] = usuario

        if not respuesta or not nueva_password:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "password_reset.html", context)

        if usuario.respuesta_seguridad.lower() != respuesta.lower():
            messages.error(request, "La respuesta no coincide.")
            return render(request, "password_reset.html", context)

        usuario.set_password(nueva_password)
        usuario.save()
        messages.success(request, "Contraseña cambiada correctamente.")
        return redirect("login")

    return render(request, "password_reset.html", context)


def meme(request):
    return render(request, "meme.html")


@login_required
def student_dashboard(request):
    latest_result = Result.objects.filter(student=request.user).select_related("test").first()
    progress_entries = Progress.objects.filter(student=request.user).order_by("phase")
    active_test = Test.objects.filter(is_active=True).order_by("name").first()
    certificate = Certificate.objects.filter(student=request.user, valid=True).first()

    return render(
        request,
        "estudiantes.html",
        {
            "latest_result": latest_result,
            "progress_entries": progress_entries,
            "active_test": active_test,
            "certificate": certificate,
        },
    )

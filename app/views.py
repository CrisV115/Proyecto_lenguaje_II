from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegistroForm
from .models import Usuario


# =========================
# 🏠 HOME
# =========================
def home(request):
    # Muestra la página principal
    return render(request, 'home.html')


# =========================
# 📝 REGISTER
# =========================
def register(request):

    if request.method == 'POST':
        form = RegistroForm(request.POST)

        # Si el formulario es válido (ya valida usuario, email, contraseñas)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect('login')

        else:
            # Si hay errores, se enviarán al template automáticamente
            messages.error(request, "Corrija los errores del formulario.")

    else:
        form = RegistroForm()

    return render(request, 'register.html', {'form': form})


# =========================
# 🔐 LOGIN
# =========================
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validar campos vacíos
        if not username or not password:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("estudiantes")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return redirect("login")

    return render(request, "login.html")


# =========================
# 🔑 RECUPERAR CONTRASEÑA
# =========================
def password_reset(request):

    if request.method == "POST":

        # -------------------------
        # PASO 1: INGRESAR EMAIL
        # -------------------------
        if "email" in request.POST and "respuesta_seguridad" not in request.POST:

            email = request.POST.get("email")

            if not email:
                messages.error(request, "Debe ingresar un correo.")
                return redirect("password_reset")

            usuario = Usuario.objects.filter(email=email).first()

            if not usuario:
                messages.error(request, "No existe un usuario con ese correo.")
                return redirect("password_reset")

            # Mostrar pregunta de seguridad
            return render(request, "password_reset.html", {"usuario": usuario})


        # -------------------------
        # PASO 2: VALIDAR RESPUESTA
        # -------------------------
        if "respuesta_seguridad" in request.POST:

            email = request.POST.get("email")
            respuesta = request.POST.get("respuesta_seguridad")
            nueva_password = request.POST.get("nueva_password")

            usuario = Usuario.objects.filter(email=email).first()

            if not usuario:
                messages.error(request, "Error inesperado.")
                return redirect("password_reset")

            # Validar campos vacíos
            if not respuesta or not nueva_password:
                messages.error(request, "Todos los campos son obligatorios.")
                return render(request, "password_reset.html", {"usuario": usuario})

            # Validar respuesta de seguridad
            if usuario.respuesta_seguridad.lower() == respuesta.lower():

                usuario.set_password(nueva_password)
                usuario.save()

                messages.success(request, "Contraseña cambiada correctamente.")
                return redirect("login")

            else:
                messages.error(request, "La respuesta no coincide.")
                return render(request, "password_reset.html", {"usuario": usuario})

    return render(request, "password_reset.html")

def meme(request):
    return render(request, 'meme.html')

def estudiantes(request):
    return render(request, 'estudiantes.html')

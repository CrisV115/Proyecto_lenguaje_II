from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, AsignacionForm, EntregaAsignacionForm, CalificacionForm
from .models import Usuario, Asignacion, EntregaAsignacion
from django.utils import timezone


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
            return redirect("home")
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


# =========================
# 📚 VISTAS PARA ASIGNACIONES
# =========================

@login_required
def listar_asignaciones(request):
    """Lista todas las asignaciones disponibles"""
    if request.user.tipo_usuario == 'profesor':
        asignaciones = Asignacion.objects.filter(profesor=request.user)
    else:
        asignaciones = Asignacion.objects.all()
    
    return render(request, 'asignaciones/listar_asignaciones.html', {'asignaciones': asignaciones})


@login_required
def crear_asignacion(request):
    """Solo profesores pueden crear asignaciones"""
    if request.user.tipo_usuario != 'profesor':
        messages.error(request, "Solo los profesores pueden crear asignaciones.")
        return redirect('listar_asignaciones')
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.profesor = request.user
            asignacion.save()
            messages.success(request, "Asignación creada correctamente.")
            return redirect('listar_asignaciones')
    else:
        form = AsignacionForm()
    
    return render(request, 'asignaciones/crear_asignacion.html', {'form': form})


@login_required
def detalle_asignacion(request, asignacion_id):
    """Muestra el detalle de una asignación y permite subir entrega o calificar"""
    asignacion = get_object_or_404(Asignacion, pk=asignacion_id)
    
    # Verificar si el estudiante ya entregó
    entrega = None
    if request.user.tipo_usuario == 'estudiante':
        entrega = EntregaAsignacion.objects.filter(asignacion=asignacion, estudiante=request.user).first()
    
    # Obtener todas las entregas (para profesores)
    entregas = None
    if request.user.tipo_usuario == 'profesor' and asignacion.profesor == request.user:
        entregas = EntregaAsignacion.objects.filter(asignacion=asignacion)
    
    return render(request, 'asignaciones/detalle_asignacion.html', {
        'asignacion': asignacion,
        'entrega': entrega,
        'entregas': entregas
    })


@login_required
def subir_entrega(request, asignacion_id):
    """Los estudiantes suben sus entregas"""
    asignacion = get_object_or_404(Asignacion, pk=asignacion_id)
    
    if request.user.tipo_usuario != 'estudiante':
        messages.error(request, "Solo los estudiantes pueden subir entregas.")
        return redirect('detalle_asignacion', asignacion_id=asignacion_id)
    
    # Verificar si ya existe una entrega
    entrega, created = EntregaAsignacion.objects.get_or_create(
        asignacion=asignacion,
        estudiante=request.user
    )
    
    if request.method == 'POST':
        form = EntregaAsignacionForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.estudiante = request.user
            entrega.asignacion = asignacion
            entrega.save()
            messages.success(request, "Entrega subida correctamente.")
            return redirect('detalle_asignacion', asignacion_id=asignacion_id)
    else:
        form = EntregaAsignacionForm(instance=entrega)
    
    return render(request, 'asignaciones/subir_entrega.html', {'form': form, 'asignacion': asignacion})


@login_required
def calificar_entrega(request, entrega_id):
    """Los profesores califican las entregas de los estudiantes"""
    entrega = get_object_or_404(EntregaAsignacion, pk=entrega_id)
    
    # Verificar que el profesor es el dueño de la asignación
    if request.user.tipo_usuario != 'profesor' or entrega.asignacion.profesor != request.user:
        messages.error(request, "No tienes permiso para calificar esta entrega.")
        return redirect('listar_asignaciones')
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=entrega)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.fecha_calificacion = timezone.now()
            entrega.save()
            messages.success(request, f"Entrega calificada con {entrega.calificacion}/100")
            return redirect('detalle_asignacion', asignacion_id=entrega.asignacion.id)
    else:
        form = CalificacionForm(instance=entrega)
    
    return render(request, 'asignaciones/calificar_entrega.html', {'form': form, 'entrega': entrega})

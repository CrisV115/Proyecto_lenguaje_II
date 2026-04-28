from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    telefono = models.CharField(max_length=10)

    PREGUNTAS = [
        ('mascota', '¿Cómo se llama tu primera mascota?'),
        ('madre', '¿Cuál es el segundo nombre de tu madre?'),
        ('ciudad', '¿En qué ciudad naciste?'),
    ]

    ROLES = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
    ]

    tipo_usuario = models.CharField(max_length=20, choices=ROLES, default='estudiante')
    pregunta_seguridad = models.CharField(max_length=50, choices=PREGUNTAS)
    respuesta_seguridad = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class Asignacion(models.Model):
    """Modelo para las asignaciones/tareas que suben los estudiantes"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField()
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='asignaciones')
    
    class Meta:
        verbose_name_plural = "Asignaciones"
    
    def __str__(self):
        return self.titulo


class EntregaAsignacion(models.Model):
    """Modelo para las entregas de asignaciones por parte de los estudiantes"""
    asignacion = models.ForeignKey(Asignacion, on_delete=models.CASCADE, related_name='entregas')
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='entregas')
    archivo = models.FileField(upload_to='entregas/')
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    comentario_estudiante = models.TextField(blank=True, null=True)
    
    # Campos para calificación
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    comentario_profesor = models.TextField(blank=True, null=True)
    fecha_calificacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['asignacion', 'estudiante']
    
    def __str__(self):
        return f"{self.estudiante.username} - {self.asignacion.titulo}"

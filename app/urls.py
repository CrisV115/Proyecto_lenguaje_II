from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('meme/', views.meme, name='meme'),
    
    # URLs para asignaciones
    path('asignaciones/', views.listar_asignaciones, name='listar_asignaciones'),
    path('asignaciones/crear/', views.crear_asignacion, name='crear_asignacion'),
    path('asignaciones/<int:asignacion_id>/', views.detalle_asignacion, name='detalle_asignacion'),
    path('asignaciones/<int:asignacion_id>/subir/', views.subir_entrega, name='subir_entrega'),
    path('entregas/<int:entrega_id>/calificar/', views.calificar_entrega, name='calificar_entrega'),
]

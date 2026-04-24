from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.role_dashboard, name="role_dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("primer-ingreso/cambiar-clave/", views.force_password_change, name="force_password_change"),
    path("password-reset/", views.password_reset_security, name="password_reset"),
    path("meme/", views.meme, name="meme"),
    path("estudiantes/", views.student_dashboard, name="student_dashboard"),
    path("profesores/", views.teacher_dashboard, name="teacher_dashboard"),
]

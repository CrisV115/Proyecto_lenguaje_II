from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("password-reset/", views.password_reset_security, name="password_reset"),
    path("meme/", views.meme, name="meme"),
    path("estudiantes/", views.student_dashboard, name="student_dashboard"),
]

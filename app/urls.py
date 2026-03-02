from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),  # 👈 ESTA ES IMPORTANTE
    path('register/', views.register, name='register'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('meme/', views.meme, name='meme'),
    path('estudiantes/', views.estudiantes, name='estudiantes'),
     # Recuperar contraseña
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html'
         ), 
         name='password_reset'),

    path('password_reset_done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),

    path('reset_done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    path('login/', views.login_view, name='login'),

    path('password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html'
        ),
        name='password_reset'),

    path('password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html'
        ),
        name='password_reset_confirm'),

    path('reset_done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete'),
]

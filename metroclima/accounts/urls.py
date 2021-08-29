from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/',
         auth_views.PasswordChangeView.as_view(template_name='accounts/password.html'),
         name='change_password'),
    path('success/',
         auth_views.PasswordChangeDoneView.as_view(template_name='accounts/success.html'),
         name='password_change_done'),
]

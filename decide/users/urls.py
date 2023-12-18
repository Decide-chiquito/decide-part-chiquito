from django.urls import path

from .views import RegisterView, LoginView, LogoutView, RequestPasswordReset, ChangePassword, CertLoginView, EditProfileView, NoticeView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', RequestPasswordReset.as_view(), name='password_reset'),
    path('change-password/<str:uidb64>/<str:token>/', ChangePassword.as_view(), name='change_password'),
    path('notice/', NoticeView.as_view(), name='notice'),
    path('cert-login/', CertLoginView.as_view(), name='cert_login'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
]

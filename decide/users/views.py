import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from users.forms import EmailForm, PasswordForm
from decide import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import gettext as _
from .forms import CertificateLoginForm
from django.contrib.auth.backends import ModelBackend



class RegisterView(APIView):
    def get(self, request):
        return render(request, 'users/register.html')

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        confirm_password = request.data.get('confirm_password', '')
        email = request.data.get('email', '') 

        if password != confirm_password:
            return render(request, 'registration/register_fail.html', {'error': _('The passwords do not match.')})        
        try:
            user = User.objects.create_user(username, password=password, email=email)
            return render(request, 'registration/register_success.html', {'message': _('Successful registration. You are now registered.')})        
        except IntegrityError:
            return render(request, 'registration/register_fail.html', {'error': _('The username is already in use.')})        



class LoginView(APIView):
    template_name = 'users/login.html'

    def get(self, request):
        user = request.user
        return render(request, self.template_name, {'user': user})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, self.template_name, {'error': _('invalid credentials')})

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return redirect('/')

class RequestPasswordReset(APIView):
    def post(self, request):
        form = EmailForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, email=form.cleaned_data['email'])

            if self.validate_email(user.email):
                # Generar el token único
                token = default_token_generator.make_token(user)

                # Generar la URL de verificación por correo electrónico
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                new_password_url = reverse('users:change_password', args=[uid, token])

                # Enviar el correo electrónico de verificación
                template = get_template('registration/password_email.html')
                content = template.render({'new_password_url': settings.BASEURL + new_password_url, 'username': user.username})
                message = EmailMultiAlternatives(
                    'Cambio de contraseña',
                    content,
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )

                message.attach_alternative(content, 'text/html')
                message.send()
                return redirect('/')

        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        form = EmailForm()
        return render(request, 'registration/make_petition_form.html', {'form': form})

    def validate_email(self, email):
        patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if re.match(patron, email):
            return True
        else:
            return False



class ChangePassword(APIView):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            form = PasswordForm()
            return render(request, 'registration/change_password_form.html', {'form': form})
        else:
            return render(request, 'registration/petition_new_password_error.html')

    def post(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            form = PasswordForm(request.POST)
            form.old_password = user.password
            if form.is_valid():
                user.password = make_password(form.cleaned_data['password'])
                user.save()
                return redirect('/')
            else:
                return render(request, 'registration/change_password_form.html', {'form': form})
        else:
            return render(request, 'registration/petition_new_password_error.html')

    def get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user


class CertLoginView(APIView):
    template_name = 'registration/cert_login.html'

    def get(self, request, *args, **kwargs):
        cert_form = CertificateLoginForm()
        return render(request, self.template_name, {'cert_form': cert_form})

    def post(self, request, *args, **kwargs):
        cert_form = CertificateLoginForm(request.POST, request.FILES)
        if cert_form.is_valid():
            user = cert_form.get_or_create_user()
            if user:
                backend = ModelBackend()
                user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
                login(request, user)
                return render(request, 'registration/cert_success.html', {'user': user})
            else:
                return render(request, 'registration/cert_fail.html')

        return render(request, 'registration/cert_fail.html')

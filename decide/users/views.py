from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import gettext as _

class RegisterView(APIView):
    def get(self, request):
        return render(request, 'users/register.html')

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        confirm_password = request.data.get('confirm_password', '')
        email = request.data.get('email', '') 

        if not username or not password or not confirm_password:
            return Response({'error': _('Username and password are required.')}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != confirm_password:
            return Response({'error': _('The passwords do not match.')}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.create_user(username, password=password, email=email)
            token, _ = Token.objects.get_or_create(user=user)
            success_message = _('Successful registration. You are now registered.')
            return Response({'user_pk': user.pk, 'token': token.key}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': _('The username is already in use.')}, status=status.HTTP_400_BAD_REQUEST)



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
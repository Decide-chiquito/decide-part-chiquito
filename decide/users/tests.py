from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APIClient

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_register_view(self):
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')


    def test_register(self):
        data = {'username': 'voter_correct',
                'password': '1234',
                'confirm_password': '1234',
                'email': 'voter1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_pk', response.data)

        user = User.objects.get(username='voter_correct')
        self.assertTrue(user.check_password('1234'))
        self.assertEqual(user.email, 'voter1@gmail.com')

    def test_register_existing_username(self):
        User.objects.create_user(username='username_exist', password='1234')
        data = {'username': 'username_exist',
                'password': '12345',
                'confirm_password': '12345',
                'email': 'user1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('The username is already in use.', response.data['error'])

    def test_register_not_username(self):
        User.objects.create_user(username='username_exist', password='1234')
        data = {'username': '',
                'password': '12345',
                'confirm_password': '12345',
                'email': 'user1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Username and password are required.', response.data['error'])


    def test_register_distinct_password(self):
        data = {'username': 'user1',
                'password': '1234',
                'confirm_password': '12345',
                'email': 'user1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('The passwords do not match.', response.data['error'])

class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.login_url = reverse('users:login')

    def test_get_login_view(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login_success(self):
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_login_failure(self):
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'invalid credentials')

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
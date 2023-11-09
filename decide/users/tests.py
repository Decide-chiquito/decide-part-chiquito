from django.test import TestCase
from django.contrib.auth.models import User
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
        self.assertIn('El nombre de usuario ya está en uso.', response.data['error'])

    def test_register_not_username(self):
        User.objects.create_user(username='username_exist', password='1234')
        data = {'username': '',
                'password': '12345',
                'confirm_password': '12345',
                'email': 'user1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Se requieren nombre de usuario y contraseña.', response.data['error'])


    def test_register_distinct_password(self):
        data = {'username': 'user1',
                'password': '1234',
                'confirm_password': '12345',
                'email': 'user1@gmail.com'}
        response = self.client.post('/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Las contraseñas no coinciden.', response.data['error'])

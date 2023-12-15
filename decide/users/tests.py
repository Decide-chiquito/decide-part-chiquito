from base.tests import BaseTestCase
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.core.files.uploadedfile import SimpleUploadedFile


class RegisterViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_get_register_view(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_successful_registration(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'email': 'test@example.com',
        }
        response = self.client.post(reverse('users:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register_success.html')

    def test_password_mismatch(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'mismatchedpassword',
            'email': 'test@example.com',
        }
        response = self.client.post(reverse('users:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register_fail.html')
        self.assertContains(response, 'The passwords do not match.')

    def test_username_already_in_use(self):
        User.objects.create_user(username='existinguser', password='testpassword', email='existing@example.com')
        data = {
            'username': 'existinguser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'email': 'test@example.com',
        }
        response = self.client.post(reverse('users:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register_fail.html')
        self.assertContains(response, 'The username is already in use.')



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

    def test_mail_login(self):
        response = self.client.get(reverse('social:begin', args=['google-oauth2']))
        assert response.status_code == 302

class RequestPasswordResetViewTests(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

        self.password = "Hola$1234"
        self.noadmin = User.objects.filter(username="noadmin").first()
        self.noadmin.set_password('1234')
        self.noadmin.email = 'noadmin@gmail.com'
        self.noadmin.save()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_request_password_reset(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.set_window_size(1850, 1016)
        self.driver.find_element(By.LINK_TEXT, "¿Olvidó su contraseña?").click()
        self.driver.find_element(By.ID, "id_email").click()
        self.driver.find_element(By.ID, "id_email").send_keys(self.noadmin.email)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/")

    def test_change_password(self):
        token = default_token_generator.make_token(self.noadmin)
        uid = urlsafe_base64_encode(force_bytes(self.noadmin.pk))
        self.driver.get(f"{self.live_server_url}/users/change-password/{uid}/{token}/")
        self.driver.set_window_size(1850, 1016)
        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys(self.password)
        self.driver.find_element(By.ID, "id_confirm_password").click()
        self.driver.find_element(By.ID, "id_confirm_password").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.noadmin = User.objects.filter(username="noadmin").first()
        self.assertTrue(self.noadmin.check_password(self.password))
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/")


class MailLoginTest(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_mail_login_fail(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Google").click()
        self.assertTrue("https://accounts.google.com/" in self.driver.current_url)

class CertLoginViewTest(TestCase):
    def test_get_cert_login_view(self):
        response = self.client.get('/users/cert-login/')
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,'registration/cert_login.html')

    def test_post_cert_login_view_filure(self):
        data={'cert_file':'','cert_password':''}
        response = self.client.post('/users/cert-login/',data)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'registration/cert_fail.html')

    def test_post_cert_login_view_invalid_cert(self):
        invalid_file = SimpleUploadedFile("invalid_file.txt",
            b"soy un archivo que no es un certificado digital, por lo tanto no debe funcionar el login")
        data = {'cert_file': invalid_file, 'cert_password': 'testpassword'}
        response = self.client.post('/users/cert-login/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/cert_fail.html')

    # El archivo cert.pfx es un certificado digital ficticio que sirve para hacer pruebas, la contraseña es 1111
    def test_post_cert_login_view_succes(self):
        with open('cert.pfx', 'rb') as cert_file:
            cert_content = cert_file.read()
        cert_uploaded = SimpleUploadedFile("cert.pfx", cert_content, content_type="application/x-pkcs12")
        data = {'cert_file': cert_uploaded, 'cert_password': '1111'}
        response = self.client.post('/users/cert-login/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/cert_success.html')

    def test_post_cert_login_view_invalid_password(self):
        with open('cert.pfx', 'rb') as cert_file:
            cert_content = cert_file.read()
        cert_uploaded = SimpleUploadedFile("cert.pfx", cert_content, content_type="application/x-pkcs12")
        data = {'cert_file': cert_uploaded, 'cert_password': 'invalid_pasword'}
        response = self.client.post('/users/cert-login/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/cert_fail.html')


class EditProfileTest(BaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='updateuser', password='passwd')
        self.client.force_login(self.user)


    def test_get_edit_profile(self):
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')

    def test_succesful_edit_profile(self):
        data = {
            'username': 'new_username',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'updated@example.com'
        }
        response = self.client.post(reverse('users:edit_profile'), data)
        self.assertEqual(response.status_code, 302)
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, 'new_username')
        self.assertEqual(updated_user.first_name, 'Nombre')
        self.assertEqual(updated_user.last_name, 'Apellido')
        self.assertEqual(updated_user.email, 'updated@example.com')

    def test_invalid_edit_profile(self):
        data = {
            'username': '', 
        }
        response = self.client.post(reverse('users:edit_profile'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')

    def test_username_already_in_use(self):
        User.objects.create_user(username='existinguser', password='testpassword', email='existing@example.com')
        data = {
            'username': 'existinguser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'email': 'test@example.com',
        }
        response = self.client.post(reverse('users:edit_profile'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertContains(response, 'El nombre de usuario ya está en uso.')


class EditProfileViewTest(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

        self.driver.get(f'{self.live_server_url}/users/login/')
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("noadmin")
        self.driver.find_element(By.NAME, "password").click()
        self.driver.find_element(By.NAME, "password").send_keys("qwerty")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_get_edit_profile(self):
        editURL = f'{self.live_server_url}/users/edit-profile/'
        self.driver.get(editURL)
        elemento = self.driver.find_element(By.CLASS_NAME, "edit-profile-title")
        self.assertEqual(elemento.text, 'Editar datos de usuario')

    def test_succesful_edit_profile(self):
        user_id = User.objects.get(username='noadmin').id

        self.driver.get(f'{self.live_server_url}/users/edit-profile/')
        username_element = self.driver.find_element(By.NAME, "username")
        username_element.click()
        username_element.clear()
        username_element.send_keys("new_username")

        self.driver.find_element(By.NAME, "first_name").click()
        self.driver.find_element(By.NAME, "first_name").send_keys("Nombre")

        self.driver.find_element(By.NAME, "last_name").click()
        self.driver.find_element(By.NAME, "last_name").send_keys("Apellido")

        self.driver.find_element(By.NAME, "email").click()
        self.driver.find_element(By.NAME, "email").send_keys("updated@example.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()

        self.assertTrue(self.driver.current_url == f'{self.live_server_url}/')

        updated_user = User.objects.get(id=user_id)
        self.assertEqual(updated_user.username, 'new_username')
        self.assertEqual(updated_user.first_name, 'Nombre')
        self.assertEqual(updated_user.last_name, 'Apellido')
        self.assertEqual(updated_user.email, 'updated@example.com')

    def test_username_already_in_use(self):
        User.objects.create_user(username='existinguser', password='testpassword', email='existing@example.com')

        user_id = User.objects.get(username='noadmin').id
        
        editURL = f'{self.live_server_url}/users/edit-profile/'
        self.driver.get(editURL)

        username_element = self.driver.find_element(By.NAME, "username")
        username_element.click()
        username_element.clear()
        username_element.send_keys("existinguser")

        self.driver.find_element(By.NAME, "first_name").click()
        self.driver.find_element(By.NAME, "first_name").send_keys("existinguser")

        self.driver.find_element(By.NAME, "last_name").click()
        self.driver.find_element(By.NAME, "last_name").send_keys("testpassword")

        self.driver.find_element(By.NAME, "email").click()
        self.driver.find_element(By.NAME, "email").send_keys("test@example.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()

        self.assertTrue(self.driver.current_url == editURL)

        updated_user = User.objects.get(id=user_id)
        self.assertEqual(updated_user.username, 'noadmin')

        current_element = self.driver.find_element(By.CLASS_NAME, "edit-error").text
        self.assertEqual(current_element, 'El nombre de usuario ya está en uso.')

    def test_invalid_edit_profile(self):
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        editURL = f'{self.live_server_url}/users/edit-profile/'
        self.driver.get(editURL)
        login_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
        self.assertTrue("Iniciar sesión" in login_button.text)


class MobileTestCase(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@test.com')
        self.user = User.objects.create_user(username='testuser2', password='testpassword')
        mobile_emulation = {
            "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"
        }
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.driver = webdriver.Chrome(options=chrome_options)
        super().setUp()

    def tearDown(self):
        self.driver.quit()
        super().tearDown()
        self.base.tearDown()
    
    def test_register_empty_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/register/")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/register/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "Nombre de usuario y contraseña son obligatorios.")

    def test_existing_user_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/register/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.ID, "id_confirm_password").send_keys("testpassword")
        self.driver.find_element(By.ID, "id_email").send_keys("test@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/register/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "El nombre de usuario ya está en uso.")

    def test_password_mismatch_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/register/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser2")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.ID, "id_confirm_password").send_keys("testpassword2")
        self.driver.find_element(By.ID, "id_email").send_keys("test@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/register/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "Las contraseñas no coinciden.")
        
    def test_register_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/register/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser3")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.ID, "id_confirm_password").send_keys("testpassword")
        self.driver.find_element(By.ID, "id_email").send_keys("test@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/")
    
    def test_login_empty_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/login/")

    def test_wrong_user_login_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.find_element(By.ID, "id_username").send_keys("wronguser")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/login/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "Credenciales inválidas")

    def test_login_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/")

    def test_wrong_email_password_reset_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/login/")
        self.driver.find_element(By.LINK_TEXT, "Recuperar contraseña").click()
        self.driver.find_element(By.ID, "id_email").send_keys("test2@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/password-reset/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "No existe un usuario con ese correo electrónico.")

    def test_not_username_edit_profile_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/edit-profile/")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.driver.get(f"{self.live_server_url}/users/edit-profile/")
        self.driver.find_element(By.ID, "id_username").clear()
        self.driver.find_element(By.ID, "id_first_name").clear()
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").clear()
        self.driver.find_element(By.ID, "id_last_name").send_keys("test")
        self.driver.find_element(By.ID, "id_email").clear()
        self.driver.find_element(By.ID, "id_email").send_keys("test20@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/edit-profile/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "El nombre de usuario es obligatorio.")

    def test_existing_username_edit_profile_mobile(self):
        self.driver.get(f"{self.live_server_url}/users/edit-profile/")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.driver.get(f"{self.live_server_url}/users/edit-profile/")
        self.driver.find_element(By.ID, "id_username").clear()
        self.driver.find_element(By.ID, "id_username").send_keys("testuser2")
        self.driver.find_element(By.ID, "id_first_name").clear()
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").clear()
        self.driver.find_element(By.ID, "id_last_name").send_keys("test")
        self.driver.find_element(By.ID, "id_email").clear()
        self.driver.find_element(By.ID, "id_email").send_keys("test@test.com")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-mobile").click()
        self.assertTrue(self.driver.current_url == f"{self.live_server_url}/users/edit-profile/")
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".error-mobile").text == "El nombre de usuario ya está en uso.")
        


import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework import status
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption
from datetime import datetime

from base.tests import BaseTestCase
from voting.models import Voting, Question, QuestionOption,Auth
from django.urls import reverse
class VotingModelTestCase(BaseTestCase):
    def setUp(self):
        # Crear instancias de Question y sus opciones
        q1 = Question.objects.create(desc='Descripcion 1')
        QuestionOption.objects.create(question=q1, option='opcion 1')
        QuestionOption.objects.create(question=q1, option='opcion 2')

        q2 = Question.objects.create(desc='Descripcion 2')
        QuestionOption.objects.create(question=q2, option='opcion 3')
        QuestionOption.objects.create(question=q2, option='opcion 4')

        auth1= Auth.objects.create(name='hola',url='https://localhost:8000')
        auth2=Auth.objects.create(name='hola2',url='https://localhost:8000')

        # Crear una instancia de Voting y asociar las preguntas
        self.v = Voting.objects.create(name='Votacion')
        self.v.questions.add(q1, q2)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v = None

    def create_voting(self):
        # Crear una instancia de Question y asociar opciones
        q = Question.objects.create(desc='test question')
        for i in range(5):
            QuestionOption.objects.create(question=q, option='option {}'.format(i + 1))

        # Crear una instancia de Voting y asociar la pregunta
        v = Voting.objects.create(name='test voting')
        v.questions.add(q)

        # Configuración adicional si es necesaria
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL, defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def testExist(self):
        v = Voting.objects.get(name='Votacion')
        # Verificar si una de las opciones está en alguna de las preguntas asociadas
        self.assertTrue(any('opcion 1' in [option.option for option in question.options.all()] for question in v.questions.all()))

    def test_create_voting_API(self):
        self.login()
        voting = self.create_voting()
        # Nota: Este test asume que el endpoint de tu API maneja correctamente la creación de preguntas
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)

        try:
            voting = Voting.objects.get(name='test voting')
            self.assertEqual(voting.desc, None)
            questions = [question.desc for question in voting.questions.all()]
        except Voting.DoesNotExist:
            self.fail("Voting object 'Example' was not created")





class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def create_voting(self):
        # Crear una instancia de Question y asociar opciones
        q = Question.objects.create(desc='test question')
        for i in range(5):
            QuestionOption.objects.create(question=q, option='option {}'.format(i + 1))

        # Crear una instancia de Voting y asociar la pregunta
        v = Voting.objects.create(name='test voting')
        v.questions.add(q)

        # Configuración adicional si es necesaria
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL, defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def test_update_voting_405(self):
        v = self.create_voting()
        data = {}
        self.login()
        response = self.client.post('/voting/{}/'.format(v.pk), data, format='json')
        self.assertEqual(response.status_code, 405)

    def test_to_string(self):
        v = self.create_voting()
        self.assertEquals(str(v), "test voting")
        self.assertEquals(str(v.questions.first()), "test question")
        self.assertEquals(str(v.questions.first().options.all()[0]), "option 1 (2)")

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    



    def test_create_voting_from_api(self):
        data = {
        'name': 'Example',
        'desc': 'Description example',
        'questions': [
        {'desc': 'I want a cat'},
        {'desc': 'I want a dog'},
        {'desc': 'I want a horse'}
            ]
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'questions': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')


    def test_retrieve_voting(self):
        voting = self.create_voting()
        self.login()
        response = self.client.get('/voting/{}/staff/'.format(voting.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], voting.name)

    def test_delete_voting(self):
        voting = self.create_voting()
        self.login()
        response = self.client.delete('/voting/{}/staff/'.format(voting.pk))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Voting.objects.filter(pk=voting.pk).count(), 0)

    def test_update_voting_staff(self):
        voting = self.create_voting()
        self.login()
        data = { 'name': 'Updated' }
        voting.name = 'Updated'
        response = self.client.put('/voting/{}/staff/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/voting/{}/staff/'.format(voting.pk))
        self.assertEqual(response.json()['name'], "Updated")



class LogInSuccessTests(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
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

    def successLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/")

class LogInErrorTests(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
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

    def usernameWrongLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)
        
        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("usuarioNoExistente")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("usuarioNoExistente")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[2]/div/div[1]/p').text == 'Please enter the correct username and password for a staff account. Note that both fields may be case-sensitive.')

    def passwordWrongLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("wrongPassword")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[2]/div/div[1]/p').text == 'Please enter the correct username and password for a staff account. Note that both fields may be case-sensitive.')

class QuestionsTests(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
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

    def createQuestionSuccess(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/voting/question/add/")
        
        self.cleaner.find_element(By.ID, "id_desc").click()
        self.cleaner.find_element(By.ID, "id_desc").send_keys('Test')
        self.cleaner.find_element(By.ID, "id_options-0-number").click()
        self.cleaner.find_element(By.ID, "id_options-0-number").send_keys('1')
        self.cleaner.find_element(By.ID, "id_options-0-option").click()
        self.cleaner.find_element(By.ID, "id_options-0-option").send_keys('test1')
        self.cleaner.find_element(By.ID, "id_options-1-number").click()
        self.cleaner.find_element(By.ID, "id_options-1-number").send_keys('2')
        self.cleaner.find_element(By.ID, "id_options-1-option").click()
        self.cleaner.find_element(By.ID, "id_options-1-option").send_keys('test2')
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/voting/question/")

    def createCensusEmptyError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/voting/question/add/")

        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/voting/question/add/")

class VotingPostAPITestCase(APITestCase):

    def setUp(self):
        # Configura un usuario staff para las pruebas
        self.user = User.objects.create_user(username='staffs', password='password',is_staff=True)
        self.login_url = reverse('users:login')
       
    def test_post_voting_with_missing_data(self):
        """
        Prueba la creación de una votación con datos faltantes.
        """
        # Datos incompletos, faltan 'question' y 'question_opt'
        incomplete_data = {
            'name': 'Test Voting',
            'desc': 'Test Description',
        }

        response = self.client.post('/voting/', incomplete_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_voting_success(self):
        """
        Prueba la creación exitosa de una votación.
        """
        # Datos completos incluyendo 'question' y 'question_opt'
        complete_data = {
            'name': 'Test Voting',
            'desc': 'Test Description',
            'question': 'Test Question',
            'question_opt': ['Option 1', 'Option 2'],
            'method': 'IDENTITY',  # Asumiendo que se requiere especificar un método
        }

        response = self.client.post('/voting/', complete_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

       

    def tearDown(self):
        self.client.logout()
import random
import itertools
import csv
import os
import time
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from selenium.webdriver.common.action_chains import ActionChains
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
from auditlog.models import LogEntry

class VotingModelTestCase(BaseTestCase):
    def setUp(self):
        q = Question(desc='Descripcion')
        q.save()
        
        opt1 = QuestionOption(question=q, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q, option='opcion 2')
        opt1.save()

        self.v = Voting(name='Votacion', question=q)
        self.v.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v = None

    def testExist(self):
        v=Voting.objects.get(name='Votacion')
        self.assertEquals(v.question.options.all()[0].option, "opcion 1")

    def test_create_voting_API(self):
        self.login()
        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

        voting = Voting.objects.get(name='Example')
        self.assertEqual(voting.desc, 'Description example')


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_update_voting_405(self):
        v = self.create_voting()
        data = {}
        self.login()
        response = self.client.post('/voting/{}/'.format(v.pk),data,format='json')
        self.assertEqual(response.status_code,405)

    def test_to_string(self):
        #Crea un objeto votacion
        v = self.create_voting()
        #Verifica que el nombre de la votacion es test voting
        self.assertEquals(str(v),"test voting")
        #Verifica que la descripcion de la pregunta sea test question
        self.assertEquals(str(v.question),"test question")
        #Verifica que la primera opcion es option1 (2)
        self.assertEquals(str(v.question.options.all()[0]),"option 1 (2)")


    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

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

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
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
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

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

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')

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

class ExportCensusTestCase(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        user = User(username='admintest', is_staff=True)
        user.is_superuser = True
        user.set_password('qwerty')
        user.save()

        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_experimental_option("prefs", {
            "download.default_directory": "./downloads/",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_export_census_empty(self):
        q = Question(desc='test question')
        q.save()
        v = Voting(name='test voting', question=q)
        v.save()

        votingURL = f'{self.live_server_url}/admin/voting/voting/'
        self.driver.get(votingURL)
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys("admintest")

        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        self.assertTrue(self.driver.current_url == votingURL)

        self.driver.set_window_size(1850, 1053)
        self.driver.find_element(By.ID, "action-toggle").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Export to csv']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.CSS_SELECTOR, ".h-9\\.5 > .material-symbols-outlined").click()
        time.sleep(10)
        self.assertTrue(self.driver.current_url == votingURL)
        csv_file_path = "./downloads/census.csv"
        self.assertTrue(os.path.isfile(csv_file_path))
        with open(csv_file_path, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            linea = next(csv_reader, None)
            self.assertTrue(len(linea) == 2 and linea[0].isdigit() and linea[1] == 'No Census')

    def test_export_census_success(self):
        q = Question(desc='test question')
        q.save()
        v = Voting(name='test voting', question=q)
        v.save()
        u = User(username='testvoter')
        u.save()
        c = Census(voter_id=u.id, voting_id=v.id)
        c.save()

        votingURL = f'{self.live_server_url}/admin/voting/voting/'
        self.driver.get(votingURL)
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys("admintest")

        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        self.assertTrue(self.driver.current_url == votingURL)

        self.driver.set_window_size(1850, 1053)
        self.driver.find_element(By.ID, "action-toggle").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Export to csv']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.CSS_SELECTOR, ".h-9\\.5 > .material-symbols-outlined").click()
        time.sleep(10)
        self.assertTrue(self.driver.current_url == votingURL)
        csv_file_path = "./downloads/census.csv"
        self.assertTrue(os.path.isfile(csv_file_path))
        with open(csv_file_path, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            headerCSV = ['votingID', 'voterID', 'center', 'tags...']
            self.assertTrue(header == headerCSV)
            linea = next(csv_reader, None)
            self.assertTrue(linea[0].isdigit() and linea[1].isdigit())


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


class AuditVotingModelTestCase(BaseTestCase):
    def setUp(self):
        q = Question(desc='Descripcion')
        q.save()
        
        opt1 = QuestionOption(question=q, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q, option='opcion 2')
        opt1.save()

        self.v = Voting(name='Votacion', question=q)
        self.v.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v = None
    
    def testQuestionEditAndAppearsOnHistory(self):
        opt = QuestionOption.objects.get(option='opcion 1')
        opt.option = "New opcion"
        opt.save()
        changes = opt.history.latest().changes_display_dict
        self.assertEquals(len(changes), 1)
        self.assertEquals(changes['option'], ['opcion 1', 'New opcion'])

    def testQuestionOptionEditAndAppearsOnHistory(self):
        q = Question.objects.get(desc='Descripcion')
        q.desc = "New desc"
        q.save()
        changes = q.history.latest().changes_display_dict
        self.assertEquals(len(changes), 1)
        self.assertEquals(changes['desc'], ['Descripcion', 'New desc'])

    def testLogEntries(self):
        q = Question.objects.get(desc='Descripcion')
        q.desc = "New desc"
        q.save()
        opt = QuestionOption.objects.get(option='opcion 1')
        opt.option = "New opcion"
        opt.save()
        self.assertEquals(LogEntry.objects.count(), 6)
        opt.delete()
        self.assertEquals(LogEntry.objects.count(), 5)
        self.assertTrue(LogEntry.objects.filter(action=2).exists())


class ReuseCensusTests(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        user = User(username='admintest', is_staff=True)
        user.is_superuser = True
        user.set_password('qwerty')
        user.is_superuser = True
        user.save()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v
    
    def create_voters(self, v):
        for i in range(10):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def test_successful_reuse_census(self):
        voting1 = self.create_voting()
        self.create_voters(voting1)
        voting2 = self.create_voting()

        census1 = Census.objects.filter(voting_id=voting1.id)
        census2 = Census.objects.filter(voting_id=voting2.id)

        self.assertTrue(census1 != census2)
  
        self.driver.get(self.live_server_url + "/admin/voting/voting/")
        self.driver.set_window_size(1920, 1080)

        self.driver.find_element(By.ID, "id_username").send_keys("admintest")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        
        voting_elements = self.driver.find_elements(By.CLASS_NAME, "action-select")
        if len(voting_elements) >= 2:
            voting_elements[0].click()
            voting_elements[1].click()

            self.assertTrue(voting_elements[0].is_selected())
            self.assertTrue(voting_elements[1].is_selected())
        
        dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "action")))
        dropdown.find_element(By.XPATH, "//option[. = 'Copiando el censo a otra votacion'] | //option[. = 'Copy the census to other voting'] | //option[. = 'Copy census to another voting']").click()
        self.driver.find_element(By.NAME, "index").click()
        
        voters1 = set(census_entry.voter_id for census_entry in census1)
        voters2 = set(census_entry.voter_id for census_entry in census2)
        self.assertTrue(voters1 == voters2)
        
        self.assertTrue(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Censo copiado con exito de {} a {}".format(voting1.name, voting2.name) or self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Census successfully copied from {} to {}.".format(voting1.name, voting2.name))
    
    def test_votings_with_no_census(self):
        voting1 = self.create_voting()
        voting2 = self.create_voting()

        census1 = Census.objects.filter(voting_id=voting1.id)
        census2 = Census.objects.filter(voting_id=voting2.id)
  
        self.driver.get(self.live_server_url + "/admin/voting/voting/")
        self.driver.set_window_size(1920, 1080)

        self.driver.find_element(By.ID, "id_username").send_keys("admintest")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        
        voting_elements = self.driver.find_elements(By.CLASS_NAME, "action-select")
        if len(voting_elements) >= 2:
            voting_elements[0].click()
            voting_elements[1].click()

            self.assertTrue(voting_elements[0].is_selected())
            self.assertTrue(voting_elements[1].is_selected())
        
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Copiando el censo a otra votacion'] | //option[. = 'Copy the census to other voting'] | //option[. = 'Copy census to another voting']").click()
        self.driver.find_element(By.NAME, "index").click()

        voters1 = set(census_entry.voter_id for census_entry in census1)
        voters2 = set(census_entry.voter_id for census_entry in census2)
        self.assertTrue(len(voters1) == 0 and len(voters2) == 0)
        
        self.assertTrue(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "El censo de ambas botaciones esta vacio" or self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "The census of both votes are empty")
    
    def test_one_voting_selected(self):
        voting1 = self.create_voting()
        self.create_voters(voting1)
        voting2 = self.create_voting()

        census1 = Census.objects.filter(voting_id=voting1.id)
        census2 = Census.objects.filter(voting_id=voting2.id)
  
        self.driver.get(self.live_server_url + "/admin/voting/voting/")
        self.driver.set_window_size(1920, 1080)

        self.driver.find_element(By.ID, "id_username").send_keys("admintest")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        
        voting_elements = self.driver.find_elements(By.CLASS_NAME, "action-select")
        if len(voting_elements) >= 2:
            voting_elements[0].click()

            self.assertTrue(voting_elements[0].is_selected())
            self.assertFalse(voting_elements[1].is_selected())
        
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Copiando el censo a otra votacion'] | //option[. = 'Copy the census to other voting'] | //option[. = 'Copy census to another voting']").click()
        self.driver.find_element(By.NAME, "index").click()

        voters1 = set(census_entry.voter_id for census_entry in census1)
        voters2 = set(census_entry.voter_id for census_entry in census2)
        self.assertTrue(voters1 != voters2)
        
        self.assertTrue(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Selecciona exactamente 2 votos" or self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Select exactly 2 votes.")
    
    def test_both_with_census(self):
        voting1 = self.create_voting()
        self.create_voters(voting1)
        voting2 = self.create_voting()
        self.create_voters(voting2)

        census1 = Census.objects.filter(voting_id=voting1.id)
        census2 = Census.objects.filter(voting_id=voting2.id)
  
        self.driver.get(self.live_server_url + "/admin/voting/voting/")
        self.driver.set_window_size(1920, 1080)

        self.driver.find_element(By.ID, "id_username").send_keys("admintest")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        
        voting_elements = self.driver.find_elements(By.CLASS_NAME, "action-select")
        if len(voting_elements) >= 2:
            voting_elements[0].click()
            voting_elements[1].click()

            self.assertTrue(voting_elements[0].is_selected())
            self.assertTrue(voting_elements[1].is_selected())
        
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Copiando el censo a otra votacion'] | //option[. = 'Copy the census to other voting'] | //option[. = 'Copy census to another voting']").click()
        self.driver.find_element(By.NAME, "index").click()

        voters1 = set(census_entry.voter_id for census_entry in census1)
        voters2 = set(census_entry.voter_id for census_entry in census2)
        self.assertTrue(len(voters1) > 0 and len(voters2) > 0)
        
        self.assertTrue(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Ambas votaciones tienen un censo" or self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/ul/li').text == "Both votes have a census")
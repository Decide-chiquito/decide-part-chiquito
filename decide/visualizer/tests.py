from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from voting.models import Voting, Question, QuestionOption
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.utils import timezone
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings
from selenium.webdriver.support.ui import WebDriverWait

from rest_framework.test import APIClient
from voting.models import Voting, Question, QuestionOption
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from census.models import Census
from voting.models import Voting
from django.utils import timezone
from datetime import timedelta

from mixnet.models import Auth

from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC


from base import mods


class VisualizerTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

    def tearDown(self):
        self.driver.quit()
        self.base.tearDown()

    def create_voting(self, method, data):
        q = Question.objects.create(desc='test question')
        q.save()
        if data == None:
            data = [
                {'option': 'Option 1', 'votes': 5},
                {'option': 'Option 2', 'votes': 3},
                # Añadir más opciones según sea necesario
            ]
        for item in data:
            QuestionOption.objects.create(question=q, option=item['option'])

        v = Voting.objects.create(name='test voting', method=method, start_date=timezone.now(), end_date=timezone.now())
        v.questions.add(q)
        v.postproc=data
        v.save()


    def test_simple_visualizer(self):
        v = self.create_voting('IDENTITY', None)
        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        v_state = self.driver.find_element(By.TAG_NAME, "h2").text
        self.assertIn("Resultados", v_state)
    
    def test_dhondt_voting_visualizer(self):
        q = Question(desc='test question')
        q.save()
        data = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]
        v = Voting(name='test voting', method='DHONDT',seats=100,start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        vState= self.driver.find_element(By.ID,"container2").text
        self.assertTrue(vState)

    def test_webster_voting_visualizer(self):
        q = Question(desc='test question')
        q.save()
        data = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]
        v = Voting(name='test voting', question=q, method='WEBSTER',seats=100,start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()
        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        vState= self.driver.find_element(By.ID,"container2").text
        self.assertTrue(vState)

    def test_identity_voting_visualizer(self):
        q = Question(desc='test question')
        q.save()
        data = [
            { 'option': 'Option 1', 'number': 1, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 3 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 2 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 1 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]
        v = Voting(name='test voting', question=q, method='IDENTITY',seats=100,start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()
        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        vState= self.driver.find_element(By.ID,"container").text
        self.assertTrue(vState)


class LiveStaticticsSeleniumTests(StaticLiveServerTestCase):

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

    def test_liveStatictics(self):

        voting1 = self.create_voting()
        
        voting1.create_pubkey()
        voting1.save()

        user = User(username='user123')
        user.set_password('Testeando1234')
        user.is_active = True
        user.save()

        c = Census(voter_id=user.pk, voting_id=voting1.pk)
        c.save()

        self.driver.get(self.live_server_url + "/admin/voting/voting/")
        self.driver.set_window_size(1920, 1080)

        self.driver.find_element(By.ID, "id_username").send_keys("admintest")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        voting_element = self.driver.find_elements(By.CLASS_NAME, "action-select")[0]
        voting_element.click()
        self.assertTrue(voting_element.is_selected())

        dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "action")))
        dropdown.find_element(By.XPATH, "//option[. = 'Start'] | //option[. = 'start'] | //option[. = 'empezar']").click()
        self.driver.find_element(By.NAME, "index").click()

        self.driver.get(self.live_server_url + "/admin/logout/")
        

        self.driver.get(self.live_server_url + "/users/login/")

        self.driver.find_element(By.NAME, "username").send_keys("user123")
        self.driver.find_element(By.NAME, "password").send_keys("Testeando1234")
        self.driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
        
        self.driver.get(f'{self.live_server_url}/booth/{voting1.id}/')

        voting_element = self.driver.find_elements(By.NAME, "question")[0]
        voting_element.click()
        voting_element = self.driver.find_elements(By.TAG_NAME, "button")
        voting_element[2].click()

        self.driver.get(self.live_server_url + "/users/logout/")

        self.driver.get(f'{self.live_server_url}/visualizer/{voting1.pk}/')


        elements = self.driver.find_element(By.TAG_NAME, "h2").text
        assert len(elements) > 0
        elements = self.driver.find_elements(By.CLASS_NAME, "title")
        assert len(elements) > 0


class LiveStaticticsBaseTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting_identity(self):
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

    def create_voting_dhont(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting',method='DHONDT', question=q, seats=100)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voting_webster(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting',method='WEBSTER', question=q, seats=100)
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
            for _ in range(4):
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
    
    def test_liveStaticticsIdentity(self):
        
        v = self.create_voting_identity()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        self.store_votes(v)

        self.login(user='admin')

        live_tally = v.live_tally(self.token)
        v.tally_votes(self.token)
        tally = v.postproc

        self.assertEqual(tally, live_tally)

    def test_liveStaticticsDhont(self):
        
        v = self.create_voting_dhont()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        self.store_votes(v)

        self.login(user='admin')

        live_tally = v.live_tally(self.token)
        v.tally_votes(self.token)
        tally = v.postproc

        self.assertEqual(tally, live_tally)

    def test_liveStaticticsWebster(self):
        
        v = self.create_voting_webster()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        self.store_votes(v)

        self.login(user='admin')

        live_tally = v.live_tally(self.token)
        v.tally_votes(self.token)
        tally = v.postproc

        self.assertEqual(tally, live_tally)

class ListVisualizerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.list_visualizer_url = reverse_lazy('listEnd') 

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.list_visualizer_url)
        self.assertRedirects(response, '/users/login',status_code=302,target_status_code=301)

    def test_logged_in_no_census(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_visualizer_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'visualizer/listVisualizer.html')
        self.assertEqual(len(response.context['visualizers']), 0)

    def test_logged_in_with_census_no_voting(self):
        Census.objects.create(voter_id=self.user.id, voting_id=1) 
        self.client.force_login(self.user)
        response = self.client.get(self.list_visualizer_url)
        self.assertEqual(len(response.context['visualizers']), 0)

    def test_logged_in_with_census_and_voting(self):
        q = Question(desc='test question1')
        q.save()
        voting = Voting.objects.create(id=1,name="vting1",desc="desc1",question=q,start_date=timezone.now(), end_date=timezone.now() - timedelta(days=1),
                                       method='IDENTITY',seats=10)
        Census.objects.create(voter_id=self.user.id, voting_id=voting.id)
        self.client.force_login(self.user)
        response = self.client.get(self.list_visualizer_url)
        self.assertEqual(len(response.context['visualizers']), 1)


class VisualizerQuestionYesNoTestCase(StaticLiveServerTestCase):

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

    def test_visualizer_yes_no(self):
        q = Question(desc='test question', type = 'YESNO')
        q.save()
        data = [
            { 'option': 'No', 'number': 1, 'votes': 1 },
            { 'option': 'Yes', 'number': 2,'votes': 2 },
        ]
        v = Voting(name='test voting', question=q, method='IDENTITY',start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        votosSi = self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > .text-muted").text
        votosNo = self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > .text-muted").text
        self.assertEqual(votosSi, "2")
        self.assertEqual(votosNo, "1")

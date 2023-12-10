from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from rest_framework.test import APIClient
from voting.models import Voting, Question
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from census.models import Census
from voting.models import Voting
from django.utils import timezone
from datetime import timedelta, datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from django.utils import timezone

import time

class VisualizerTestCase(StaticLiveServerTestCase):

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


    def test_simpleVisualizer(self):        
        q = Question(desc='test question')
        q.save()
        v = Voting(name='test voting', question=q)
        v.save()
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Votación no comenzada")

    def test_dhondt_voting_visualizer(self):
        q = Question(desc='test question')
        q.save()
        data = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]
        v = Voting(name='test voting', question=q, method='DHONDT',seats=100,start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        vState= self.driver.find_element(By.ID,"container2").text
        self.assertTrue(vState)
    
    def test_dhondt_voting_visualizer(self):
        q = Question(desc='test question')
        q.save()
        data = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]
        v = Voting(name='test voting', question=q, method='DHONDT',seats=100,start_date=timezone.now(),end_date=timezone.now(),postproc=data)
        v.save()
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
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
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
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
        response =self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        vState= self.driver.find_element(By.TAG_NAME,"h2").text
        self.assertTrue(vState, "Resultados")
        vState= self.driver.find_element(By.ID,"container").text
        self.assertTrue(vState)



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
        voting = Voting.objects.create(id=1,name="vting1",desc="desc1",question=q,start_date=timezone.now(), end_date=datetime.now() - timedelta(days=1),
                                       method='IDENTITY',seats=10)
        Census.objects.create(voter_id=self.user.id, voting_id=voting.id)
        self.client.force_login(self.user)
        response = self.client.get(self.list_visualizer_url)
        self.assertEqual(len(response.context['visualizers']), 1)


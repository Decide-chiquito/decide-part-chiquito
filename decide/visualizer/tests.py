from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from voting.models import Voting, Question

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

    


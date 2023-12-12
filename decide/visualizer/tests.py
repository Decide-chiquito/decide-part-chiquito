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

    def create_voting(self, method,data):
        q = Question.objects.create(desc='test question')
        if data== None:
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
        return v


    def test_simple_visualizer(self):
        v = self.create_voting('IDENTITY', None)
        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        v_state = self.driver.find_element(By.TAG_NAME, "h2").text
        self.assertIn("Resultados", v_state)

  

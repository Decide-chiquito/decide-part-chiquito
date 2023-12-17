from django.test import TestCase, Client
from base.tests import BaseTestCase
from django.urls import reverse
from .models import Ticket
from .admin import TicketAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from ticket import admin


class TicketModelTestCase(TestCase):
    def test_ticket_creation(self):
        ticket = Ticket.objects.create(title="Test Ticket", description="Test Description")
        self.assertEqual(ticket.status, 'PENDING')
        self.assertEqual(ticket.title, "Test Ticket")
        self.assertEqual(str(ticket), "Test Ticket : Test Description -> PENDING")

class TicketViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_ticket_view_post(self):
        response = self.client.post(reverse('add_ticket'), {'title': 'New Ticket', 'description': 'Description'})
        self.assertEqual(response.status_code, 302)  # Assuming the view redirects after successful post
        self.assertTrue(Ticket.objects.filter(title='New Ticket').exists())


    def test_add_ticket_view_post_invalid_form(self):
        response = self.client.post(reverse('add_ticket'), {'title': '', 'description': 'Description'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(description='Description').exists())

class TicketAdminTestCase(TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create(title="Admin Test", description="Admin Description")
        self.admin_site = TicketAdmin(Ticket, admin.ModelAdmin)

    def test_solve_ticket_action(self):
        self.admin_site.solve_ticket(None, Ticket.objects.filter(id=self.ticket.id))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'SOLVED')

    def test_reject_ticket_action(self):
        self.admin_site.reject_ticket(None, Ticket.objects.filter(id=self.ticket.id))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'REJECTED')

class TestReportIncidence(StaticLiveServerTestCase):
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
  
  def test_reportIncidence(self):
    home = self.live_server_url + "/"
    self.driver.get(self.live_server_url)
    self.driver.set_window_size(1480, 808)
    self.driver.find_element(By.CSS_SELECTOR, ".button-ticket").click()

    self.assertTrue(self.driver.current_url == f'{self.live_server_url}/ticket/add-ticket/')

    self.driver.find_element(By.ID, "id_title").click()
    self.driver.find_element(By.ID, "id_title").send_keys("Ticket de prueba")
    self.driver.find_element(By.ID, "id_description").click()
    self.driver.find_element(By.ID, "id_description").send_keys("Esto es una prueba")
    self.driver.find_element(By.CSS_SELECTOR, ".filled-button:nth-child(2)").click()

    time.sleep(2)

    title = self.driver.find_element(By.ID, "id_title").text
    description = self.driver.find_element(By.ID, "id_description").text

    self.assertEqual(title, '')
    self.assertEqual(description, '')

    self.driver.find_element(By.ID, "return").click()

    time.sleep(2)

    self.assertEqual(self.driver.current_url, home)

  
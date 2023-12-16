from django.test import TestCase, Client
from django.urls import reverse
from .models import Ticket
from .admin import TicketAdmin
from django.contrib.admin.sites import AdminSite

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
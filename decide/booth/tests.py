from django.test import TestCase
from base.tests import BaseTestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from census.models import Census
from voting.models import Voting,Question
from django.utils import timezone
from datetime import datetime,timedelta

# Create your tests here.

class BoothTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
    def tearDown(self):
        super().tearDown()
    def testBoothNotFound(self):
        response = self.client.get('/booth/10000/')
        self.assertEqual(response.status_code, 404)
    
    def testBoothRedirection(self):
        response = self.client.get('/booth/10000')
        self.assertEqual(response.status_code, 301)

class ListActiveBoothTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.list_booth_url = reverse('listActiveVoting') 

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.list_booth_url)
        self.assertRedirects(response, '/users/login',status_code=302,target_status_code=301)

    def test_logged_in_no_census(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_booth_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booth/listBooth.html')
        self.assertEqual(len(response.context['booths']), 0)

    def test_logged_in_with_census_no_active_booth(self):
        q = Question(desc='test question1')
        q.save()
        voting = Voting.objects.create(id=1,name="vting1",desc="desc1",question=q,start_date=timezone.now(), end_date=timezone.now() - timedelta(days=1),
                                       method='IDENTITY',seats=10)
        Census.objects.create(voter_id=self.user.id, voting_id=voting.id)
        self.client.force_login(self.user)
        response = self.client.get(self.list_booth_url)
        self.assertEqual(len(response.context['booths']), 0)

    def test_logged_in_with_census_and_active_booth(self):
        q = Question(desc='test question2')
        q.save()
        voting = Voting.objects.create(id=2,name="vting2",desc="desc1",question=q,start_date=timezone.now(), end_date=None,
                                       method='IDENTITY',seats=10)
        Census.objects.create(voter_id=self.user.id, voting_id=voting.id)
        self.client.force_login(self.user)
        response = self.client.get(self.list_booth_url)
        self.assertEqual(len(response.context['booths']), 1)


       
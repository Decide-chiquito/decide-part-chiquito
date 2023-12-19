import datetime
import random

from base.tests import BaseTestCase
from census.models import Census
from django.contrib.auth.models import User
from django.utils import timezone
from voting.models import Question
from voting.models import Voting

from .models import Vote
from .serializers import VoteSerializer


class StoreTextCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.question = Question(desc='qwerty')
        self.question.save()
        self.voting = Voting(pk=5001,
                             name='voting example',
                             start_date=timezone.now(),
        )
        self.voting.save()
        self.voting.questions.add(self.question)
        self.voting.save()

    def tearDown(self):
        super().tearDown()

    def gen_voting(self, pk):
        voting = Voting(pk=pk, name='v1', start_date=timezone.now(), 
                        end_date=timezone.now() + datetime.timedelta(days=1))
        voting.save()
        voting.questions.add(self.question)
        voting.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def gen_votes(self):
        votings = [random.randint(1, 5000) for i in range(10)]
        users = [random.randint(3, 5002) for i in range(50)]

        for voting in votings:
            self.gen_voting(voting)
            random_user = random.choice(users)
            user = self.get_or_create_user(random_user)
            self.login(user=user.username)

            votes = []

            self.census = Census(voting_id=voting, voter_id=random_user)
            self.census.save()

            a = random.randint(2, 500)
            b = random.randint(2, 500)
            votes.append({"questionId": self.question.id, "vote": {"a": a, "b": b}})

            data = {
                "voting": voting,
                "voter": random_user,
                "votes": votes
            }

            response = self.client.post('/store/', data, format='json')
            self.assertEqual(response.status_code, 200)
            
        self.logout()
        return votings, users

    def test_gen_vote_invalid(self):
        data = {
            "voting": 1,
            "voter": 1,
            "votes": [{"questionId": 1, "vote": {"a": 1, "b": 1}}]
        }
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_store_vote(self):
        VOTING_PK = 345
        CTE_A = 96
        CTE_B = 184
        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()
        
        # Crear votación y asociar una pregunta
        voting = self.gen_voting(VOTING_PK)

        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "votes": [{"questionId": self.question.id, "vote": {"a": CTE_A, "b": CTE_B}}]
        }

        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().question_id, self.question.id)
        self.assertEqual(Vote.objects.first().a, CTE_A)
        self.assertEqual(Vote.objects.first().b, CTE_B)

    def test_vote(self):
        self.gen_votes()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.count())
        self.assertEqual(votes[0], VoteSerializer(Vote.objects.all().first()).data)

    def test_filter(self):
        votings, voters = self.gen_votes()
        v = votings[0]

        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voting_id=v).count())

        v = voters[0]
        response = self.client.get('/store/?voter_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voter_id=v).count())

    def test_hasvote(self):
        _, _ = self.gen_votes()

        vo = Vote.objects.first()
        v = vo.voting_id
        u = vo.voter_id

        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["voting_id"], v)
        self.assertEqual(votes[0]["voter_id"], u)
    
    def test_voting_status(self):
        VOTING_PK = 5001

        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "votes": [{"questionId": self.question.id, "vote": {"a": 30, "b": 55}}]
        }

        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()

        # not opened
        self.voting.start_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        user = self.get_or_create_user(1)

        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # not closed
        self.voting.start_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        self.voting.end_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        # closed
        self.voting.end_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_retrieve_vote(self):
        self.gen_votes()
        self.login()

        vote = Vote.objects.first()

        response = self.client.get('/store/{}/'.format(vote.pk), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["a"], vote.a)

    def test_update_votes(self):
        self.gen_votes()
        self.login()

        vote = Vote.objects.first()
        new_data = {
            "questionId": self.question.id,
            "vote": {
                "a": vote.a + 1,
                "b": vote.b + 1
            }
        }
        
        response = self.client.put('/store/{}/'.format(vote.pk), new_data, format='json')
        self.assertEqual(response.status_code, 204)

    def test_delete_vote(self):
        self.gen_votes()
        self.login()

        vote = Vote.objects.first()

        response = self.client.delete('/store/{}/'.format(vote.pk), format='json')
        self.assertEqual(response.status_code, 204)

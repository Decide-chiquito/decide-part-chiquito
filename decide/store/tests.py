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

    def tearDown(self):
        super().tearDown()

    def gen_voting(self, pk, question_desc=None):
        voting = Voting(pk=pk, name='v1', start_date=timezone.now(), end_date=timezone.now() + datetime.timedelta(days=1))
        voting.save()

        if question_desc:
            question = Question(desc=question_desc)
            question.save()
            voting.questions.add(question)

        return voting

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def gen_votes(self):
        votings = [self.gen_voting(pk=random.randint(1, 5000)) for _ in range(5)]
        users = [self.get_or_create_user(pk=random.randint(3, 5002)) for _ in range(50)]
        questions = [Question.objects.create(desc='Question desc {}'.format(i)) for i in range(2)]

        for voting in votings:
            voting.questions.add(*questions)

            random_user = random.choice(users)
            votes = []
            census = Census(voting_id=voting.id, voter_id=random_user.id)
            census.save()
            for question in questions:
                a = random.randint(2, 500)
                b = random.randint(2, 500)
                votes.append({"questionId": question.id, "vote": {"a": a, "b": b}})

            data = {
                "voting": voting.id,
                "voter": random_user.id,
                "votes": votes
            }

            self.login(user=random_user.username)
            response = self.client.post('/store/', data, format='json')
            self.assertEqual(response.status_code, 200)
            self.logout()

        return votings, users, questions
    
    

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
        QUESTION_DESC = 'Sample question description'
        CTE_A = 96
        CTE_B = 184
        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()
        
        # Crear votación y asociar una pregunta
        voting = self.gen_voting(VOTING_PK, question_desc=QUESTION_DESC)

        question = voting.questions.first()  # Obtener la primera pregunta asociada
        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "votes": [{"questionId": question.id, "vote": {"a": CTE_A, "b": CTE_B}}]
        }

        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().question_id, question.id)
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
        votings, voters, questions = self.gen_votes()
        v = votings[0]

        response = self.client.get('/store/?voting_id={}'.format(v.id), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}'.format(v.id), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}'.format(v.id), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voting_id=v.id).count())

        v = voters[0]
        response = self.client.get('/store/?voter_id={}'.format(v.id), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voter_id=v.id).count())

    def test_hasvote(self):
        votings, voters, questions = self.gen_votes()
        vo = Vote.objects.first()
        v = vo.voting_id
        u = vo.voter_id
        q = vo.question_id

        response = self.client.get('/store/?voting_id={}&voter_id={}&question_id={}'.format(v, u, q), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}&voter_id={}&question_id={}'.format(v, u, q), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}&voter_id={}&question_id={}'.format(v, u, q), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["voting_id"], v)
        self.assertEqual(votes[0]["voter_id"], u)
    
    def test_voting_status(self):
        VOTING_PK = 5001
        QUESTION_DESC = 'Sample question description'
        
        # Crear votación y asociar una pregunta
        self.voting = self.gen_voting(VOTING_PK, question_desc=QUESTION_DESC)
        question = self.voting.questions.first()

        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "votes": [{"questionId": question.id, "vote": {"a": 30, "b": 55}}]
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
            "a": vote.a +1,
            "b": vote.b +1
        }
        response = self.client.put('/store/{}/'.format(vote.pk), new_data, format='json')
        self.assertEqual(response.status_code, 204)

    def test_delete_vote(self):
        self.gen_votes()
        self.login()
        vote = Vote.objects.first()
        response = self.client.delete('/store/{}/'.format(vote.pk), format='json')
        self.assertEqual(response.status_code, 204)

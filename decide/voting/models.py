from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _ 

from base import mods
from base.models import Auth, Key


class Question(models.Model):
    desc = models.TextField()

    def __str__(self):
        return self.desc
    class Meta:
        verbose_name=_("Question")


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE,verbose_name=_("question"))
    number = models.PositiveIntegerField(blank=True, null=True,verbose_name=_("number"))
    option = models.TextField(verbose_name=_("option"))
    class Meta:
        verbose_name=_("QuestionOption")

    def save(self):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)
    


class Voting(models.Model):
    name = models.CharField(max_length=200,verbose_name=_("name"))
    desc = models.TextField(blank=True, null=True)

    questions = models.ManyToManyField(Question, related_name='voting',verbose_name=_("questions"))

    start_date = models.DateTimeField(blank=True, null=True,verbose_name=_("start_date"))
    end_date = models.DateTimeField(blank=True, null=True,verbose_name=_("end_date"))

    pub_key = models.OneToOneField(Key, related_name='voting', blank=True, null=True, on_delete=models.SET_NULL)
    auths = models.ManyToManyField(Auth, related_name='votings')

    tally = JSONField(blank=True, null=True,verbose_name=_("tally"))
    postproc = JSONField(blank=True, null=True)

    VOTE_TYPES = (
        ('IDENTITY','Identity'),
        ('DHONDT',"D'Hondt"),
        ('WEBSTER',"Webster"),
    )

    type = models.CharField(max_length=8,choices=VOTE_TYPES,default='IDENTITY',verbose_name=_("type"))

    seats = models.PositiveIntegerField(blank=True, null=True,verbose_name=_("seats"))
    
    class Meta:
        verbose_name=_("Voting")

    def create_pubkey(self):
        print("=== CREATE PUBKEY ===")
        if self.pub_key or not self.auths.count():
            return

        auth = self.auths.first()
        data = {
            "voting": self.id,
            "auths": [ {"name": a.name, "url": a.url} for a in self.auths.all() ],
        }
        key = mods.post('mixnet', baseurl=auth.url, json=data)
        pk = Key(p=key["p"], g=key["g"], y=key["y"])
        pk.save()
        self.pub_key = pk
        self.save()

    def get_votes(self, token=''):

        votes_by_question = {}

        for question in self.questions.all():

            question_votes = mods.get('store', params={'voting_id': self.id, 'question_id': question.id}, HTTP_AUTHORIZATION='Token ' + token)
            print("=== question_votes ===")
            print(question_votes)
            votes_format = []
            votes_list = []

            for vote in question_votes:
                for info in vote:
                    if info == "a":
                        votes_format.append(vote['a'])
                    elif info == "b":
                        votes_format.append(vote['b'])
                votes_list.append(votes_format)
                votes_format = []

            votes_by_question[question.id] = votes_list

        return votes_by_question

    def tally_votes(self, token=''):
        '''
        The tally is a shuffle and then a decrypt
        '''
        
        votes_by_question = self.get_votes(token)
        tally_results = {}

        shuffle_url = "/shuffle/{}/".format(self.id)
        decrypt_url = "/decrypt/{}/".format(self.id)

        for question_id, question_votes in votes_by_question.items():
            auth = self.auths.first()
            auths = [{"name": a.name, "url": a.url} for a in self.auths.all()]

            # Realizar la mezcla (shuffle) para los votos de esta pregunta
            shuffle_data = {"msgs": question_votes}

            shuffle_response = mods.post('mixnet', entry_point=shuffle_url, baseurl=auth.url, json=shuffle_data, response=True)

            if shuffle_response.status_code != 200:
                # TODO: manage error
                continue
            # Realizar la descifrado (decrypt) para los votos de esta pregunta
            decrypt_data = {"msgs": shuffle_response.json()}
            decrypt_response = mods.post('mixnet', entry_point=decrypt_url, baseurl=auth.url, json=decrypt_data, response=True)
            if decrypt_response.status_code != 200:
                # TODO: manage error
                continue
            # Guardar los resultados del tally para esta pregunta
            tally_results[question_id] = decrypt_response.json()
        self.tally = tally_results
        self.save()
        self.do_postproc()

    def do_postproc(self):
        print("=== POSTPROC ===")

        if isinstance(self.tally, dict):
            print("=== POSTPROC 1 ===")
            postproc_results = []
            print(self.tally.items())
            for question_id, question_tally in self.tally.items():
                print("=== POSTPROC 2 ===")
                print(question_id)
                print(question_tally)
                # Obtener las opciones para la pregunta actual
                question = Question.objects.get(id=question_id)
                options = question.options.all()
                opts = []
                print("=== POSTPROC 3 ===")
                for opt in options:
                    print("=== POSTPROC 4 ===")
                    # Contar los votos para cada opción según el tipo de votación
                    if self.type == 'IDENTITY':
                        votes = question_tally.count(opt.number)
                    elif self.type == 'DHONDT':
                        votes = question_tally.count(opt.number)
                    elif self.type == 'WEBSTER':
                        votes = question_tally.count(opt.number)
                    else:
                        votes = 0

                    opts.append({
                        'option': opt.option,
                        'number': opt.number,
                        'votes': votes
                    })
                print(opts)
                print("=== POSTPROC 5 ===")
                # Realizar el post-procesamiento para esta pregunta
                data = {'type': self.type, 'options': opts, 'seats': self.seats}
                postp = mods.post('postproc', json=data)

                postproc_results.append({
                    'question_id': question_id,
                    'postproc': postp
                })

            # Guardar los resultados del post-procesamiento para cada pregunta
            self.postproc = postproc_results
            self.save()

    def __str__(self):
        return self.name
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _ 

from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

from base import mods
from base.models import Auth, Key

from datetime import datetime


class Question(models.Model):
    desc = models.TextField()
    history = AuditlogHistoryField()

    VOTE_TYPE = (
        ('MULTIPLE','Multiple'),
        ('YESNO',"Yes/No"),
    )

    type = models.CharField(max_length=8,choices=VOTE_TYPE,default='MULTIPLE',verbose_name=_("type"))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.type == 'YESNO':
            # Eliminar todas las QuestionOptions asociadas
            self.options.all().delete()

            # Crear dos nuevas QuestionOptions
            optYes = QuestionOption(
                question_id=self.id,
                number=0,
                option='Yes',
            )
            optYes.save()

            optNo = QuestionOption(
                question_id=self.id,
                number=1,
                option='No',
            )
            optNo.save()
        if self.type == 'MULTIPLE':
            option = QuestionOption.objects.filter(number=2, option='No')
            option.delete()
            option = QuestionOption.objects.filter(number=3, option='Yes')
            option.delete()

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.desc
    class Meta:
        verbose_name=_("Question")


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE,verbose_name=_("question"))
    number = models.PositiveIntegerField(blank=True, null=True,verbose_name=_("number"))
    option = models.TextField(verbose_name=_("option"))
    history = AuditlogHistoryField()
    class Meta:
        verbose_name=_("QuestionOption")

    def save(self,*args,**kwargs):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super(QuestionOption,self).save(*args,**kwargs)

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
    history = AuditlogHistoryField()

    VOTE_METHODS = (
        ('IDENTITY','Identity'),
        ('DHONDT',"D'Hondt"),
        ('WEBSTER',"Webster"),
    )

    method = models.CharField(max_length=8,choices=VOTE_METHODS,default='IDENTITY',verbose_name=_("method"))

    seats = models.PositiveIntegerField(blank=True, null=True,verbose_name=_("seats"))

    single_vote = models.BooleanField(default=False,verbose_name=_("single_vote"))
    
    class Meta:
        verbose_name=_("Voting")

    def create_pubkey(self):
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
    
    def live_tally(self, token=''):
        votes_by_question = self.get_votes(token)
        tally_results = {}
        postproc_results = []

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
            
            question_tally = decrypt_response.json()
            tally_results[question_id] = question_tally

            question = Question.objects.get(id=question_id)
            options = question.options.all()
            opts = []

            for opt in options:
                # Contar los votos para cada opción según el tipo de votación
                if self.method == 'IDENTITY':
                    votes = question_tally.count(opt.number)
                elif self.method == 'DHONDT':
                    votes = question_tally.count(opt.number)
                elif self.method == 'WEBSTER':
                    votes = question_tally.count(opt.number)
                else:
                    votes = 0

                opts.append({
                    'option': opt.option,
                    'number': opt.number,
                    'votes': votes
                })

            # Realizar el post-procesamiento para esta pregunta
            data = {'method': self.method, 'options': opts, 'seats': self.seats}
            postp = mods.post('postproc', json=data)

            postproc_results.append({
                'question_id': question_id,
                'postproc': postp,
            })
        
        self.tally = tally_results
        self.postproc = postproc_results
        self.save()

        return postproc_results

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
        if isinstance(self.tally, dict):
            postproc_results = []

            for question_id, question_tally in self.tally.items():

                # Obtener las opciones para la pregunta actual
                question = Question.objects.get(id=question_id)
                options = question.options.all()
                opts = []

                for opt in options:
                    # Contar los votos para cada opción según el tipo de votación
                    if self.method == 'IDENTITY':
                        votes = question_tally.count(opt.number)
                    elif self.method == 'DHONDT':
                        votes = question_tally.count(opt.number)
                    elif self.method == 'WEBSTER':
                        votes = question_tally.count(opt.number)
                    else:
                        votes = 0

                    opts.append({
                        'option': opt.option,
                        'number': opt.number,
                        'votes': votes
                    })

                # Realizar el post-procesamiento para esta pregunta
                data = {'method': self.method, 'options': opts, 'seats': self.seats}
                postp = mods.post('postproc', json=data)

                postproc_results.append({
                    'question_id': question_id,
                    'postproc': postp,
                })

            # Guardar los resultados del post-procesamiento para cada pregunta
            self.postproc = postproc_results
            self.save()

    def __str__(self):
        return self.name


auditlog.register(Question, serialize_data=True,)
auditlog.register(QuestionOption, serialize_data=True,)
auditlog.register(Voting, serialize_data=True,)
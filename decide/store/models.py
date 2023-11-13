from django.db import models
from base.models import BigBigField
from auditlog.registry import auditlog


class Vote(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    a = BigBigField()
    b = BigBigField()

    voted = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.voting_id, self.voter_id)

auditlog.register(Vote, serialize_data=True,)


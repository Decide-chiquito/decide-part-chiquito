from django.db import models
from base.models import BigBigField

from django.utils.translation import gettext_lazy as _

class Vote(models.Model):
    voting_id = models.PositiveIntegerField(verbose_name=_("voting_id"))
    voter_id = models.PositiveIntegerField(verbose_name=_("voter_id"))
    question_id = models.PositiveIntegerField(verbose_name=_("question_id"))

    a = BigBigField()
    b = BigBigField()

    voted = models.DateTimeField(auto_now=True,verbose_name=_("voted"))

    class Meta:
        verbose_name=_("Vote")
        
    def __str__(self):
        return '{}: {}'.format(self.voting_id, self.voter_id)

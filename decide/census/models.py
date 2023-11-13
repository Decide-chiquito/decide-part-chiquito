from django.db import models
from django.utils.translation import gettext_lazy as _

class Census(models.Model):
    voting_id = models.PositiveIntegerField(verbose_name=_("voting_id"))
    voter_id = models.PositiveIntegerField(verbose_name=_("voter_id"))
    adscription_center = models.CharField(max_length=200, default="")

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)
        verbose_name=_("Census")

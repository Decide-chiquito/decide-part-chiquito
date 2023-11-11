from django.db import models


class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()
    adscription_center = models.CharField(max_length=200, default="")

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

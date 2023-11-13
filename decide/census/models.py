from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=128, unique=True, blank=False)

    def __str__(self) -> str:
        return self.name

class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()
    adscription_center = models.CharField(max_length=200, default="")
    tags = models.ManyToManyField(Tag, related_name='census')

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

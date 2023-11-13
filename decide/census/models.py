from django.db import models
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField


class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()
    adscription_center = models.CharField(max_length=200, default="")
    history = AuditlogHistoryField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

auditlog.register(Census, serialize_data=True,)

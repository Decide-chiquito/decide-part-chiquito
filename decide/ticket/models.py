from django.db import models
from decide.ticket.enums import TicketStatus

from decide.voting.models import Voting


class Ticket(models.Model):
    title = models.CharField(max_length=64, blank=False, null=False)
    description = models.CharField(max_length=1024, blank=False, null=False)
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, blank=False, null=False)
    status = models.CharField(max_length=16, choices=TicketStatus.choices(), default=TicketStatus.PENDING, blank=False, null=False)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        indexes = [
            models.Index(fields=['voting'])
        ]

    def __str__(self):
        return f"{self.voting.name} : {self.title}"
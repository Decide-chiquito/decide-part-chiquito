from django.db import models
from ticket.enums import TicketStatus



class Ticket(models.Model):
    title = models.CharField(max_length=64, blank=False, null=False)
    description = models.CharField(max_length=1024, blank=False, null=False)
    status = models.CharField(max_length=16, choices=TicketStatus.choices(), default=TicketStatus.PENDING, blank=False, null=False)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        indexes = [
        ]

    def __str__(self):
        return f"{self.title} : {self.description} -> {self.status}"
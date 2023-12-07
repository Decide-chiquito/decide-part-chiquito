from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from voting.models import Voting

class Tag(models.Model):
    name = models.CharField(max_length=128, unique=True, blank=False)

    def __str__(self) -> str:
        return self.name

class Census(models.Model):
    voting_id = models.PositiveIntegerField(verbose_name=_("voting_id"))
    voter_id = models.PositiveIntegerField(verbose_name=_("voter_id"))
    adscription_center = models.CharField(max_length=200, default="")
    tags = models.ManyToManyField(Tag, related_name='census')

    def save(self, *args, **kwargs):
        is_new = not self.pk  # Verifica si es una instancia nueva
        super().save(*args, **kwargs)  # Guarda la instancia de Census

        if is_new:
            voter_id = self.voter_id
            voting_id = self.voting_id
            try:
                subject = 'Nueva Votación Disponible'
                voter = User.objects.get(pk=voter_id)
                mailTo = voter.email
                
                voting = Voting.objects.get(pk=voting_id)
                
                message = f"Ha sido añadido a un nuevo censo para la votación {voting.name}. Podrá votar por la votación con id: {voting_id} cuando se abra la votación"

                email = EmailMessage(subject, message, to=[mailTo])
                reponse = email.send()
            except User.DoesNotExist:
                pass
            except Voting.DoesNotExist:
                message = f"Ha sido añadido a un nuevo censo. Podrá votar por la votación con id: {voting_id} cuando se abra la votación"
                email = EmailMessage(subject, message, to=[mailTo])
                reponse = email.send()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)
        verbose_name=_("Census")

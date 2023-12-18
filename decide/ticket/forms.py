from django import forms

from ticket.models import Ticket


class TicketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Ticket
        fields = ['title', 'description']

        widgets={
            'title': forms.Textarea(attrs={'class': 'form-control custom-title-input', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'required': True}),
        }

        labels={
            'title': 'Title',
            'description': 'Description'
        }
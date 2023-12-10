from django.shortcuts import render, redirect
from decide.ticket.forms import TicketForm
from decide.voting.models import Voting


def add_ticket(request, votation_id):
    voting = Voting.objects.get(pk=votation_id)

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.voting = voting
            ticket.save()

            return redirect(request.META.get('HTTP_REFERER', ''))
    else:
        form = TicketForm()

    return render(request, 'add_ticket.html', {'form': form, 'voting': voting})
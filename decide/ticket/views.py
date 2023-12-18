from django.shortcuts import render, redirect
from ticket.forms import TicketForm


def add_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.save()

            return redirect('add_ticket')
    else:
        form = TicketForm()

    return render(request, 'add-ticket.html', {'form': form})
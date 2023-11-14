from django.shortcuts import render
from django.urls import get_resolver

from voting.models import Voting
# Create your views here.


def welcome(request):
    url_patterns = get_resolver(None).url_patterns
    context = {'url_patterns': {str(i.pattern) for i in url_patterns if str(i.pattern) != ''}}
    voting_enabled = Voting.objects.filter(start_date__isnull=False).filter( end_date=None)
    voting_finished = Voting.objects.filter(start_date__isnull=False).filter( end_date__isnull=False)
    context['voting_enabled'] = voting_enabled
    context['voting_finished'] = voting_finished

    return render(request, 'initial.html', context)
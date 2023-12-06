from django.shortcuts import render
from django.urls import get_resolver, reverse
from voting.models import Voting


def welcome(request):
    url_patterns = get_resolver(None).url_patterns
    context = {'url_patterns': {str(i.pattern) for i in url_patterns if str(i.pattern) != ''}}
    voting_enabled = Voting.objects.filter(start_date__isnull=False).filter( end_date=None)
    voting_finished = Voting.objects.filter(start_date__isnull=False).filter( end_date__isnull=False)
    is_mobile = request.user_agent.is_mobile
    is_welcome_page = request.path == '/' or request.path == ''
    context['voting_enabled'] = voting_enabled
    context['voting_finished'] = voting_finished
    context['is_mobile'] = is_mobile
    context['is_welcome_page'] = is_welcome_page
    

    if (request.user_agent.is_mobile):
        return render(request, 'initial_mobile.html', context)
    else:
        return render(request, 'initial.html', context)
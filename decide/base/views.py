from django.shortcuts import render
from django.urls import get_resolver

# Create your views here.


def welcome(request):
    url_patterns = get_resolver(None).url_patterns
    print("res:",url_patterns[1].pattern,"fin")
    context = {'url_patterns': url_patterns}
    return render(request, 'initial.html', context)
from django.urls import path
from . import views


urlpatterns = [

    path('add-ticket/', views.add_ticket, name='add_ticket'),
    
]
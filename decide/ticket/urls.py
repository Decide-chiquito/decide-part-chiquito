from django.urls import path
from . import views


urlpatterns = [

    path('add_ticket/<int:voting_id>/', views.add_ticket, name='add_ticket'),
    
]
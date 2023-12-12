from django.urls import path
from .views import BoothView
from . import views

urlpatterns = [
    path('<int:voting_id>/', BoothView.as_view()),
    path('listActiveVoting/',views.listActiveBooth ,name='listActiveVoting')

]

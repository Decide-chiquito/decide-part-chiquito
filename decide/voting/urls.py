from django.urls import path
from . import views


urlpatterns = [
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingAction.as_view(), name='voting'),
    path('<int:voting_id>/staff/', views.VotingStaff.as_view(), name='voting_staff'),
]

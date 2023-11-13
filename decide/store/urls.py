from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.StoreView.as_view(), name='store'),
    path('<int:vote_id>/', views.StoreDetail.as_view(), name='store_detail'),
]

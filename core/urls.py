from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),  # Add this line
    path('create-profile/', views.create_profile, name='create_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
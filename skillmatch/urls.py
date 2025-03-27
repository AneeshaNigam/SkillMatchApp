from django.urls import path
from core import views 

urlpatterns = [
    path('', views.home, name='home'),  # This ensures '/' points to home
    path('home/', views.home, name='home'),  # This makes '/home/' accessible
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('create-profile/', views.create_profile, name='create_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login-redirect/', views.login_redirect, name='login_redirect'),
]

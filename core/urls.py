from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/home/')),  # Redirect root URL to home
    path('', include('core.urls')),  # Include core.urls only once
]

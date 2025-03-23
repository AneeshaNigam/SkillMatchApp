from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/create-profile/')),  # Redirect root URL to create-profile
    path('', include('core.urls')),  # Include core.urls only once
]
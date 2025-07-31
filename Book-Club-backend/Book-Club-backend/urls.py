from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from myapp.jwt_views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('myapp.urls')),  # API endpoints
    # JWT Authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Add favicon route to prevent 404
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    # Home page (keep this last to avoid conflicts)
    path('', include('myapp.urls')),  # Home and legacy routes
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

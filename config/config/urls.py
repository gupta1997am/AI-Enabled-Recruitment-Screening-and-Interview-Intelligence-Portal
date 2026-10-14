from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Recruitment website
    path('', include('recruitment.urls')),

    # Django authentication
    path('accounts/', include('django.contrib.auth.urls')),

    # Recruitment APIs
    path('api/', include('recruitment.api_urls')),

    # OpenAPI schema
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema',
    ),

    # Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    # ReDoc UI
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]
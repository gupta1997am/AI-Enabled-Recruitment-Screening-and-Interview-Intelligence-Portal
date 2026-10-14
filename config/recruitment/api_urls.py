from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import api_views

app_name = "recruitment_api"

urlpatterns = [
    # JWT authentication
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Candidate APIs
    path(
        "candidates/",
        api_views.CandidateListCreateAPIView.as_view(),
        name="candidate_list_create",
    ),
    path(
        "candidates/<int:pk>/",
        api_views.CandidateDetailAPIView.as_view(),
        name="candidate_detail",
    ),

    # Job role APIs
    path(
        "roles/",
        api_views.JobRoleListCreateAPIView.as_view(),
        name="role_list_create",
    ),
    path(
        "roles/<int:pk>/",
        api_views.JobRoleDetailAPIView.as_view(),
        name="role_detail",
    ),

    # Screening results API
    path(
        "screening/",
        api_views.ScreeningResultListAPIView.as_view(),
        name="screening_results",
    ),
]
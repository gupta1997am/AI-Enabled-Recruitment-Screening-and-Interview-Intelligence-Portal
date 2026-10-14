from django.urls import path

from . import views
from . import views_cbv

app_name = "recruitment"

urlpatterns = [
    # Existing function-based views
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_candidates, name="upload_candidates"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),

    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/add/", views.candidate_create, name="candidate_create"),
    path("candidates/<int:pk>/", views.candidate_detail, name="candidate_detail"),
    path("candidates/<int:pk>/edit/", views.candidate_update, name="candidate_update"),
    path("candidates/<int:pk>/delete/", views.candidate_delete, name="candidate_delete"),

    path("screening/", views.screening_results, name="screening_results"),
    path("interviews/", views.interview_list, name="interview_list"),
    path(
        "interviews/slots/add/",
        views.interview_slot_create,
        name="interview_slot_create",
    ),
    path(
        "interviews/feedback/add/",
        views.interview_feedback_create,
        name="interview_feedback_create",
    ),

    # Class-based views (CBVs)
    path(
        "cbv/candidates/",
        views_cbv.CandidateListCBV.as_view(),
        name="candidate_list_cbv",
    ),
    path(
        "cbv/candidates/add/",
        views_cbv.CandidateCreateCBV.as_view(),
        name="candidate_create_cbv",
    ),
    path(
        "cbv/candidates/<int:pk>/",
        views_cbv.CandidateDetailCBV.as_view(),
        name="candidate_detail_cbv",
    ),
    path(
        "cbv/candidates/<int:pk>/edit/",
        views_cbv.CandidateUpdateCBV.as_view(),
        name="candidate_update_cbv",
    ),
    path(
        "cbv/candidates/<int:pk>/delete/",
        views_cbv.CandidateDeleteCBV.as_view(),
        name="candidate_delete_cbv",
    ),
]
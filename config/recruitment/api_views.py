from rest_framework import generics, permissions, filters
from rest_framework.exceptions import PermissionDenied
from .permissions import IsAdminOrReadOnly

from .models import Candidate, JobRole, ScreeningResult
from .serializers import (
    CandidateSerializer,
    JobRoleSerializer,
    ScreeningResultSerializer,
)


class CandidateListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List candidates.
    POST: Create a candidate.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "candidate_name",
        "email",
        "college",
        "applied_role",
    ]
    ordering_fields = [
        "candidate_name",
        "created_at",
        "experience_months",
        "expected_salary",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Candidate.objects.all()


class CandidateDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a candidate.
    PUT/PATCH: Update a candidate.
    DELETE: Delete a candidate.
    """
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAdminOrReadOnly]


class JobRoleListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List job roles.
    POST: Create a job role.
    """
    queryset = JobRole.objects.all()
    serializer_class = JobRoleSerializer
    permission_classes = [IsAdminOrReadOnly]


class JobRoleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a job role.
    PUT/PATCH: Update a job role.
    DELETE: Delete a job role.
    """
    queryset = JobRole.objects.all()
    serializer_class = JobRoleSerializer
    permission_classes = [IsAdminOrReadOnly]


class ScreeningResultListAPIView(generics.ListAPIView):
    """
    GET: List screening results.
    """
    serializer_class = ScreeningResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "candidate__candidate_name",
        "candidate__email",
        "role__title",
    ]
    ordering_fields = ["rule_score", "ml_score", "resume_score", "screened_at"]
    ordering = ["-screened_at"]

    def get_queryset(self):
        return ScreeningResult.objects.select_related(
            "candidate",
            "role",
            "batch",
        )


class MyCandidateListAPIView(generics.ListAPIView):
    """
    Lists candidates whose records were created by the current user.

    Candidate currently has no owner field, so this endpoint is intentionally
    unavailable until ownership is implemented.
    """
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(Candidate, "created_by"):
            raise PermissionDenied(
                "Candidate ownership is not configured yet."
            )

        return Candidate.objects.filter(created_by=self.request.user)
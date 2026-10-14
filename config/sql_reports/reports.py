# recruitment/sql_reports/reports.py

from django.db.models import Avg, Count

from recruitment.models import (
    Candidate,
    JobRole,
    ScreeningResult,
    InterviewFeedback,
)


def get_dashboard_report():
    """Return key recruitment dashboard totals."""
    return {
        "total_candidates": Candidate.objects.count(),
        "total_roles": JobRole.objects.count(),
        "active_roles": JobRole.objects.filter(is_active=True).count(),
        "total_screening_results": ScreeningResult.objects.count(),
        "total_interview_feedback": InterviewFeedback.objects.count(),
    }


def get_candidate_status_report():
    """Count candidates by historical selection status."""
    return list(
        Candidate.objects.values(
            "historical_selection_status"
        ).annotate(
            total=Count("id")
        ).order_by("historical_selection_status")
    )


def get_role_candidate_report():
    """Count candidates grouped by their applied role."""
    return list(
        Candidate.objects.values(
            "applied_role"
        ).annotate(
            total_candidates=Count("id")
        ).order_by("-total_candidates", "applied_role")
    )


def get_screening_status_report():
    """Count screening results grouped by status."""
    return list(
        ScreeningResult.objects.values(
            "status"
        ).annotate(
            total=Count("id")
        ).order_by("status")
    )


def get_role_screening_report():
    """Show screening totals for each job role."""
    return list(
        ScreeningResult.objects.values(
            "role__title",
            "status",
        ).annotate(
            total=Count("id"),
            average_combined_score=Avg("rule_score"),
        ).order_by("role__title", "status")
    )
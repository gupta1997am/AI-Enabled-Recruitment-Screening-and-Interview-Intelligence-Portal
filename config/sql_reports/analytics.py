# recruitment/sql_reports/analytics.py

from recruitment.models import Candidate, ScreeningResult, InterviewFeedback


def get_candidate_selection_analytics():
    """Calculate historical candidate selection and rejection rates."""
    total = Candidate.objects.count()

    selected = Candidate.objects.filter(
        historical_selection_status="SELECTED"
    ).count()

    rejected = Candidate.objects.filter(
        historical_selection_status="REJECTED"
    ).count()

    waitlisted = Candidate.objects.filter(
        historical_selection_status="WAITLISTED"
    ).count()

    def percentage(value):
        return round((value / total) * 100, 2) if total else 0.0

    return {
        "total_candidates": total,
        "selected": selected,
        "rejected": rejected,
        "waitlisted": waitlisted,
        "selected_percentage": percentage(selected),
        "rejected_percentage": percentage(rejected),
        "waitlisted_percentage": percentage(waitlisted),
    }


def get_screening_analytics():
    """Calculate screening-result totals and status percentages."""
    total = ScreeningResult.objects.count()

    shortlisted = ScreeningResult.objects.filter(
        status="SHORTLISTED"
    ).count()

    selected = ScreeningResult.objects.filter(
        status="SELECTED"
    ).count()

    rejected = ScreeningResult.objects.filter(
        status="REJECTED"
    ).count()

    waitlisted = ScreeningResult.objects.filter(
        status="WAITLISTED"
    ).count()

    def percentage(value):
        return round((value / total) * 100, 2) if total else 0.0

    return {
        "total_screening_results": total,
        "shortlisted": shortlisted,
        "selected": selected,
        "rejected": rejected,
        "waitlisted": waitlisted,
        "shortlisted_percentage": percentage(shortlisted),
        "selected_percentage": percentage(selected),
        "rejected_percentage": percentage(rejected),
        "waitlisted_percentage": percentage(waitlisted),
    }


def get_interview_feedback_analytics():
    """Calculate interview feedback count and average rating."""
    feedback = InterviewFeedback.objects.all()

    from django.db.models import Avg, Count

    summary = feedback.aggregate(
        average_rating=Avg("rating"),
        total=Count("id"),
    )

    return {
        "total_feedback": summary["total"] or 0,
        "average_rating": (
            round(summary["average_rating"], 2)
            if summary["average_rating"] is not None
            else 0.0
        ),
        "strong_hire": feedback.filter(
            recommendation="STRONG_HIRE"
        ).count(),
        "hire": feedback.filter(
            recommendation="HIRE"
        ).count(),
        "hold": feedback.filter(
            recommendation="HOLD"
        ).count(),
        "reject": feedback.filter(
            recommendation="REJECT"
        ).count(),
    }
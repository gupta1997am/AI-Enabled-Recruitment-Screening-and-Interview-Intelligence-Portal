import re
from decimal import Decimal, InvalidOperation

import pandas as pd

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Avg
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    CandidateForm,
    CandidateUploadForm,
    InterviewFeedbackForm,
    InterviewSlotForm,
)
from .models import (
    ApplicationBatch,
    Candidate,
    InterviewFeedback,
    InterviewSlot,
    JobRole,
    ScreeningResult,
)


# --------------------------------------------------
# Helper functions for CSV / Excel ingestion
# --------------------------------------------------

def normalize_column_name(name):
    """Convert a column name to a consistent format."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def get_row_value(row, *possible_names, default=None):
    """Read a value using any recognized column name."""
    for name in possible_names:
        if name in row.index:
            value = row[name]
            if pd.notna(value) and str(value).strip():
                return value
    return default


def parse_skills(value):
    """Convert skills supplied as text into a list of strings."""
    if value is None or pd.isna(value):
        return []

    if isinstance(value, list):
        return [str(skill).strip() for skill in value if str(skill).strip()]

    text = str(value).strip()
    if not text:
        return []

    # Accept JSON-like lists as well as comma/semicolon-separated text.
    text = text.strip("[]")
    return [
        skill.strip().strip("'\"")
        for skill in re.split(r"[,;|]", text)
        if skill.strip().strip("'\"")
    ]


def parse_nonnegative_int(value, default=0):
    """Convert a spreadsheet value to a non-negative integer."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return default

    try:
        number = int(float(value))
        return max(number, 0)
    except (TypeError, ValueError, OverflowError):
        return default


def parse_salary(value):
    """Convert salary to Decimal, or None when not supplied."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None

    try:
        cleaned = re.sub(r"[₹$,\s]", "", str(value))
        amount = Decimal(cleaned)
        return amount if amount >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def parse_historical_status(value):
    """Map common spreadsheet status labels to model choices."""
    if value is None or pd.isna(value):
        return "UNKNOWN"

    normalized = str(value).strip().upper().replace(" ", "_").replace("-", "_")

    aliases = {
        "SELECTED": "SELECTED",
        "SHORTLISTED": "SELECTED",
        "ACCEPTED": "SELECTED",
        "REJECTED": "REJECTED",
        "NOT_SELECTED": "REJECTED",
        "WAITLISTED": "WAITLISTED",
        "WAITLIST": "WAITLISTED",
        "UNKNOWN": "UNKNOWN",
        "PENDING": "UNKNOWN",
    }
    return aliases.get(normalized, "UNKNOWN")


def process_application_batch(batch):
    """
    Read a batch file and import valid candidate records.

    Recognized column names include:
    candidate_name/name, email, phone, college, applied_role/role,
    skills, experience_months/experience, notice_period_days,
    expected_salary, resume_text, portfolio_url, and selection_status.
    """
    batch.status = "PROCESSING"
    batch.error_message = ""
    batch.save(update_fields=["status", "error_message"])

    processed = 0
    accepted = 0
    rejected = 0
    errors = []

    try:
        file_path = batch.file.path
        filename = batch.original_filename.lower()

        if filename.endswith(".csv"):
            dataframe = pd.read_csv(file_path)
        elif filename.endswith((".xlsx", ".xls")):
            dataframe = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Upload a CSV or Excel file.")

        dataframe.columns = [
            normalize_column_name(column) for column in dataframe.columns
        ]

        if dataframe.empty:
            raise ValueError("The uploaded file contains no candidate rows.")

        for row_number, row in dataframe.iterrows():
            processed += 1

            try:
                name = get_row_value(
                    row, "candidate_name", "name", "full_name"
                )
                email = get_row_value(row, "email", "email_address")
                phone = get_row_value(row, "phone", "phone_number", "mobile")
                role = get_row_value(row, "applied_role", "role", "job_role")

                if not name or not email:
                    raise ValueError("Candidate name and email are required.")

                name = " ".join(str(name).split())
                email = str(email).strip().lower()

                if "@" not in email:
                    raise ValueError("Invalid email address.")

                # Avoid importing duplicate email addresses.
                if Candidate.objects.filter(email__iexact=email).exists():
                    raise ValueError(f"Candidate email already exists: {email}")

                salary_value = get_row_value(
                    row, "expected_salary", "salary", default=None
                )

                candidate = Candidate(
                    candidate_name=name,
                    email=email,
                    phone=str(phone).strip() if phone is not None else "",
                    college=str(
                        get_row_value(row, "college", "college_name", default="")
                    ).strip(),
                    applied_role=str(role).strip() if role is not None else "",
                    skills=parse_skills(
                        get_row_value(row, "skills", "technical_skills", default="")
                    ),
                    experience_months=parse_nonnegative_int(
                        get_row_value(
                            row, "experience_months", "experience", default=0
                        )
                    ),
                    notice_period_days=parse_nonnegative_int(
                        get_row_value(row, "notice_period_days", "notice_period", default=0)
                    ),
                    expected_salary=parse_salary(salary_value),
                    resume_text=str(
                        get_row_value(row, "resume_text", "resume", default="")
                    ),
                    portfolio_url=str(
                        get_row_value(
                            row, "portfolio_url", "portfolio", default=""
                        )
                    ).strip(),
                    historical_selection_status=parse_historical_status(
                        get_row_value(
                            row, "selection_status", "historical_selection_status",
                            "status", default="UNKNOWN"
                        )
                    ),
                    batch=batch,
                    is_valid=True,
                )

                # Validate model fields before saving.
                candidate.full_clean()
                candidate.save()
                accepted += 1

            except Exception as exc:
                rejected += 1
                errors.append(f"Row {row_number + 2}: {str(exc)}")

        batch.total_records = processed
        batch.processed_records = processed
        batch.accepted_records = accepted
        batch.rejected_records = rejected
        batch.status = "COMPLETED"
        batch.error_message = "\n".join(errors[:50])
        batch.save()

        return True

    except Exception as exc:
        batch.total_records = processed
        batch.processed_records = processed
        batch.accepted_records = accepted
        batch.rejected_records = rejected
        batch.status = "FAILED"
        batch.error_message = str(exc)
        batch.save()
        return False


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@login_required
def dashboard(request):
    context = {
        "total_candidates": Candidate.objects.count(),
        "valid_candidates": Candidate.objects.filter(is_valid=True).count(),
        "total_roles": JobRole.objects.count(),
        "active_roles": JobRole.objects.filter(is_active=True).count(),
        "total_batches": ApplicationBatch.objects.count(),
        "total_screenings": ScreeningResult.objects.count(),
        "shortlisted_candidates": ScreeningResult.objects.filter(
            status="SHORTLISTED"
        ).count(),
        "upcoming_interviews": InterviewSlot.objects.filter(
            is_booked=False
        ).count(),
        "recent_candidates": Candidate.objects.order_by("-created_at")[:5],
        "recent_batches": ApplicationBatch.objects.order_by("-created_at")[:5],
    }
    return render(request, "recruitment/dashboard.html", context)


# --------------------------------------------------
# Candidate upload and ingestion
# --------------------------------------------------

@login_required
def upload_candidates(request):
    if request.method == "POST":
        form = CandidateUploadForm(request.POST, request.FILES)

        if form.is_valid():
            batch = form.save(commit=False)
            batch.uploader = request.user
            batch.status = "PENDING"
            batch.save()

            if process_application_batch(batch):
                messages.success(
                    request,
                    f"Import completed: {batch.accepted_records} candidates imported; "
                    f"{batch.rejected_records} rows rejected."
                )
            else:
                messages.error(
                    request,
                    f"Import failed: {batch.error_message}"
                )

            return redirect("recruitment:batch_detail", pk=batch.pk)
    else:
        form = CandidateUploadForm()

    return render(
        request,
        "recruitment/upload.html",
        {"form": form},
    )


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(ApplicationBatch, pk=pk)

    candidates = Candidate.objects.filter(batch=batch).order_by(
        "-created_at"
    )

    return render(
        request,
        "recruitment/batch_detail.html",
        {
            "batch": batch,
            "candidates": candidates,
        },
    )


# --------------------------------------------------
# Candidate list, details, create, update, delete
# --------------------------------------------------

@login_required
def candidate_list(request):
    candidates = Candidate.objects.all().order_by("-created_at")

    search = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        candidates = candidates.filter(
            Q(candidate_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(college__icontains=search)
            | Q(applied_role__icontains=search)
        )

    if role:
        candidates = candidates.filter(applied_role__icontains=role)

    if status:
        candidates = candidates.filter(
            historical_selection_status=status
        )

    context = {
        "candidates": candidates,
        "search_query": search,
        "selected_role": role,
        "selected_status": status,
        "roles": JobRole.objects.filter(is_active=True),
    }
    return render(request, "recruitment/candidate_list.html", context)



@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(
        Candidate,
        pk=pk,
    )

    screening_results = ScreeningResult.objects.filter(
        candidate=candidate
    ).select_related(
        "role", "batch"
    ).order_by("-screened_at")

    feedback = InterviewFeedback.objects.filter(
        candidate=candidate
    ).select_related(
        "slot", "interviewer"
    ).order_by("-created_at")

    return render(
        request,
        "recruitment/candidate_detail.html",
        {
            "candidate": candidate,
            "screening_results": screening_results,
            "feedback": feedback,
        },
    )


@login_required
def candidate_create(request):
    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Candidate created successfully.")
                return redirect("recruitment:candidate_list")
            except (IntegrityError, ValidationError):
                messages.error(
                    request,
                    "Candidate could not be saved. Check the details and try again."
                )
    else:
        form = CandidateForm()

    return render(
        request,
        "recruitment/candidate_form.html",
        {"form": form, "page_title": "Add Candidate"},
    )


@login_required
def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)

    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES, instance=candidate)

        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Candidate updated successfully.")
                return redirect("recruitment:candidate_detail", pk=candidate.pk)
            except (IntegrityError, ValidationError):
                messages.error(
                    request,
                    "Candidate could not be updated. Check the details and try again."
                )
    else:
        form = CandidateForm(instance=candidate)

    return render(
        request,
        "recruitment/candidate_form.html",
        {"form": form, "page_title": "Edit Candidate"},
    )


@login_required
@require_POST
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.delete()
    messages.success(request, "Candidate deleted successfully.")
    return redirect("recruitment:candidate_list")


# --------------------------------------------------
# Screening results
# --------------------------------------------------

@login_required
def screening_results(request):
    results = ScreeningResult.objects.select_related(
        "candidate", "role", "batch"
    ).order_by("-screened_at")

    status = request.GET.get("status", "").strip()
    role_id = request.GET.get("role", "").strip()
    search = request.GET.get("q", "").strip()

    if status:
        results = results.filter(status=status)

    if role_id:
        results = results.filter(role_id=role_id)

    if search:
        results = results.filter(
            Q(candidate__candidate_name__icontains=search)
            | Q(candidate__email__icontains=search)
            | Q(role__title__icontains=search)
        )

    return render(
        request,
        "recruitment/screening_results.html",
        {
            "results": results,
            "roles": JobRole.objects.filter(is_active=True),
            "selected_status": status,
            "selected_role": role_id,
            "search_query": search,
            "status_choices": ScreeningResult._meta.get_field("status").choices,
        },
    )


# --------------------------------------------------
# Interview slots and feedback
# --------------------------------------------------

@login_required
def interview_list(request):
    slots = InterviewSlot.objects.select_related(
        "role", "interviewer"
    ).order_by("start_time")

    return render(
        request,
        "recruitment/interviews.html",
        {"slots": slots},
    )


@login_required
def interview_slot_create(request):
    if request.method == "POST":
        form = InterviewSlotForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Interview slot created successfully.")
            return redirect("recruitment:interview_list")
    else:
        form = InterviewSlotForm()

    return render(
        request,
        "recruitment/interview_slot_form.html",
        {"form": form, "page_title": "Create Interview Slot"},
    )


@login_required
def interview_feedback_create(request):
    if request.method == "POST":
        form = InterviewFeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)

            # Use the logged-in user as the feedback author.
            feedback.interviewer = request.user
            feedback.save()

            messages.success(request, "Interview feedback saved successfully.")
            return redirect(
                "recruitment:candidate_detail",
                pk=feedback.candidate.pk,
            )
    else:
        form = InterviewFeedbackForm()

    return render(
        request,
        "recruitment/interview_feedback_form.html",
        {"form": form, "page_title": "Add Interview Feedback"},
    )
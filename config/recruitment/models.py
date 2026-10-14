from django.conf import settings
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    URLValidator,
)
from django.db import models
from django.utils import timezone


# ============================================================
# 1. JOB ROLE MODEL
# ============================================================

class JobRole(models.Model):
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    minimum_experience = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


# ============================================================
# 2. APPLICATION BATCH MODEL
# ============================================================

class ApplicationBatch(models.Model):

    class BatchStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_batches",
    )

    file = models.FileField(
        upload_to="candidate_uploads/",
        blank=True,
        null=True,
    )

    original_filename = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=BatchStatus.choices,
        default=BatchStatus.PENDING,
    )

    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def progress_percentage(self):
        if self.total_rows == 0:
            return 0

        return min(
            100,
            int((self.processed_rows / self.total_rows) * 100),
        )

    def __str__(self):
        return f"Batch #{self.pk} - {self.status}"


# ============================================================
# 3. CANDIDATE MODEL
# ============================================================

class Candidate(models.Model):

    class HistoricalStatus(models.TextChoices):
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"
        WAITLISTED = "WAITLISTED", "Waitlisted"
        UNKNOWN = "UNKNOWN", "Unknown"

    candidate_name = models.CharField(max_length=150)

    email = models.EmailField(max_length=254, db_index=True)

    phone = models.CharField(max_length=25)

    college = models.CharField(max_length=200, db_index=True)

    # The role text is retained from the source file.
    applied_role = models.CharField(max_length=150, db_index=True)

    # Normalized list of skills, for example ["python", "django"].
    skills = models.JSONField(default=list, blank=True)

    experience_months = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    notice_period_days = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    expected_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    resume_text = models.TextField(blank=True)

    portfolio_url = models.URLField(blank=True)

    historical_selection_status = models.CharField(
        max_length=20,
        choices=HistoricalStatus.choices,
        default=HistoricalStatus.UNKNOWN,
    )

    # Optional uploaded resume and candidate photograph.
    resume_file = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True,
    )

    photo = models.ImageField(
        upload_to="candidate_photos/",
        blank=True,
        null=True,
    )

    # Batch is optional for manually entered candidates.
    batch = models.ForeignKey(
        ApplicationBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidates",
    )

    is_valid = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["college", "applied_role"]),
            models.Index(fields=["experience_months"]),
        ]

    def __str__(self):
        return f"{self.candidate_name} ({self.email})"


# ============================================================
# 4. SCREENING RESULT MODEL
# ============================================================

class ScreeningResult(models.Model):

    class ScreeningStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        SELECTED = "SELECTED", "Selected"
        WAITLISTED = "WAITLISTED", "Waitlisted"
        REJECTED = "REJECTED", "Rejected"

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="screening_results",
    )

    role = models.ForeignKey(
        JobRole,
        on_delete=models.CASCADE,
        related_name="screening_results",
    )

    batch = models.ForeignKey(
        ApplicationBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="screening_results",
    )

    rule_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    ml_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    resume_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    status = models.CharField(
        max_length=20,
        choices=ScreeningStatus.choices,
        default=ScreeningStatus.PENDING,
        db_index=True,
    )

    reasons = models.JSONField(default=list, blank=True)

    screened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-ml_score", "-rule_score"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "role", "batch"],
                name="unique_candidate_role_batch_screening",
            ),
        ]

    @property
    def combined_score(self):
        """
        Example score: 40% rule score, 40% ML score,
        and 20% resume score.
        """
        return round(
            (self.rule_score * 0.40)
            + (self.ml_score * 0.40)
            + (self.resume_score * 0.20),
            2,
        )

    def __str__(self):
        return (
            f"{self.candidate.candidate_name} - "
            f"{self.role.title} - {self.status}"
        )


# ============================================================
# 5. INTERVIEW SLOT MODEL
# ============================================================

class InterviewSlot(models.Model):

    role = models.ForeignKey(
        JobRole,
        on_delete=models.CASCADE,
        related_name="interview_slots",
    )

    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_interview_slots",
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    is_booked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["role", "is_booked", "start_time"]),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_time <= self.start_time:
            raise ValidationError(
                {"end_time": "End time must be after start time."}
            )

    def __str__(self):
        return (
            f"{self.role.title} - "
            f"{self.start_time:%Y-%m-%d %H:%M}"
        )


# ============================================================
# 6. INTERVIEW FEEDBACK MODEL
# ============================================================

class InterviewFeedback(models.Model):

    class Recommendation(models.TextChoices):
        STRONG_HIRE = "STRONG_HIRE", "Strong Hire"
        HIRE = "HIRE", "Hire"
        HOLD = "HOLD", "Hold"
        REJECT = "REJECT", "Reject"

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="interview_feedback",
    )

    slot = models.ForeignKey(
        InterviewSlot,
        on_delete=models.PROTECT,
        related_name="feedback_entries",
    )

    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_interview_feedback",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    comments = models.TextField(blank=True)

    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
        default=Recommendation.HOLD,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Feedback: {self.candidate.candidate_name} "
            f"- {self.recommendation}"
        )
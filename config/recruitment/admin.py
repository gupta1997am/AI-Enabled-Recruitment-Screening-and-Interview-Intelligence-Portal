from django.contrib import admin

from .models import (
    JobRole,
    Candidate,
    ApplicationBatch,
    ScreeningResult,
    InterviewSlot,
    InterviewFeedback,
)


# ============================================================
# 1. JOB ROLE ADMIN
# ============================================================

@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "minimum_experience",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )

    list_editable = (
        "is_active",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Role Information", {
            "fields": (
                "title",
                "description",
                "required_skills",
            )
        }),
        ("Requirements", {
            "fields": (
                "minimum_experience",
                "is_active",
            )
        }),
        ("System Information", {
            "fields": ("created_at",),
        }),
    )


# ============================================================
# 2. APPLICATION BATCH ADMIN
# ============================================================

@admin.register(ApplicationBatch)
class ApplicationBatchAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "original_filename",
        "uploaded_by",
        "status",
        "total_rows",
        "processed_rows",
        "accepted_rows",
        "rejected_rows",
        "progress_percentage",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "original_filename",
        "uploaded_by__username",
        "uploaded_by__email",
    )

    readonly_fields = (
        "created_at",
        "completed_at",
        "progress_percentage",
    )

    fieldsets = (
        ("Upload Information", {
            "fields": (
                "uploaded_by",
                "file",
                "original_filename",
            )
        }),
        ("Processing Status", {
            "fields": (
                "status",
                "total_rows",
                "processed_rows",
                "accepted_rows",
                "rejected_rows",
                "progress_percentage",
                "error_message",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "completed_at",
            )
        }),
    )


# ============================================================
# 3. SCREENING RESULT INLINE
# ============================================================

class ScreeningResultInline(admin.TabularInline):

    model = ScreeningResult
    extra = 0

    fields = (
        "role",
        "batch",
        "rule_score",
        "ml_score",
        "resume_score",
        "status",
        "screened_at",
    )

    readonly_fields = (
        "screened_at",
    )


# ============================================================
# 4. CANDIDATE ADMIN
# ============================================================

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "candidate_name",
        "email",
        "phone",
        "college",
        "applied_role",
        "experience_months",
        "historical_selection_status",
        "is_valid",
        "created_at",
    )

    list_filter = (
        "applied_role",
        "college",
        "historical_selection_status",
        "is_valid",
        "created_at",
    )

    search_fields = (
        "candidate_name",
        "email",
        "phone",
        "college",
        "applied_role",
    )

    list_editable = (
        "historical_selection_status",
        "is_valid",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        ScreeningResultInline,
    )

    fieldsets = (
        ("Personal Information", {
            "fields": (
                "candidate_name",
                "email",
                "phone",
                "photo",
            )
        }),
        ("Education and Application", {
            "fields": (
                "college",
                "applied_role",
                "skills",
                "experience_months",
            )
        }),
        ("Employment Preferences", {
            "fields": (
                "notice_period_days",
                "expected_salary",
                "portfolio_url",
            )
        }),
        ("Resume Information", {
            "fields": (
                "resume_text",
                "resume_file",
            )
        }),
        ("Import and Validation", {
            "fields": (
                "batch",
                "historical_selection_status",
                "is_valid",
            )
        }),
        ("System Information", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    date_hierarchy = "created_at"
    list_per_page = 25


# ============================================================
# 5. SCREENING RESULT ADMIN
# ============================================================

@admin.register(ScreeningResult)
class ScreeningResultAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "candidate",
        "role",
        "rule_score",
        "ml_score",
        "resume_score",
        "display_combined_score",
        "status",
        "screened_at",
    )

    list_filter = (
        "status",
        "role",
        "screened_at",
    )

    search_fields = (
        "candidate__candidate_name",
        "candidate__email",
        "role__title",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "screened_at",
        "display_combined_score",
    )

    fieldsets = (
        ("Candidate and Role", {
            "fields": (
                "candidate",
                "role",
                "batch",
            )
        }),
        ("Screening Scores", {
            "fields": (
                "rule_score",
                "ml_score",
                "resume_score",
                "display_combined_score",
            )
        }),
        ("Decision", {
            "fields": (
                "status",
                "reasons",
                "screened_at",
            )
        }),
    )

    @admin.display(
        description="Combined Score",
        ordering="rule_score",
    )
    def display_combined_score(self, obj):
        return obj.combined_score


# ============================================================
# 6. INTERVIEW SLOT ADMIN
# ============================================================

@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "role",
        "interviewer",
        "start_time",
        "end_time",
        "is_booked",
    )

    list_filter = (
        "role",
        "is_booked",
        "start_time",
    )

    search_fields = (
        "role__title",
        "interviewer__username",
        "interviewer__email",
    )

    list_editable = (
        "is_booked",
    )

    date_hierarchy = "start_time"

    fieldsets = (
        ("Interview Assignment", {
            "fields": (
                "role",
                "interviewer",
            )
        }),
        ("Schedule", {
            "fields": (
                "start_time",
                "end_time",
                "is_booked",
            )
        }),
    )


# ============================================================
# 7. INTERVIEW FEEDBACK ADMIN
# ============================================================

@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "candidate",
        "slot",
        "interviewer",
        "rating",
        "recommendation",
        "created_at",
    )

    list_filter = (
        "recommendation",
        "rating",
        "created_at",
    )

    search_fields = (
        "candidate__candidate_name",
        "candidate__email",
        "interviewer__username",
        "comments",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Interview Details", {
            "fields": (
                "candidate",
                "slot",
                "interviewer",
            )
        }),
        ("Evaluation", {
            "fields": (
                "rating",
                "recommendation",
                "comments",
            )
        }),
        ("System Information", {
            "fields": ("created_at",),
        }),
    )
import os
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Q

from .models import (
    Candidate,
    ApplicationBatch,
    InterviewSlot,
    InterviewFeedback,
)


# ============================================================
# 1. CANDIDATE UPLOAD FORM
# ============================================================

class CandidateUploadForm(forms.ModelForm):

    file = forms.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=["csv", "xlsx", "xls"]
            )
        ],
        help_text="Upload a CSV or Excel file.",
    )

    class Meta:
        model = ApplicationBatch
        fields = ["file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        # Maximum upload size: 10 MB
        max_size = 10 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise ValidationError(
                "File size must not exceed 10 MB."
            )

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension not in [".csv", ".xlsx", ".xls"]:
            raise ValidationError(
                "Only CSV and Excel files are allowed."
            )

        return uploaded_file

    def save(self, commit=True):
        batch = super().save(commit=False)
        uploaded_file = self.cleaned_data["file"]

        batch.original_filename = uploaded_file.name
        batch.status = ApplicationBatch.BatchStatus.PENDING

        if commit:
            batch.save()

        return batch


# ============================================================
# 2. CANDIDATE FORM
# ============================================================

class CandidateForm(forms.ModelForm):

    class Meta:
        model = Candidate

        fields = [
            "candidate_name",
            "email",
            "phone",
            "college",
            "applied_role",
            "skills",
            "experience_months",
            "notice_period_days",
            "expected_salary",
            "resume_text",
            "portfolio_url",
            "historical_selection_status",
            "resume_file",
            "photo",
            "batch",
            "is_valid",
        ]

        widgets = {
            "candidate_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter candidate name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "candidate@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phone number",
                }
            ),
            "college": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter college name",
                }
            ),
            "applied_role": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Python Developer",
                }
            ),
            "skills": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": (
                        'Enter a JSON list, e.g. ["python", "django"]'
                    ),
                }
            ),
            "experience_months": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
            "notice_period_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
            "expected_salary": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "resume_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "portfolio_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com",
                }
            ),
        }

    def clean_candidate_name(self):
        name = self.cleaned_data["candidate_name"].strip()

        if not name:
            raise ValidationError(
                "Candidate name is required."
            )

        return " ".join(name.split())

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        # Permit editing the existing record while checking
        # for duplicate emails on other candidate records.
        duplicates = Candidate.objects.filter(
            email__iexact=email
        )

        if self.instance and self.instance.pk:
            duplicates = duplicates.exclude(
                pk=self.instance.pk
            )

        if duplicates.exists():
            raise ValidationError(
                "A candidate with this email already exists."
            )

        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        # Basic format check; not phone-number verification.
        if not re.fullmatch(
            r"\+?[0-9][0-9\s()-]{7,18}",
            phone,
        ):
            raise ValidationError(
                "Enter a valid phone number."
            )

        return phone

    def clean_skills(self):
        skills = self.cleaned_data.get("skills")

        if not isinstance(skills, list):
            raise ValidationError(
                'Skills must be a JSON list, e.g. ["python", "django"].'
            )

        cleaned_skills = []

        for skill in skills:
            if not isinstance(skill, str):
                raise ValidationError(
                    "Every skill must be a string."
                )

            skill = skill.strip().lower()

            if skill:
                cleaned_skills.append(skill)

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(cleaned_skills))

    def clean(self):
        cleaned_data = super().clean()

        experience = cleaned_data.get("experience_months")
        notice = cleaned_data.get("notice_period_days")
        salary = cleaned_data.get("expected_salary")

        if experience is not None and experience < 0:
            self.add_error(
                "experience_months",
                "Experience cannot be negative.",
            )

        if notice is not None and notice < 0:
            self.add_error(
                "notice_period_days",
                "Notice period cannot be negative.",
            )

        if salary is not None and salary < 0:
            self.add_error(
                "expected_salary",
                "Expected salary cannot be negative.",
            )

        return cleaned_data


# ============================================================
# 3. SCREENING STATUS FORM
# ============================================================

class ScreeningStatusForm(forms.Form):

    status = forms.ChoiceField(
        choices=[
            ("PENDING", "Pending"),
            ("SHORTLISTED", "Shortlisted"),
            ("SELECTED", "Selected"),
            ("WAITLISTED", "Waitlisted"),
            ("REJECTED", "Rejected"),
        ],
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )


# ============================================================
# 4. INTERVIEW SLOT FORM
# ============================================================

class InterviewSlotForm(forms.ModelForm):

    class Meta:
        model = InterviewSlot

        fields = [
            "role",
            "interviewer",
            "start_time",
            "end_time",
            "is_booked",
        ]

        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            self.add_error(
                "end_time",
                "End time must be after start time.",
            )

        return cleaned_data


# ============================================================
# 5. INTERVIEW FEEDBACK FORM
# ============================================================

class InterviewFeedbackForm(forms.ModelForm):

    class Meta:
        model = InterviewFeedback

        fields = [
            "candidate",
            "slot",
            "rating",
            "comments",
            "recommendation",
        ]

        widgets = {
            "rating": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter interview feedback",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        candidate = cleaned_data.get("candidate")
        slot = cleaned_data.get("slot")

        if candidate and slot:
            if candidate.applied_role.lower() != slot.role.title.lower():
                self.add_error(
                    "slot",
                    "The interview slot does not match the candidate's role.",
                )

        return cleaned_data
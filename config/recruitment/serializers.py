from rest_framework import serializers
from .models import Candidate, JobRole, ScreeningResult


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",
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
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "batch",
            "is_valid",
            "created_at",
            "updated_at",
        ]

    def validate_candidate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Candidate name cannot be empty."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        queryset = Candidate.objects.filter(email__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A candidate with this email already exists."
            )

        return value

    def validate_experience_months(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Experience cannot be negative."
            )

        return value

    def validate_notice_period_days(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Notice period cannot be negative."
            )

        return value


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = [
            "id",
            "title",
            "description",
            "required_skills",
            "minimum_experience",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ScreeningResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate.candidate_name",
        read_only=True,
    )
    candidate_email = serializers.EmailField(
        source="candidate.email",
        read_only=True,
    )
    role_title = serializers.CharField(
        source="role.title",
        read_only=True,
    )
    combined_score = serializers.FloatField(read_only=True)

    class Meta:
        model = ScreeningResult
        fields = [
            "id",
            "candidate",
            "candidate_name",
            "candidate_email",
            "role",
            "role_title",
            "batch",
            "rule_score",
            "ml_score",
            "resume_score",
            "combined_score",
            "status",
            "reasons",
            "screened_at",
        ]
        read_only_fields = [
            "id",
            "candidate_name",
            "candidate_email",
            "role_title",
            "combined_score",
            "screened_at",
        ]
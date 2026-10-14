import re


class CandidateValidationError(Exception):
    pass


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s()-]{7,18}$")


def validate_candidate(row):
    errors = []

    email = str(row.get("email", "")).strip()
    phone = str(row.get("phone", "")).strip()

    if not EMAIL_PATTERN.fullmatch(email):
        errors.append("invalid_email")

    if not PHONE_PATTERN.fullmatch(phone):
        errors.append("invalid_phone")

    if not str(row.get("candidate_name", "")).strip():
        errors.append("missing_candidate_name")

    return errors
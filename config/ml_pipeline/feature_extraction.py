import pandas as pd

from .preprocessing import prepare_candidate_data


FEATURE_COLUMNS = [
    "combined_text",
    "experience_months",
    "notice_period_days",
    "expected_salary",
]


def extract_features(dataframe):
    """Convert candidate records into ML-ready features."""

    df = prepare_candidate_data(dataframe)

    df["combined_text"] = (
        df["skills"] + " "
        + df["resume_text"] + " "
        + df["applied_role"]
    ).str.lower().str.strip()

    return df[FEATURE_COLUMNS].copy()


def candidate_to_dataframe(candidate):
    """Convert a Django Candidate instance into one DataFrame row."""

    skills = candidate.skills or []

    if isinstance(skills, list):
        skills_text = " ".join(str(skill) for skill in skills)
    else:
        skills_text = str(skills)

    return pd.DataFrame([{
        "skills": skills_text,
        "resume_text": candidate.resume_text or "",
        "applied_role": candidate.applied_role or "",
        "experience_months": candidate.experience_months or 0,
        "notice_period_days": candidate.notice_period_days or 0,
        "expected_salary": candidate.expected_salary or 0,
    }])
import pandas as pd


def prepare_candidate_data(dataframe):
    """Clean candidate data before feature extraction."""

    df = dataframe.copy()
    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    for column in ["skills", "resume_text", "applied_role"]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].fillna("").astype(str).str.strip()

    for column in [
        "experience_months",
        "notice_period_days",
        "expected_salary",
    ]:
        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        ).fillna(0).clip(lower=0)

    return df
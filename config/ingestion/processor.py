import pandas as pd

from ingestion.cleaning import clean_candidate
from ingestion.validators import validate_candidate


def process_file(file_path):
    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Only CSV and Excel files are supported")

    accepted, rejected = [], []

    for row in df.to_dict(orient="records"):
        cleaned = clean_candidate(row)
        errors = validate_candidate(cleaned)

        if errors:
            rejected.append({
                **cleaned,
                "error_reason": ", ".join(errors),
            })
            continue

        accepted.append(cleaned)

    pd.DataFrame(accepted).to_csv(
        "ingestion/output/accepted_rows.csv", index=False
    )
    pd.DataFrame(rejected).to_csv(
        "ingestion/output/rejected_rows.csv", index=False
    )

    return {
        "total": len(df),
        "accepted": len(accepted),
        "rejected": len(rejected),
    }
import copy


def clean_candidate(row):
    cleaned = copy.deepcopy(row)

    for key, value in cleaned.items():
        if isinstance(value, str):
            value = value.strip()
            value = value.removeprefix("Name:")
            value = value.removesuffix(";")
            cleaned[key] = " ".join(value.split())

    cleaned["candidate_name"] = (
        cleaned.get("candidate_name", "").title()
    )
    cleaned["email"] = cleaned.get("email", "").lower()
    cleaned["skills"] = cleaned.get("skills", "").lower()

    return cleaned
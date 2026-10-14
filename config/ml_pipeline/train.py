import pandas as pd

from django.db.models import Q

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from recruitment.models import Candidate
from .feature_extraction import extract_features
from .model_utils import save_model


def build_pipeline():
    """Build the preprocessing and classification pipeline."""

    text_pipeline = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
    )

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    features = ColumnTransformer([
        ("text", text_pipeline, "combined_text"),
        (
            "numeric",
            numeric_pipeline,
            [
                "experience_months",
                "notice_period_days",
                "expected_salary",
            ],
        ),
    ])

    return Pipeline([
        ("features", features),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight="balanced",
            ),
        ),
    ])


def train_model():
    """Train and save a model from historical candidate records."""

    candidates = Candidate.objects.filter(
        Q(historical_selection_status="SELECTED")
        | Q(historical_selection_status="REJECTED")
    )

    records = list(candidates.values(
        "skills",
        "resume_text",
        "applied_role",
        "experience_months",
        "notice_period_days",
        "expected_salary",
        "historical_selection_status",
    ))

    if len(records) < 10:
        raise ValueError(
            "At least 10 labeled candidates are required "
            "for this baseline training script."
        )

    dataframe = pd.DataFrame(records)
    labels = dataframe["historical_selection_status"]

    if labels.nunique() != 2 or labels.value_counts().min() < 2:
        raise ValueError(
            "Training requires at least two SELECTED and "
            "two REJECTED candidates."
        )

    features = extract_features(dataframe)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    model = build_pipeline()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)

    print("Accuracy:", round(accuracy_score(y_test, predictions), 3))
    print(classification_report(
        y_test,
        predictions,
        zero_division=0,
    ))

    save_model(model)
    print("Trained model saved successfully.")

    return model


if __name__ == "__main__":
    train_model()
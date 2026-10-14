from .feature_extraction import (
    candidate_to_dataframe,
    extract_features,
)
from .model_utils import load_model


def predict_candidate(candidate):
    """
    Return the predicted class and selection score for a
    Django Candidate instance.
    """

    model = load_model()

    dataframe = candidate_to_dataframe(candidate)
    features = extract_features(dataframe)

    predicted_status = model.predict(features)[0]

    classifier = model.named_steps["classifier"]
    classes = list(classifier.classes_)

    if "SELECTED" in classes:
        selected_index = classes.index("SELECTED")
        probability = model.predict_proba(features)[0][selected_index]
        score = round(float(probability) * 100, 2)
    else:
        score = 0.0

    return {
        "predicted_status": str(predicted_status),
        "ml_score": score,
    }
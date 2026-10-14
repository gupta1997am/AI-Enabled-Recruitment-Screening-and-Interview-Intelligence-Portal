from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


def evaluate_model(model, x_test, y_test):
    """Evaluate a fitted model against test data."""

    predictions = model.predict(x_test)

    results = {
        "accuracy": round(
            float(accuracy_score(y_test, predictions)), 4
        ),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=["REJECTED", "SELECTED"],
        ).tolist(),
    }

    return results


def print_evaluation(results):
    """Print evaluation metrics in a readable format."""

    print("Accuracy:", results["accuracy"])
    print("\nClassification report:")

    for label, metrics in results["classification_report"].items():
        if isinstance(metrics, dict):
            print(
                f"{label}: "
                f"precision={metrics.get('precision', 0):.3f}, "
                f"recall={metrics.get('recall', 0):.3f}, "
                f"f1={metrics.get('f1-score', 0):.3f}"
            )

    print("\nConfusion matrix:")
    print(results["confusion_matrix"])
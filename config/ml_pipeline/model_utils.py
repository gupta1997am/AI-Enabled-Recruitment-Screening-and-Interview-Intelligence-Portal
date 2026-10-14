from pathlib import Path
import joblib


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "candidate_model.joblib"


def save_model(model, path=MODEL_PATH):
    """Save a trained model to disk."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path=MODEL_PATH):
    """Load a previously trained model."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Trained model not found at {path}. "
            "Run the training script first."
        )

    return joblib.load(path)
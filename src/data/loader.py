"""Dataset path resolution, validation, and loading module.

Provides reliable dataset loading in both Google Colab and local environments.
Validates file presence, columns ('text', 'label'), and class balance.
"""
from pathlib import Path
import os
import sys
import pandas as pd


def resolve_project_root(custom_path: str = None) -> Path:
    """Resolve the project root directory reliably across Colab, local, and custom environments."""
    if custom_path:
        p = Path(custom_path)
        if p.exists() and (p / "dataset" / "processed" / "train.csv").is_file():
            return p

    # Check environment variable
    env_dir = os.environ.get("PHISHSENSE_PROJECT_DIR", "")
    if env_dir:
        p = Path(env_dir)
        if p.exists() and (p / "dataset" / "processed" / "train.csv").is_file():
            return p

    # Candidate locations in priority order
    candidates = [
        Path("/content/drive/MyDrive/Applied_AI/Team 02/PhishSense Final"),
        Path("/content/drive/MyDrive/Applied_AI/Team 02"),
        Path("/content/drive/MyDrive/PhishSense Final"),
        Path.cwd(),
        Path(__file__).resolve().parent.parent.parent,
    ]

    for c in candidates:
        if c and c.exists():
            if (c / "dataset" / "processed" / "train.csv").is_file():
                return c

    # Fallback recursive search if in Colab Google Drive
    drive_root = Path("/content/drive/MyDrive")
    if drive_root.exists() and ("google.colab" in sys.modules or os.path.exists("/content")):
        for root, dirs, files in os.walk(str(drive_root)):
            if "train.csv" in files and "processed" in root.replace("\\", "/"):
                candidate = Path(root).parent.parent
                if (candidate / "dataset" / "processed" / "train.csv").is_file():
                    return candidate

    # Return current directory if nothing else found
    return Path.cwd()


def get_dataset_paths(project_root: Path = None) -> dict:
    """Return dictionary of dataset paths validated against the project root."""
    if project_root is None:
        project_root = resolve_project_root()

    processed_dir = project_root / "dataset" / "processed"
    paths = {
        "root": project_root,
        "processed_dir": processed_dir,
        "train": processed_dir / "train.csv",
        "validation": processed_dir / "validation.csv",
        "test": processed_dir / "test.csv",
        "probe": processed_dir / "temporal_holdout_probe.csv",
        "results": project_root / "results",
        "artifacts": project_root / "artifacts",
    }
    if not paths["probe"].is_file():
        paths["probe"] = processed_dir / "ood_probe.csv"

    return paths


def validate_split_file(path: Path, split_name: str) -> None:
    """Assert that a required split file exists and is readable."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Required {split_name} dataset file missing at: {path}\n"
            f"Expected directory: {path.parent}\n"
            f"Please ensure dataset/processed/{path.name} exists."
        )


def load_and_validate_datasets(
    project_root: Path = None,
    expected_train_rows: int = 7696,
    expected_val_rows: int = 1646,
    expected_test_rows: int = 1658,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, validation, test, and probe splits with strict validation.
    
    Validates:
    - File existence
    - Required columns ('text', 'label')
    - Allowed label set ({'safe', 'phishing'})
    - Class balance
    """
    paths = get_dataset_paths(project_root)

    # 1. Validate file presence
    validate_split_file(paths["train"], "Train")
    validate_split_file(paths["validation"], "Validation")
    validate_split_file(paths["test"], "Test")

    # 2. Load DataFrames
    train_df = pd.read_csv(paths["train"])
    val_df = pd.read_csv(paths["validation"])
    test_df = pd.read_csv(paths["test"])
    probe_df = pd.read_csv(paths["probe"]) if paths["probe"].is_file() else None

    # 3. Column and label validation
    for name, df in [("Train", train_df), ("Validation", val_df), ("Test", test_df)]:
        if "text" not in df.columns or "label" not in df.columns:
            raise ValueError(f"{name} split missing required columns ('text', 'label'). Found: {list(df.columns)}")
        
        labels = set(df["label"].dropna().unique())
        invalid_labels = labels - {"safe", "phishing"}
        if invalid_labels:
            raise ValueError(f"{name} split contains invalid labels: {invalid_labels}. Expected only 'safe' or 'phishing'.")

    return train_df, val_df, test_df, probe_df

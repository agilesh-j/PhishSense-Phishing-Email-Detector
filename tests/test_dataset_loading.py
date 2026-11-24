"""Unit tests for dataset path resolution, validation, and loading."""
import pytest
from pathlib import Path
import pandas as pd
from src.data.loader import (
    resolve_project_root,
    get_dataset_paths,
    load_and_validate_datasets,
    validate_split_file,
)


def test_resolve_project_root_exists():
    root = resolve_project_root()
    assert root.exists(), f"Resolved project root does not exist: {root}"
    train_file = root / "dataset" / "processed" / "train.csv"
    assert train_file.is_file(), f"Expected train.csv not found under resolved root: {train_file}"


def test_get_dataset_paths():
    root = resolve_project_root()
    paths = get_dataset_paths(root)
    assert paths["train"].is_file(), f"Missing train.csv at {paths['train']}"
    assert paths["validation"].is_file(), f"Missing validation.csv at {paths['validation']}"
    assert paths["test"].is_file(), f"Missing test.csv at {paths['test']}"
    assert paths["results"].exists() or paths["results"].parent.exists()
    assert paths["artifacts"].exists() or paths["artifacts"].parent.exists()


def test_load_and_validate_datasets_counts_and_columns():
    root = resolve_project_root()
    train_df, val_df, test_df, probe_df = load_and_validate_datasets(root)

    # Row counts
    assert len(train_df) == 7696, f"Expected 7,696 train rows, got {len(train_df)}"
    assert len(val_df) == 1646, f"Expected 1,646 validation rows, got {len(val_df)}"
    assert len(test_df) == 1658, f"Expected 1,658 test rows, got {len(test_df)}"

    # Required columns
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        assert "text" in df.columns, f"{name} missing 'text' column"
        assert "label" in df.columns, f"{name} missing 'label' column"

    # Class balance (50:50)
    assert (train_df["label"] == "phishing").sum() == 3848
    assert (train_df["label"] == "safe").sum() == 3848
    assert (val_df["label"] == "phishing").sum() == 823
    assert (val_df["label"] == "safe").sum() == 823
    assert (test_df["label"] == "phishing").sum() == 829
    assert (test_df["label"] == "safe").sum() == 829


def test_validate_split_file_missing():
    non_existent = Path("/non/existent/path/dataset.csv")
    with pytest.raises(FileNotFoundError) as exc_info:
        validate_split_file(non_existent, "TestSplit")
    assert "Required TestSplit dataset file missing" in str(exc_info.value)

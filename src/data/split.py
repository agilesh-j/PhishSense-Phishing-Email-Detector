"""Group-aware, leakage-free stratified splitting (70/15/15) with zero-overlap assertions."""
import json
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, train_test_split


def make_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
    group_col: str = "cluster_id",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Split curated dataset into Train (70%), Validation (15%), and Test (15%) preserving group integrity and class balance.

    Returns:
        (train_df, val_df, test_df, report_dict)
    """
    assert (
        abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5
    ), "Split ratios must sum to 1.0"
    df = df.copy()

    # Assign group id if not present (default to index)
    if group_col not in df.columns:
        df[group_col] = df.index.astype(str)

    # First split: 70% Train, 30% Temp (Val + Test)
    # Using group-aware stratification
    temp_ratio = val_ratio + test_ratio  # 0.30

    # If all groups are unique, use standard stratified split
    if df[group_col].nunique() == len(df):
        train_df, temp_df = train_test_split(
            df,
            test_size=temp_ratio,
            stratify=df["label"],
            random_state=random_seed,
        )
        val_sub_ratio = val_ratio / temp_ratio  # 0.50
        val_df, test_df = train_test_split(
            temp_df,
            test_size=(1.0 - val_sub_ratio),
            stratify=temp_df["label"],
            random_state=random_seed,
        )
    else:
        # Group-aware split using StratifiedGroupKFold
        # Create 10 folds: 7 folds for train, 1.5 folds each for val/test
        sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=random_seed)
        folds = list(sgkf.split(df, df["label"], df[group_col]))

        # Take folds 0-6 as Train (70%), fold 7-8 as Val, fold 9 as Test (approx)
        train_idx = np.concatenate([folds[i][1] for i in range(7)])
        val_idx = np.concatenate([folds[7][1], folds[8][1][: len(folds[8][1]) // 2]])
        test_idx = np.concatenate([folds[8][1][len(folds[8][1]) // 2 :], folds[9][1]])

        train_df = df.iloc[train_idx].copy()
        val_df = df.iloc[val_idx].copy()
        test_df = df.iloc[test_idx].copy()

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # Assertions for zero leakage
    train_texts = set(train_df["text"].str.lower().str.strip())
    val_texts = set(val_df["text"].str.lower().str.strip())
    test_texts = set(test_df["text"].str.lower().str.strip())

    train_val_overlap = train_texts.intersection(val_texts)
    train_test_overlap = train_texts.intersection(test_texts)
    val_test_overlap = val_texts.intersection(test_texts)

    assert (
        len(train_val_overlap) == 0
    ), f"Leakage detected between Train and Val: {len(train_val_overlap)} rows"
    assert (
        len(train_test_overlap) == 0
    ), f"Leakage detected between Train and Test: {len(train_test_overlap)} rows"
    assert (
        len(val_test_overlap) == 0
    ), f"Leakage detected between Val and Test: {len(val_test_overlap)} rows"

    # Assert group non-overlap
    if group_col in df.columns:
        train_groups = set(train_df[group_col])
        val_groups = set(val_df[group_col])
        test_groups = set(test_df[group_col])
        assert (
            len(train_groups.intersection(val_groups)) == 0
        ), "Group overlap between Train and Val"
        assert (
            len(train_groups.intersection(test_groups)) == 0
        ), "Group overlap between Train and Test"
        assert (
            len(val_groups.intersection(test_groups)) == 0
        ), "Group overlap between Val and Test"

    report = {
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "train_class_balance": train_df["label"].value_counts(normalize=True).to_dict(),
        "val_class_balance": val_df["label"].value_counts(normalize=True).to_dict(),
        "test_class_balance": test_df["label"].value_counts(normalize=True).to_dict(),
        "leakage_assertions_passed": True,
    }
    return train_df, val_df, test_df, report


def save_processed_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    processed_dir: str = "dataset/processed",
    results_dir: str = "results",
) -> None:
    """Save clean train.csv, validation.csv, test.csv with text,label only, and save provenance to results."""
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Standard clean splits for training / testing: text, label only
    train_clean = train_df[["text", "label"]].copy()
    val_clean = val_df[["text", "label"]].copy()
    test_clean = test_df[["text", "label"]].copy()

    train_clean.to_csv(os.path.join(processed_dir, "train.csv"), index=False)
    val_clean.to_csv(os.path.join(processed_dir, "validation.csv"), index=False)
    test_clean.to_csv(os.path.join(processed_dir, "test.csv"), index=False)

    # Provenance tracking files
    train_df.to_csv(
        os.path.join(results_dir, "provenance_train.csv"), index=False
    )
    val_df.to_csv(os.path.join(results_dir, "provenance_val.csv"), index=False)
    test_df.to_csv(os.path.join(results_dir, "provenance_test.csv"), index=False)

    print(
        f"Saved processed splits to {processed_dir} and provenance logs to {results_dir}."
    )

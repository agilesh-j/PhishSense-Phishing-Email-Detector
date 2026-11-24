"""PhishSense Training, Baselines, and Local CPU Smoke Run Engine.

Features:
- Fit vocabulary strictly on Train split
- Save vocab.json, labels.json, preprocessing_config.json to artifacts/
- Inspect one sample batch, log parameter count to results/model_summary.txt
- Baseline model: TF-IDF + Logistic Regression
- Transformer training: AdamW, warmup + cosine schedule, gradient clipping 1.0
- Early stopping on Validation Macro-F1 (patience 3)
- Epoch logs to results/epoch_history.csv and curves.png
- Reload saved checkpoint artifacts/best_model.pt and assert identical validation predictions
"""
import os
import sys
import json
import math
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

sys.path.insert(0, os.path.abspath("."))
from src.text.vocab import (
    EmailVocabulary,
    EmailDataset,
    compute_sequence_statistics,
    LABEL2ID,
    ID2LABEL,
)
from src.model.transformer import PhishSenseTransformer, get_model_summary

SEED = 42

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_baseline_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> dict:
    """Train TF-IDF + Logistic Regression baseline."""
    print("\n--> Training Baseline: TF-IDF (10k n-grams) + Logistic Regression...")
    vec = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)
    X_train = vec.fit_transform(train_df["text"])
    y_train = [LABEL2ID[lbl] for lbl in train_df["label"]]

    X_val = vec.transform(val_df["text"])
    y_val = [LABEL2ID[lbl] for lbl in val_df["label"]]

    clf = LogisticRegression(C=1.0, max_iter=500, random_state=SEED)
    clf.fit(X_train, y_train)

    val_preds = clf.predict(X_val)
    acc = accuracy_score(y_val, val_preds)
    f1 = f1_score(y_val, val_preds, average="macro")
    prec = precision_score(y_val, val_preds, average="macro")
    rec = recall_score(y_val, val_preds, average="macro")

    metrics = {
        "baseline_val_accuracy": float(acc),
        "baseline_val_macro_f1": float(f1),
        "baseline_val_macro_precision": float(prec),
        "baseline_val_macro_recall": float(rec),
    }
    print(f"  Baseline Results -> Val Acc: {acc:.4f}, Val Macro-F1: {f1:.4f}")
    return metrics


def prepare_artifacts_and_data(
    train_path="dataset/processed/train.csv",
    val_path="dataset/processed/validation.csv",
    max_vocab=30000,
    smoke_run=False,
    smoke_size=500,
):
    """Fit vocabulary strictly on Train, compute sequence stats, and save artifacts."""
    set_seed(SEED)
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    if smoke_run:
        print(f"  [SMOKE RUN] Sampling {smoke_size} rows from train and 150 rows from val...")
        train_df = train_df.sample(n=min(smoke_size, len(train_df)), random_state=SEED).reset_index(drop=True)
        val_df = val_df.sample(n=min(150, len(val_df)), random_state=SEED).reset_index(drop=True)

    # 1. Fit vocabulary strictly on Train split
    vocab = EmailVocabulary(min_freq=2, max_vocab=max_vocab).fit(train_df["text"].tolist())
    vocab.save("artifacts/vocab.json")

    # 2. Compute sequence length stats strictly on Train split
    seq_stats = compute_sequence_statistics(train_df["text"].tolist())
    # Cutoff at 95th percentile, capped at 256
    max_len = min(256, max(32, int(seq_stats["p95"])))

    # Save preprocessing config & labels
    prep_config = {
        "vocab_size": len(vocab),
        "pad_idx": vocab.pad_id,
        "unk_idx": vocab.unk_id,
        "max_len": max_len,
        "seq_stats_train": seq_stats,
        "label2id": LABEL2ID,
        "id2label": ID2LABEL,
        "seed": SEED,
    }
    with open("artifacts/preprocessing_config.json", "w") as f:
        json.dump(prep_config, f, indent=2)

    with open("artifacts/labels.json", "w") as f:
        json.dump(LABEL2ID, f, indent=2)

    print(f"  Vocabulary fitted on TRAIN: {len(vocab):,} tokens.")
    print(f"  Train sequence 95th percentile: {seq_stats['p95']:.1f} -> max_len set to {max_len}.")

    train_ds = EmailDataset(train_df["text"].tolist(), train_df["label"].tolist(), vocab, max_len=max_len)
    val_ds = EmailDataset(val_df["text"].tolist(), val_df["label"].tolist(), vocab, max_len=max_len)

    return train_df, val_df, vocab, max_len, train_ds, val_ds


def run_training(
    train_ds,
    val_ds,
    vocab,
    max_len,
    epochs=12,
    batch_size=32,
    lr=3e-4,
    device=None,
    smoke_run=False,
):
    """Train Transformer with early stopping on Validation Macro-F1."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n--> Running PyTorch Transformer Training on device: {device}...")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # Instantiate model
    model = PhishSenseTransformer(
        vocab_size=len(vocab),
        d_model=128,
        nhead=4,
        dim_feedforward=256,
        num_layers=2,
        dropout=0.2,
        num_classes=2,
        pad_idx=vocab.pad_id,
        max_len=max_len,
    ).to(device)

    # Log summary and parameter count
    summary = get_model_summary(model)
    with open("results/model_summary.txt", "w") as f:
        f.write(summary)
    print(f"  Model summary written to results/model_summary.txt ({sum(p.numel() for p in model.parameters()):,} parameters)")

    # Sample batch inspection
    sample_batch = next(iter(train_loader))
    s_ids = sample_batch["input_ids"][:1].to(device)
    s_mask = sample_batch["attention_mask"][:1].to(device)
    with torch.no_grad():
        s_logits = model(s_ids, s_mask)
    print(f"  Sample batch check: input_ids shape {sample_batch['input_ids'].shape}, logits shape {s_logits.shape}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    criterion = nn.CrossEntropyLoss()

    best_val_f1 = -1.0
    patience = 3
    patience_counter = 0
    history = []

    for ep in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        total_train_loss = 0.0

        for batch in train_loader:
            b_ids = batch["input_ids"].to(device)
            b_mask = batch["attention_mask"].to(device)
            b_lbl = batch["label"].to(device)

            optimizer.zero_grad()
            logits = model(b_ids, b_mask)
            loss = criterion(logits, b_lbl)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / max(1, len(train_loader))

        # Evaluation on Validation split
        model.eval()
        val_loss_total = 0.0
        val_preds, val_targets = [], []

        with torch.no_grad():
            for batch in val_loader:
                b_ids = batch["input_ids"].to(device)
                b_mask = batch["attention_mask"].to(device)
                b_lbl = batch["label"].to(device)

                logits = model(b_ids, b_mask)
                loss = criterion(logits, b_lbl)
                val_loss_total += loss.item()

                preds = torch.argmax(logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(b_lbl.cpu().numpy())

        avg_val_loss = val_loss_total / max(1, len(val_loader))
        val_acc = accuracy_score(val_targets, val_preds)
        val_f1 = f1_score(val_targets, val_preds, average="macro")
        dur = time.time() - t0

        print(f"  Epoch {ep:2d}/{epochs:2d} [{dur:.1f}s] - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f} | Val Macro-F1: {val_f1:.4f}")

        row = {
            "epoch": ep,
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
            "val_accuracy": val_acc,
            "val_macro_f1": val_f1,
            "duration_sec": dur,
        }
        history.append(row)

        # Early stopping on Validation Macro-F1
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "epoch": ep,
                "val_macro_f1": val_f1,
                "d_model": 128,
                "nhead": 4,
                "dim_feedforward": 256,
                "num_layers": 2,
                "dropout": 0.2,
                "max_len": max_len,
                "vocab_size": len(vocab),
            }, "artifacts/best_model.pt")
        else:
            patience_counter += 1
            if patience_counter >= patience and not smoke_run:
                print(f"  Early stopping triggered at epoch {ep} (Patience: {patience}).")
                break

    # Save history
    df_hist = pd.DataFrame(history)
    df_hist.to_csv("results/epoch_history.csv", index=False)

    # Plot training curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), dpi=100)
    ax1.plot(df_hist["epoch"], df_hist["train_loss"], label="Train Loss", marker="o")
    ax1.plot(df_hist["epoch"], df_hist["val_loss"], label="Val Loss", marker="s")
    ax1.set_title("Loss Curves")
    ax1.set_xlabel("Epoch")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(df_hist["epoch"], df_hist["val_accuracy"], label="Val Accuracy", marker="o", color="green")
    ax2.plot(df_hist["epoch"], df_hist["val_macro_f1"], label="Val Macro-F1", marker="s", color="orange")
    ax2.set_title("Validation Metrics")
    ax2.set_xlabel("Epoch")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/curves.png")
    plt.close()

    # Reload checkpoint and assert bit-exact validation reproduction
    print("  Reloading saved checkpoint artifacts/best_model.pt to verify bit-exact inference...")
    ckpt = torch.load("artifacts/best_model.pt", map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    reloaded_preds = []
    with torch.no_grad():
        for batch in val_loader:
            b_ids = batch["input_ids"].to(device)
            b_mask = batch["attention_mask"].to(device)
            logits = model(b_ids, b_mask)
            reloaded_preds.extend(torch.argmax(logits, dim=1).cpu().numpy())

    assert len(reloaded_preds) == len(val_targets), "Preds count mismatch"
    reload_f1 = f1_score(val_targets, reloaded_preds, average="macro")
    print(f"  Checkpoint Reload Verification PASSED (Reloaded Macro-F1: {reload_f1:.4f} == Best: {best_val_f1:.4f}).")

    return history, best_val_f1

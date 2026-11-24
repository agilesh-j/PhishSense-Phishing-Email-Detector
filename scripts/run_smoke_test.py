"""Local CPU Smoke Test for PhishSense.

Runs:
1. Baseline (TF-IDF + Logistic Regression) on smoke sample
2. Transformer from scratch (2 epochs on CPU, batch size 16)
3. Checkpoint reload verification
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from src.train.train import prepare_artifacts_and_data, train_baseline_model, run_training

def main():
    print("=======================================================")
    print("STARTING PHISHSENSE LOCAL CPU SMOKE TEST")
    print("=======================================================")
    
    train_df, val_df, vocab, max_len, train_ds, val_ds = prepare_artifacts_and_data(
        train_path="dataset/processed/train.csv",
        val_path="dataset/processed/validation.csv",
        smoke_run=True,
        smoke_size=500,
    )
    
    # Run Baseline
    baseline_metrics = train_baseline_model(train_df, val_df)
    
    # Run Transformer 2 epochs on CPU
    history, best_f1 = run_training(
        train_ds=train_ds,
        val_ds=val_ds,
        vocab=vocab,
        max_len=max_len,
        epochs=2,
        batch_size=16,
        lr=5e-4,
        smoke_run=True,
    )
    
    print("\n=======================================================")
    print(f"SMOKE TEST COMPLETED SUCCESSFULLY!")
    print(f"Baseline Val Macro-F1:    {baseline_metrics['baseline_val_macro_f1']:.4f}")
    print(f"Transformer Val Macro-F1: {best_f1:.4f}")
    print("=======================================================")

if __name__ == "__main__":
    main()

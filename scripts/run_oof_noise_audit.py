"""Out-Of-Fold (OOF) Label Noise Audit on Train + Validation splits.

Performs 5-fold cross-validation on Train + Val combined (strictly NOT touching Test).
Identifies high-confidence model disagreements where p(label) > 0.90 but ground truth disagrees.
Saves audit to results/oof_label_noise.csv and summary to results/oof_noise_summary.json.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

SEED = 42

def main():
    print("=======================================================")
    print("RUNNING 5-FOLD OUT-OF-FOLD LABEL NOISE AUDIT (TRAIN+VAL)")
    print("=======================================================")
    
    train_meta = pd.read_csv("dataset/processed/train_metadata.csv")
    val_meta = pd.read_csv("dataset/processed/validation_metadata.csv")
    
    df_combined = pd.concat([train_meta, val_meta], ignore_index=True)
    print(f"Total Train+Val rows for OOF audit: {len(df_combined)}")
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof_probs = np.zeros(len(df_combined))
    
    y = (df_combined["label"] == "phishing").astype(int).values
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(df_combined, y)):
        tr_df = df_combined.iloc[train_idx]
        v_df = df_combined.iloc[val_idx]
        
        vec = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
        X_tr = vec.fit_transform(tr_df["text"])
        X_v = vec.transform(v_df["text"])
        
        clf = LogisticRegression(max_iter=500, random_state=SEED)
        clf.fit(X_tr, y[train_idx])
        
        probs = clf.predict_proba(X_v)[:, 1]
        oof_probs[val_idx] = probs
        print(f"  Fold {fold+1}/5 evaluated.")
        
    df_combined["oof_prob_phishing"] = oof_probs
    df_combined["predicted_label"] = np.where(oof_probs >= 0.5, "phishing", "safe")
    df_combined["confidence"] = np.where(oof_probs >= 0.5, oof_probs, 1.0 - oof_probs)
    df_combined["disagreement"] = df_combined["label"] != df_combined["predicted_label"]
    
    high_conf_errors = df_combined[df_combined["disagreement"] & (df_combined["confidence"] >= 0.85)].copy()
    
    print(f"\nOverall OOF Accuracy: {(1 - df_combined['disagreement'].mean()) * 100:.2f}%")
    print(f"Total Disagreements: {df_combined['disagreement'].sum()} / {len(df_combined)} ({df_combined['disagreement'].mean() * 100:.2f}%)")
    print(f"High-Confidence Suspected Noise (confidence >= 0.85): {len(high_conf_errors)} rows ({len(high_conf_errors)/len(df_combined)*100:.2f}%)")
    
    # Save top 30 noise candidates with snippet
    high_conf_errors_sorted = high_conf_errors.sort_values(by="confidence", ascending=False)
    high_conf_errors_sorted["text_snippet"] = high_conf_errors_sorted["text"].str.slice(0, 140).str.replace("\n", " ")
    
    out_cols = ["source", "label", "predicted_label", "confidence", "text_snippet"]
    high_conf_errors_sorted[out_cols].head(50).to_csv("results/oof_label_noise.csv", index=False)
    
    summary = {
        "total_analyzed": len(df_combined),
        "oof_accuracy": float(round((1 - df_combined['disagreement'].mean()) * 100, 2)),
        "total_disagreements": int(df_combined['disagreement'].sum()),
        "disagreement_rate_pct": float(round(df_combined['disagreement'].mean() * 100, 2)),
        "high_confidence_noise_count": int(len(high_conf_errors)),
        "high_confidence_noise_pct": float(round(len(high_conf_errors) / len(df_combined) * 100, 2)),
        "noise_by_source": high_conf_errors["source"].value_counts().to_dict(),
    }
    with open("results/oof_noise_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("OOF noise audit complete. Saved to results/oof_label_noise.csv and results/oof_noise_summary.json")

if __name__ == "__main__":
    main()

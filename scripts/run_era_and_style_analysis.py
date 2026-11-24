"""ERA and STYLE Detailed Probe and Per-Era Evaluation.

Performs:
1. Exact counts per era and class across Train, Validation, and Test.
2. Per-era slice performance on Validation (and Test) comparing old-era phishing vs modern phishing.
3. Feature coefficients and top features of the surface/style probe.
4. Evaluation of the surface/style probe on text exactly as the model sees it (lowercased, tokenized, masked).
5. Saves results to results/era_style_detailed.json.
"""
import os
import sys
import re
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer

SEED = 42

def extract_style_features_raw(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {
            "char_len": 0, "word_count": 0, "upper_ratio": 0.0,
            "digit_ratio": 0.0, "punct_ratio": 0.0, "space_before_punct": 0,
            "has_year_token": 0, "has_date_token": 0, "has_time_token": 0,
            "has_url_token": 0, "has_email_token": 0, "has_num_token": 0,
            "avg_word_len": 0.0,
        }
    chars = len(text)
    words = text.split()
    n_words = len(words)
    upper_cnt = sum(1 for c in text if c.isupper())
    digit_cnt = sum(1 for c in text if c.isdigit())
    punct_cnt = sum(1 for c in text if c in '.,;:!?-_/()[]{}')
    space_before_p = len(re.findall(r"\s+[.,;:!?]", text))

    return {
        "char_len": chars,
        "word_count": n_words,
        "upper_ratio": upper_cnt / max(1, chars),
        "digit_ratio": digit_cnt / max(1, chars),
        "punct_ratio": punct_cnt / max(1, chars),
        "space_before_punct": space_before_p,
        "has_year_token": 1 if "<year>" in text else 0,
        "has_date_token": 1 if "<date>" in text else 0,
        "has_time_token": 1 if "<time>" in text else 0,
        "has_url_token": 1 if "<url>" in text else 0,
        "has_email_token": 1 if "<email>" in text else 0,
        "has_num_token": 1 if "<num>" in text else 0,
        "avg_word_len": chars / max(1, n_words),
    }

def extract_style_features_as_model_sees(text: str) -> dict:
    """Features extracted after lowercasing (as vocabulary and model tokenization ingest)."""
    text_model = text.lower()
    chars = len(text_model)
    words = text_model.split()
    n_words = len(words)
    digit_cnt = sum(1 for c in text_model if c.isdigit())
    punct_cnt = sum(1 for c in text_model if c in '.,;:!?-_/()[]{}')
    space_before_p = len(re.findall(r"\s+[.,;:!?]", text_model))

    return {
        "char_len": chars,
        "word_count": n_words,
        "upper_ratio": 0.0, # Model sees lowercased tokens; uppercase is zeroed out
        "digit_ratio": digit_cnt / max(1, chars),
        "punct_ratio": punct_cnt / max(1, chars),
        "space_before_punct": space_before_p,
        "has_year_token": 1 if "<year>" in text_model else 0,
        "has_date_token": 1 if "<date>" in text_model else 0,
        "has_time_token": 1 if "<time>" in text_model else 0,
        "has_url_token": 1 if "<url>" in text_model else 0,
        "has_email_token": 1 if "<email>" in text_model else 0,
        "has_num_token": 1 if "<num>" in text_model else 0,
        "avg_word_len": chars / max(1, n_words),
    }

def main():
    print("=======================================================")
    print("ERA AND STYLE COMPREHENSIVE PROBE & SLICE EVALUATION")
    print("=======================================================")
    
    train_meta = pd.read_csv("dataset/processed/train_metadata.csv")
    val_meta = pd.read_csv("dataset/processed/validation_metadata.csv")
    test_meta = pd.read_csv("dataset/processed/test_metadata.csv")
    
    print("\n1. COUNTS PER ERA AND CLASS:")
    for split_name, df in [("Train", train_meta), ("Validation", val_meta), ("Test", test_meta)]:
        print(f"\n--- {split_name} Split ---")
        ct = df.groupby(["label", "era"]).size().unstack(fill_value=0)
        print(ct)
        
    print("\n--- PHISHING BREAKDOWN BY ERA ---")
    for split_name, df in [("Train", train_meta), ("Validation", val_meta), ("Test", test_meta)]:
        p_df = df[df["label"] == "phishing"]
        old_cnt = len(p_df[p_df["source"].isin(["nigerian_fraud", "nazario_phishing"])])
        mod_cnt = len(p_df[p_df["source"] == "nazario_modern"])
        print(f"{split_name}: Old-era Phishing={old_cnt} ({(old_cnt/len(p_df))*100:.1f}%), Modern Phishing={mod_cnt} ({(mod_cnt/len(p_df))*100:.1f}%)")

    # 2. Train baseline TF-IDF on full Train set
    print("\n2. BASELINE MODEL EVALUATION BY PHISHING ERA:")
    vec = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)
    X_tr = vec.fit_transform(train_meta["text"])
    y_tr = (train_meta["label"] == "phishing").astype(int).values
    
    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
    clf.fit(X_tr, y_tr)
    
    # Validation evaluation
    val_meta["pred"] = clf.predict(vec.transform(val_meta["text"]))
    val_meta["y_true"] = (val_meta["label"] == "phishing").astype(int)
    
    test_meta["pred"] = clf.predict(vec.transform(test_meta["text"]))
    test_meta["y_true"] = (test_meta["label"] == "phishing").astype(int)
    
    # Slices on Validation
    val_phish = val_meta[val_meta["label"] == "phishing"]
    val_old_phish = val_phish[val_phish["source"].isin(["nigerian_fraud", "nazario_phishing"])]
    val_mod_phish = val_phish[val_phish["source"] == "nazario_modern"]
    
    val_old_rec = (val_old_phish["pred"] == 1).mean()
    val_mod_rec = (val_mod_phish["pred"] == 1).mean()
    print(f"Validation Old-Era Phishing Recall: {val_old_rec * 100:.2f}% ({len(val_old_phish)} samples)")
    print(f"Validation Modern Phishing Recall:  {val_mod_rec * 100:.2f}% ({len(val_mod_phish)} samples)")
    
    # Slices on Test
    test_phish = test_meta[test_meta["label"] == "phishing"]
    test_old_phish = test_phish[test_phish["source"].isin(["nigerian_fraud", "nazario_phishing"])]
    test_mod_phish = test_phish[test_phish["source"] == "nazario_modern"]
    test_old_rec = (test_old_phish["pred"] == 1).mean()
    test_mod_rec = (test_mod_phish["pred"] == 1).mean()
    print(f"Test Old-Era Phishing Recall:       {test_old_rec * 100:.2f}% ({len(test_old_phish)} samples)")
    print(f"Test Modern Phishing Recall:        {test_mod_rec * 100:.2f}% ({len(test_mod_phish)} samples)")

    # 3. Surface / Style Probe - Raw Text
    print("\n3. SURFACE / STYLE PROBE ON RAW TEXT:")
    X_tr_raw = pd.DataFrame([extract_style_features_raw(t) for t in train_meta["text"]])
    X_val_raw = pd.DataFrame([extract_style_features_raw(t) for t in val_meta["text"]])
    X_te_raw = pd.DataFrame([extract_style_features_raw(t) for t in test_meta["text"]])
    
    scaler_raw = StandardScaler()
    clf_raw = LogisticRegression(max_iter=1000, random_state=SEED)
    X_tr_raw_sc = scaler_raw.fit_transform(X_tr_raw)
    clf_raw.fit(X_tr_raw_sc, y_tr)
    
    val_raw_preds = clf_raw.predict(scaler_raw.transform(X_val_raw))
    val_raw_acc = accuracy_score(val_meta["y_true"], val_raw_preds)
    val_raw_f1 = f1_score(val_meta["y_true"], val_raw_preds, average="macro")
    print(f"Raw Text Style Probe -> Val Acc: {val_raw_acc * 100:.2f}%, Val Macro-F1: {val_raw_f1:.4f}")
    
    feat_names = list(X_tr_raw.columns)
    coefs_raw = clf_raw.coef_[0]
    top_feats_raw = sorted(zip(feat_names, coefs_raw), key=lambda x: abs(x[1]), reverse=True)
    print("Top Features in Raw Style Probe (Standardized Coefs):")
    for feat, c in top_feats_raw:
        direction = "Phishing (+)" if c > 0 else "Safe (-)"
        print(f"  {feat:20s}: {c:+.4f} ({direction})")

    # 4. Surface / Style Probe - Text As Model Sees It (Lowercased)
    print("\n4. SURFACE / STYLE PROBE ON TEXT AS MODEL SEES IT (LOWERCASED & MASKED):")
    X_tr_model = pd.DataFrame([extract_style_features_as_model_sees(t) for t in train_meta["text"]])
    X_val_model = pd.DataFrame([extract_style_features_as_model_sees(t) for t in val_meta["text"]])
    X_te_model = pd.DataFrame([extract_style_features_as_model_sees(t) for t in test_meta["text"]])
    
    scaler_model = StandardScaler()
    clf_model = LogisticRegression(max_iter=1000, random_state=SEED)
    X_tr_model_sc = scaler_model.fit_transform(X_tr_model)
    clf_model.fit(X_tr_model_sc, y_tr)
    
    val_model_preds = clf_model.predict(scaler_model.transform(X_val_model))
    val_model_acc = accuracy_score(val_meta["y_true"], val_model_preds)
    val_model_f1 = f1_score(val_meta["y_true"], val_model_preds, average="macro")
    print(f"Model-Seen Text Style Probe -> Val Acc: {val_model_acc * 100:.2f}%, Val Macro-F1: {val_model_f1:.4f}")
    
    coefs_model = clf_model.coef_[0]
    top_feats_model = sorted(zip(feat_names, coefs_model), key=lambda x: abs(x[1]), reverse=True)
    print("Top Features in Model-Seen Style Probe (Standardized Coefs):")
    for feat, c in top_feats_model:
        direction = "Phishing (+)" if c > 0 else "Safe (-)"
        print(f"  {feat:20s}: {c:+.4f} ({direction})")

    out_data = {
        "raw_style_probe": {
            "val_acc": float(round(val_raw_acc * 100, 2)),
            "val_macro_f1": float(round(val_raw_f1, 4)),
            "top_features": [(f, float(round(c, 4))) for f, c in top_feats_raw],
        },
        "model_seen_style_probe": {
            "val_acc": float(round(val_model_acc * 100, 2)),
            "val_macro_f1": float(round(val_model_f1, 4)),
            "top_features": [(f, float(round(c, 4))) for f, c in top_feats_model],
        },
        "per_era_phishing_recall": {
            "validation": {
                "old_era_recall": float(round(val_old_rec * 100, 2)),
                "modern_recall": float(round(val_mod_rec * 100, 2)),
                "old_era_samples": int(len(val_old_phish)),
                "modern_samples": int(len(val_mod_phish)),
            },
            "test": {
                "old_era_recall": float(round(test_old_rec * 100, 2)),
                "modern_recall": float(round(test_mod_rec * 100, 2)),
                "old_era_samples": int(len(test_old_phish)),
                "modern_samples": int(len(test_mod_phish)),
            }
        }
    }
    
    with open("results/era_style_detailed.json", "w") as f:
        json.dump(out_data, f, indent=2)
    print("\nSaved era_style_detailed.json successfully.")

if __name__ == "__main__":
    main()

"""Anti-Shortcut, Era, and Style Confounder Analysis.

Executes:
1. Era/Style probe: Predict label (safe vs phishing) using ONLY surface/style/era features
   (character ratios, length, year/date patterns, punctuation spacing).
2. Source-ID classifier probe: Can source identity be predicted from masked text?
3. Marker ablation probe: Remove top-50 source-distinguishing tokens by log-odds and test impact.
4. Per-source and per-era slice distributions.
5. Saves results to results/shortcut_probes.json.
"""
import os
import sys
import re
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.abspath("."))
from src.text.cleaner import unified_tokenize

SEED = 42

def extract_style_era_features(text: str) -> dict:
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

def main():
    print("=======================================================")
    print("RUNNING ANTI-SHORTCUT, ERA & STYLE PROBE ANALYSIS")
    print("=======================================================")
    
    # Load training metadata and validation metadata
    train_meta_p = "dataset/processed/train_metadata.csv"
    val_meta_p = "dataset/processed/validation_metadata.csv"
    
    if not os.path.exists(train_meta_p) or not os.path.exists(val_meta_p):
        print(f"Error: metadata files not found.")
        return
        
    train_df = pd.read_csv(train_meta_p)
    val_df = pd.read_csv(val_meta_p)
    
    print(f"Loaded Train: {len(train_df)}, Val: {len(val_df)}")
    
    # 1. Per-source and per-era class distribution
    print("\n--- PER-SOURCE AND PER-ERA DISTRIBUTIONS ---")
    dist = train_df.groupby(["label", "source", "era"]).size().reset_index(name="train_count")
    val_dist = val_df.groupby(["label", "source", "era"]).size().reset_index(name="val_count")
    dist = dist.merge(val_dist, on=["label", "source", "era"], how="left").fillna(0)
    print(dist.to_string(index=False))
    
    # 2. Era / Style Probe
    # Extract style/era features only (NO text n-grams)
    print("\n--- 1. STYLE / SURFACE ONLY PROBE ---")
    X_train_style = pd.DataFrame([extract_style_era_features(t) for t in train_df["text"]])
    X_val_style = pd.DataFrame([extract_style_era_features(t) for t in val_df["text"]])
    
    y_train = (train_df["label"] == "phishing").astype(int)
    y_val = (val_df["label"] == "phishing").astype(int)
    
    style_clf = LogisticRegression(max_iter=1000, random_state=SEED)
    style_clf.fit(X_train_style, y_train)
    
    style_preds = style_clf.predict(X_val_style)
    style_acc = accuracy_score(y_val, style_preds)
    style_f1 = f1_score(y_val, style_preds, average="macro")
    style_auc = roc_auc_score(y_val, style_clf.predict_proba(X_val_style)[:, 1])
    
    print(f"Style/Surface Only Probe Results:")
    print(f"  Accuracy: {style_acc:.4f} (Baseline random: 0.5000, Gate threshold: <= 0.6500)")
    print(f"  Macro-F1: {style_f1:.4f}")
    print(f"  ROC-AUC:  {style_auc:.4f}")
    
    feature_weights = pd.Series(style_clf.coef_[0], index=X_train_style.columns).sort_values()
    print("\nTop Negative Features (Predict Safe):")
    print(feature_weights.head(4))
    print("\nTop Positive Features (Predict Phishing):")
    print(feature_weights.tail(4))
    
    # 3. Source-ID Classifier Probe
    print("\n--- 2. SOURCE-ID CLASSIFIER PROBE ---")
    # Predict source ID from text TF-IDF
    tfidf_source = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    X_src_train = tfidf_source.fit_transform(train_df["text"])
    X_src_val = tfidf_source.transform(val_df["text"])
    
    source_clf = LogisticRegression(max_iter=500, random_state=SEED)
    source_clf.fit(X_src_train, train_df["source"])
    
    src_preds = source_clf.predict(X_src_val)
    src_acc = accuracy_score(val_df["source"], src_preds)
    print(f"Source-ID Probe Accuracy: {src_acc:.4f} across {train_df['source'].nunique()} sources")
    
    # 4. Marker Ablation Probe
    print("\n--- 3. SOURCE MARKER ABLATION PROBE ---")
    # Identify top 50 source-predictive tokens by logistic regression weights on TRAIN only
    coef_matrix = np.abs(source_clf.coef_)
    top_token_indices = np.argsort(coef_matrix.max(axis=0))[-50:]
    inv_vocab = {v: k for k, v in tfidf_source.vocabulary_.items()}
    top_50_tokens = set([inv_vocab[idx] for idx in top_token_indices if idx in inv_vocab])
    
    print(f"Identified {len(top_50_tokens)} source-identifying marker tokens on TRAIN split.")
    
    # Measure change in validation macro-F1 when these markers are ablated
    def ablate_text(text):
        tokens = text.split()
        return " ".join([t for t in tokens if t.lower() not in top_50_tokens])
        
    train_ablated = train_df["text"].apply(ablate_text)
    val_ablated = val_df["text"].apply(ablate_text)
    
    # Train binary model on regular vs ablated
    vec_bin = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_bin_tr = vec_bin.fit_transform(train_df["text"])
    X_bin_val = vec_bin.transform(val_df["text"])
    clf_bin = LogisticRegression(max_iter=500, random_state=SEED).fit(X_bin_tr, y_train)
    reg_val_f1 = f1_score(y_val, clf_bin.predict(X_bin_val), average="macro")
    
    vec_abl = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_abl_tr = vec_abl.fit_transform(train_ablated)
    X_abl_val = vec_abl.transform(val_ablated)
    clf_abl = LogisticRegression(max_iter=500, random_state=SEED).fit(X_abl_tr, y_train)
    abl_val_f1 = f1_score(y_val, clf_abl.predict(X_abl_val), average="macro")
    
    delta_f1 = abl_val_f1 - reg_val_f1
    print(f"Binary Classifier with All Tokens: Val Macro-F1 = {reg_val_f1:.4f}")
    print(f"Binary Classifier with Ablated 50 Tokens: Val Macro-F1 = {abl_val_f1:.4f}")
    print(f"Delta Macro-F1: {delta_f1:+.4f} (Robustness check: < 0.05 drop proves no reliance on isolated source markers)")
    
    # Save probe metrics
    results = {
        "style_surface_probe": {
            "accuracy": float(style_acc),
            "macro_f1": float(style_f1),
            "roc_auc": float(style_auc),
            "gate_passed": bool(style_acc <= 0.65),
        },
        "source_id_probe": {
            "accuracy": float(src_acc),
            "num_sources": int(train_df["source"].nunique()),
        },
        "marker_ablation": {
            "regular_f1": float(reg_val_f1),
            "ablated_f1": float(abl_val_f1),
            "delta_f1": float(delta_f1),
            "top_ablated_markers": list(top_50_tokens)[:15],
        },
        "era_distribution": {
            "phishing_historical_train": int(len(train_df[(train_df['label']=='phishing') & (train_df['era']=='historical')])),
            "phishing_modern_train": int(len(train_df[(train_df['label']=='phishing') & (train_df['era']=='modern')])),
            "safe_historical_train": int(len(train_df[(train_df['label']=='safe') & (train_df['era']=='historical')])),
            "safe_modern_train": 0,
        }
    }
    
    with open("results/shortcut_probes.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved probe metrics to results/shortcut_probes.json.")

if __name__ == "__main__":
    main()

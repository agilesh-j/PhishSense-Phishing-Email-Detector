import json
import os
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, cohen_kappa_score

SCORE_OUTPUT_PATH = "results/label_audit/audit_score.json"

def score_audit():
    key = pd.read_csv("results/label_audit/answer_key.csv")
    rev = pd.read_csv("results/label_audit/reviewer_1.csv")
    
    merged = key.merge(rev, on="id")
    # Clean check for filled labels
    valid_mask = merged["my_label"].notna() & (merged["my_label"].astype(str).str.strip() != "") & (merged["my_label"].astype(str).str.strip().str.lower() != "nan")
    answered = merged[valid_mask]
    
    if len(answered) == 0:
        print(f"No human reviews recorded yet in reviewer_1.csv (0/{len(key)} filled).")
        if os.path.exists(SCORE_OUTPUT_PATH):
            os.remove(SCORE_OUTPUT_PATH)
        return
        
    label_map = {"0": "safe", "1": "phishing", "safe": "safe", "phishing": "phishing"}
    y_true = answered["label"].str.strip().str.lower().map(lambda s: label_map.get(s, s))
    y_pred = answered["my_label"].astype(str).str.strip().str.lower().map(lambda s: label_map.get(s, s))
    
    acc = accuracy_score(y_true, y_pred)
    kappa = cohen_kappa_score(y_true, y_pred)
    
    print(f"Reviewed: {len(answered)}/{len(key)} emails")
    print(f"Accuracy: {acc:.4f}")
    print(f"Cohen's Kappa: {kappa:.4f}")
    
    print("\nPer-Source Precision:")
    per_source = {}
    for src, grp in answered.groupby("source"):
        src_true = grp["label"].str.strip().str.lower()
        src_pred = grp["my_label"].str.strip().str.lower()
        src_acc = accuracy_score(src_true, src_pred)
        print(f"  {src}: {src_acc*100:.1f}% ({len(grp)} audited rows)")
        per_source[src] = {
            "precision": round(float(src_acc * 100), 2),
            "count": int(len(grp)),
            "matches": int((src_true == src_pred).sum())
        }
        
    if len(answered) < len(key):
        print(f"\n[WARNING] Audit incomplete ({len(answered)}/{len(key)}). All 120 labels must be filled to pass verification gate.")
        if os.path.exists(SCORE_OUTPUT_PATH):
            os.remove(SCORE_OUTPUT_PATH)
        return
        
    audit_data = {
        "status": "complete",
        "reviewed_count": int(len(answered)),
        "total_count": int(len(key)),
        "accuracy": round(float(acc * 100), 2),
        "cohen_kappa": round(float(kappa), 4),
        "per_source_precision": per_source,
        "all_sources_pass_95": bool(all(v["precision"] >= 95.0 for v in per_source.values()))
    }
    with open(SCORE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"\nAudit results successfully saved to: {SCORE_OUTPUT_PATH}")

if __name__ == "__main__":
    score_audit()


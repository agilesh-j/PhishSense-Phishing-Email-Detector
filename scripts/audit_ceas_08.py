"""Vetting and audit script for CEAS_08.csv.
Measures:
1. Pharmacy/commercial spam share before screening.
2. Screening with cleaner.py and label guidelines (length, commercial spam exclusion, borderline quarantine).
3. Pharmacy/commercial spam share after screening.
4. Stratified audit of 100 safe and 100 phishing rows to calculate precision against label guidelines.
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import re
import json
import random
import pandas as pd
from src.text.cleaner import clean_email_text, classify_content_status

# Extended pharmacy & commercial regex for pre/post measurement
PHARMACY_PATTERNS = re.compile(
    r"\b(viagra|cialis|levitra|soma|phentermine|vicodin|xanax|valium|ambien|propecia|"
    r"pharmacy|canadian pharmacy|prescriptions? without|pills?|meds?|erectile dysfunction|"
    r"herbal|weight loss|fat burner)\b",
    re.IGNORECASE,
)

COMMERCIAL_SPAM_PATTERNS = re.compile(
    r"\b(replica watches|rolex replica|casino|poker|free spins|online slot|lottery win|"
    r"lowest mortgage|refinance now|debt consolidation|pre-approved loan|"
    r"seo services|email blast|cheap leads|target stock alert|penny stock)\b",
    re.IGNORECASE,
)

def is_pharmacy_or_commercial(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return bool(PHARMACY_PATTERNS.search(text) or COMMERCIAL_SPAM_PATTERNS.search(text))

def main():
    csv_path = "dataset/raw/ceas_08/CEAS_08.csv"
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    total_raw = len(df)
    print(f"Total raw rows: {total_raw}")
    print("Raw label counts:\n", df["label"].value_counts().to_dict())

    # Pre-screening analysis
    df["raw_text"] = df["subject"].fillna("").astype(str) + "\n" + df["body"].fillna("").astype(str)
    
    pharmacy_or_comm_raw = df["raw_text"].apply(is_pharmacy_or_commercial)
    raw_spam_mask = (df["label"] == 1)
    raw_ham_mask = (df["label"] == 0)

    raw_spam_comm = pharmacy_or_comm_raw[raw_spam_mask].sum()
    raw_ham_comm = pharmacy_or_comm_raw[raw_ham_mask].sum()

    print("\n--- PRE-SCREENING PHARMACY / COMMERCIAL SPAM SHARE ---")
    print(f"Class 1 (Spam/Phish): {raw_spam_comm} / {raw_spam_mask.sum()} ({raw_spam_comm / raw_spam_mask.sum() * 100:.2f}%)")
    print(f"Class 0 (Ham/Safe):   {raw_ham_comm} / {raw_ham_mask.sum()} ({raw_ham_comm / raw_ham_mask.sum() * 100:.2f}%)")
    print(f"Total Combined:       {pharmacy_or_comm_raw.sum()} / {total_raw} ({pharmacy_or_comm_raw.sum() / total_raw * 100:.2f}%)")

    # Run screening
    print("\nScreening rows with cleaner & label guidelines...")
    cleaned_records = []
    quarantined_records = []
    excluded_records = []

    for idx, row in df.iterrows():
        raw_t = row["raw_text"]
        lbl = int(row["label"])
        status, reason = classify_content_status(raw_t)
        
        if status == "valid":
            cleaned_t = clean_email_text(raw_t)
            post_status, post_reason = classify_content_status(cleaned_t)
            if post_status == "valid":
                cleaned_records.append({
                    "orig_idx": idx,
                    "label": lbl,
                    "cleaned_text": cleaned_t,
                    "word_count": len(cleaned_t.split()),
                })
            elif post_status == "borderline_quarantine":
                quarantined_records.append({"orig_idx": idx, "label": lbl, "reason": post_reason, "text": cleaned_t[:200]})
            else:
                excluded_records.append({"orig_idx": idx, "label": lbl, "reason": post_reason})
        elif status == "borderline_quarantine":
            quarantined_records.append({"orig_idx": idx, "label": lbl, "reason": reason, "text": raw_t[:200]})
        else:
            excluded_records.append({"orig_idx": idx, "label": lbl, "reason": reason})

    clean_df = pd.DataFrame(cleaned_records)
    print(f"\n--- SCREENING RESULTS ---")
    print(f"Accepted clean rows:     {len(clean_df)} / {total_raw} ({len(clean_df) / total_raw * 100:.2f}%)")
    print(f"Quarantined borderline:  {len(quarantined_records)}")
    print(f"Excluded (spam/short):   {len(excluded_records)}")
    
    print("\nPost-screening label distribution in accepted pool:")
    post_label_counts = clean_df["label"].value_counts().to_dict()
    print(post_label_counts)

    # Post-screening pharmacy/commercial spam share
    clean_pharm_comm = clean_df["cleaned_text"].apply(is_pharmacy_or_commercial)
    clean_spam_mask = (clean_df["label"] == 1)
    clean_ham_mask = (clean_df["label"] == 0)

    post_spam_comm = clean_pharm_comm[clean_spam_mask].sum()
    post_ham_comm = clean_pharm_comm[clean_ham_mask].sum()

    print("\n--- POST-SCREENING PHARMACY / COMMERCIAL SPAM SHARE ---")
    print(f"Class 1 (Spam/Phish): {post_spam_comm} / {clean_spam_mask.sum()} ({post_spam_comm / clean_spam_mask.sum() * 100:.2f}%)")
    print(f"Class 0 (Ham/Safe):   {post_ham_comm} / {clean_ham_mask.sum()} ({post_ham_comm / clean_ham_mask.sum() * 100:.2f}%)")
    print(f"Total Combined:       {clean_pharm_comm.sum()} / {len(clean_df)} ({clean_pharm_comm.sum() / len(clean_df) * 100:.2f}%)")

    # Stratified Audit of 100 rows per class
    print("\n--- AUDITING 100 ROWS PER CLASS ---")
    random.seed(42)
    sample_ham = clean_df[clean_df["label"] == 0].sample(n=100, random_state=42)
    sample_phish = clean_df[clean_df["label"] == 1].sample(n=100, random_state=42)

    # Audit Safe Class
    # In Safe Class: true positive if benign authentic personal/work communication (not spam, not phishing)
    ham_valid_count = 0
    ham_invalid = []
    for _, r in sample_ham.iterrows():
        t = r["cleaned_text"].lower()
        # Check if false negative (is actually phish or commercial spam)
        is_phish = any(k in t for k in ["verify your account", "urgent: update", "suspended account", "confirm password", "wire transfer"])
        is_spam = is_pharmacy_or_commercial(t)
        if not is_phish and not is_spam:
            ham_valid_count += 1
        else:
            ham_invalid.append((r["orig_idx"], "phish" if is_phish else "spam", t[:100]))

    ham_precision = ham_valid_count / 100.0 * 100.0
    print(f"Safe Class (label 0) Audit: {ham_valid_count} / 100 valid safe emails ({ham_precision:.1f}% precision)")

    # Audit Phishing Class
    # In Phishing Class: true positive if deceptive credential theft, financial fraud, impersonation, fake alerts
    # In CEAS 08, many spam emails are newsletter spam, product offers, discount coupons, or junk mail that are NOT phishing
    phish_valid_count = 0
    phish_invalid = []
    phish_cues = [
        "account", "password", "security", "update", "verify", "suspended", "login",
        "bank", "paypal", "ebay", "irs", "tax", "wire", "transfer", "western union",
        "beneficiary", "inheritance", "fund", "urgent", "access", "invoice", "payment",
        "billing", "card", "expire", "ssn", "compromised", "identity", "unauthorized",
    ]
    for _, r in sample_phish.iterrows():
        t = r["cleaned_text"].lower()
        has_phish_intent = any(k in t for k in phish_cues)
        # Check if it's mere marketing/product sales
        is_pure_marketing = any(k in t for k in ["discount code", "shop now", "free shipping", "clearance sale", "gift certificate"])
        if has_phish_intent and not is_pure_marketing:
            phish_valid_count += 1
        else:
            phish_invalid.append((r["orig_idx"], "marketing_or_generic_spam", t[:100]))

    phish_precision = phish_valid_count / 100.0 * 100.0
    print(f"Phishing Class (label 1) Audit: {phish_valid_count} / 100 meet phishing deception criteria ({phish_precision:.1f}% precision)")

    audit_summary = {
        "ceas_08_total_raw": total_raw,
        "raw_label_counts": df["label"].value_counts().to_dict(),
        "pre_screening_pharmacy_comm_spam_pct": {
            "class_1": float(raw_spam_comm / raw_spam_mask.sum() * 100),
            "class_0": float(raw_ham_comm / raw_ham_mask.sum() * 100),
            "combined": float(pharmacy_or_comm_raw.sum() / total_raw * 100),
        },
        "post_screening_clean_rows": len(clean_df),
        "post_screening_label_counts": post_label_counts,
        "post_screening_pharmacy_comm_spam_pct": {
            "class_1": float(post_spam_comm / clean_spam_mask.sum() * 100),
            "class_0": float(post_ham_comm / clean_ham_mask.sum() * 100),
            "combined": float(clean_pharm_comm.sum() / len(clean_df) * 100),
        },
        "safe_class_precision_pct": ham_precision,
        "phishing_class_precision_pct": phish_precision,
        "passes_95_pct_threshold": (ham_precision >= 95.0 and phish_precision >= 95.0),
    }

    os.makedirs("results", exist_ok=True)
    with open("results/ceas_08_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print("\nSaved results to results/ceas_08_audit.json")

if __name__ == "__main__":
    main()

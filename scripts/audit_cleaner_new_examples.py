"""Re-run cleaning audit across all sources and generate 5 new random masked examples per source."""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import random
import glob
import pandas as pd
from src.text.cleaner import clean_email_text, classify_content_status

random.seed(42)

def audit_source_examples():
    results = {}
    
    # 1. Enron Clean (Safe)
    enron_df = pd.read_csv("dataset/raw/enron_clean/Enron.csv")
    enron_safe = enron_df[enron_df["label"] == 0]
    enron_samples = []
    indices = list(range(len(enron_safe)))
    random.shuffle(indices)
    for idx in indices:
        row = enron_safe.iloc[idx]
        raw_text = f"{row['subject']}\n{row['body']}"
        cleaned = clean_email_text(raw_text)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            enron_samples.append({
                "source": "enron_clean",
                "label": "safe",
                "orig_idx": idx,
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(enron_samples) == 5:
                break
    results["enron_clean"] = enron_samples

    # 2. Nigerian Fraud (Phishing)
    nig_df = pd.read_csv("dataset/raw/nigerian_fraud/Nigerian_Fraud.csv")
    nig_samples = []
    indices = list(range(len(nig_df)))
    random.shuffle(indices)
    for idx in indices:
        row = nig_df.iloc[idx]
        raw_text = f"{row['subject']}\n{row['body']}"
        cleaned = clean_email_text(raw_text)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            nig_samples.append({
                "source": "nigerian_fraud",
                "label": "phishing",
                "orig_idx": idx,
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(nig_samples) == 5:
                break
    results["nigerian_fraud"] = nig_samples

    # 3. Nazario Phishing (Phishing)
    naz_df = pd.read_csv("dataset/raw/nazario_phishing/Nazario.csv")
    naz_samples = []
    indices = list(range(len(naz_df)))
    random.shuffle(indices)
    for idx in indices:
        row = naz_df.iloc[idx]
        raw_text = f"{row['subject']}\n{row['body']}"
        cleaned = clean_email_text(raw_text)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            naz_samples.append({
                "source": "nazario_phishing",
                "label": "phishing",
                "orig_idx": idx,
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(naz_samples) == 5:
                break
    results["nazario_phishing"] = naz_samples

    # 4. SpamAssassin Hard Ham (Safe)
    hh_files = glob.glob("dataset/raw/spamassassin_hard_ham/extracted/**/*", recursive=True)
    hh_files = [f for f in hh_files if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md")]
    random.shuffle(hh_files)
    hh_samples = []
    for f in hh_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        parts = content.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        cleaned = clean_email_text(body)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            hh_samples.append({
                "source": "spamassassin_hard_ham",
                "label": "safe",
                "file": os.path.basename(f),
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(hh_samples) == 5:
                break
    results["spamassassin_hard_ham"] = hh_samples

    # 5. SpamAssassin Easy Ham (Safe)
    eh_files = glob.glob("dataset/raw/spamassassin_easy_ham/extracted*/**/*", recursive=True)
    eh_files = [f for f in eh_files if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md")]
    random.shuffle(eh_files)
    eh_samples = []
    for f in eh_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        parts = content.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        cleaned = clean_email_text(body)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            eh_samples.append({
                "source": "spamassassin_easy_ham",
                "label": "safe",
                "file": os.path.basename(f),
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(eh_samples) == 5:
                break
    results["spamassassin_easy_ham"] = eh_samples

    # 6. Reference Dataset (Safe and Phishing)
    ref_df = pd.read_csv("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")
    ref_safe = ref_df[ref_df["Email Type"] == "Safe Email"]
    ref_phish = ref_df[ref_df["Email Type"] == "Phishing Email"]
    
    ref_safe_samples = []
    safe_indices = list(range(len(ref_safe)))
    random.shuffle(safe_indices)
    for idx in safe_indices:
        raw_text = str(ref_safe.iloc[idx]["Email Text"])
        cleaned = clean_email_text(raw_text)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            ref_safe_samples.append({
                "source": "reference_safe",
                "label": "safe",
                "orig_idx": idx,
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(ref_safe_samples) == 5:
                break
    results["reference_safe"] = ref_safe_samples

    ref_phish_samples = []
    phish_indices = list(range(len(ref_phish)))
    random.shuffle(phish_indices)
    for idx in phish_indices:
        raw_text = str(ref_phish.iloc[idx]["Email Text"])
        cleaned = clean_email_text(raw_text)
        st, _ = classify_content_status(cleaned)
        if st == "valid":
            ref_phish_samples.append({
                "source": "reference_phishing",
                "label": "phishing",
                "orig_idx": idx,
                "text": cleaned[:300] + ("..." if len(cleaned) > 300 else "")
            })
            if len(ref_phish_samples) == 5:
                break
    results["reference_phishing"] = ref_phish_samples

    os.makedirs("results", exist_ok=True)
    with open("results/cleaner_audit_examples.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Successfully generated 5 random masked examples per source.")
    for src, items in results.items():
        print(f"\n=================== {src} ({len(items)} examples) ===================")
        for i, it in enumerate(items, 1):
            print(f"[{i}] {it['text']}")

if __name__ == "__main__":
    audit_source_examples()

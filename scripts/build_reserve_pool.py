"""Build results/reserve_pool.csv for Gate B audit repairs.
Stores qualified clean rows that were not selected for the 8,000 tier.
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import glob
import pandas as pd
from src.text.cleaner import clean_email_text, classify_content_status

def main():
    print("Building Reserve Pool (results/reserve_pool.csv)...")
    
    # 8,000 Tier Allocations:
    # Safe: Ref 1000, Enron 1600, SpamAssassin 1400
    # Phish: Ref 1000, Nigerian 1600, Nazario 1400
    
    reserve_rows = []
    
    # 1. Enron Safe (keep rows from index 1600 onward)
    print("Processing Enron...")
    enron_df = pd.read_csv("dataset/raw/enron_clean/Enron.csv")
    enron_safe = enron_df[enron_df["label"] == 0]
    count = 0
    for idx, r in enron_safe.iterrows():
        t = clean_email_text(f"{r['subject']}\n{r['body']}")
        st, _ = classify_content_status(t)
        if st == "valid":
            count += 1
            if count > 1600:
                reserve_rows.append({
                    "source_id": "enron_clean",
                    "orig_index": idx,
                    "label": "safe",
                    "cleaned_text": t
                })

    # 2. SpamAssassin Easy Ham (keep rows from index 1400 onward)
    print("Processing SpamAssassin Easy Ham...")
    eh_files = glob.glob("dataset/raw/spamassassin_easy_ham/extracted*/**/*", recursive=True)
    eh_files = [f for f in eh_files if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md")]
    count = 0
    for f in eh_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        parts = content.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        t = clean_email_text(body)
        st, _ = classify_content_status(t)
        if st == "valid":
            count += 1
            if count > 1400:
                reserve_rows.append({
                    "source_id": "spamassassin_easy_ham",
                    "orig_index": os.path.basename(f),
                    "label": "safe",
                    "cleaned_text": t
                })

    # 3. Nigerian Fraud (keep rows from index 1600 onward)
    print("Processing Nigerian Fraud...")
    nig_df = pd.read_csv("dataset/raw/nigerian_fraud/Nigerian_Fraud.csv")
    count = 0
    for idx, r in nig_df.iterrows():
        t = clean_email_text(f"{r['subject']}\n{r['body']}")
        st, _ = classify_content_status(t)
        if st == "valid":
            count += 1
            if count > 1600:
                reserve_rows.append({
                    "source_id": "nigerian_fraud",
                    "orig_index": idx,
                    "label": "phishing",
                    "cleaned_text": t
                })

    # 4. Nazario Phishing (keep rows from index 1400 onward)
    print("Processing Nazario Phishing...")
    naz_df = pd.read_csv("dataset/raw/nazario_phishing/Nazario.csv")
    count = 0
    for idx, r in naz_df.iterrows():
        t = clean_email_text(f"{r['subject']}\n{r['body']}")
        st, _ = classify_content_status(t)
        if st == "valid":
            count += 1
            if count > 1400:
                reserve_rows.append({
                    "source_id": "nazario_phishing",
                    "orig_index": idx,
                    "label": "phishing",
                    "cleaned_text": t
                })

    # 5. Reference Dataset Safe and Phish (keep rows from index 1000 onward)
    print("Processing Reference Dataset...")
    ref_df = pd.read_csv("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")
    safe_count = 0
    phish_count = 0
    for idx, r in ref_df.iterrows():
        lbl_raw = str(r["Email Type"])
        t = clean_email_text(str(r["Email Text"]))
        st, _ = classify_content_status(t)
        if st == "valid":
            if lbl_raw == "Safe Email":
                safe_count += 1
                if safe_count > 1000:
                    reserve_rows.append({
                        "source_id": "reference_safe",
                        "orig_index": idx,
                        "label": "safe",
                        "cleaned_text": t
                    })
            elif lbl_raw == "Phishing Email":
                phish_count += 1
                if phish_count > 1000:
                    reserve_rows.append({
                        "source_id": "reference_phishing",
                        "orig_index": idx,
                        "label": "phishing",
                        "cleaned_text": t
                    })

    reserve_df = pd.DataFrame(reserve_rows)
    os.makedirs("results", exist_ok=True)
    reserve_path = "results/reserve_pool.csv"
    reserve_df.to_csv(reserve_path, index=False)
    print(f"\nSuccessfully wrote {len(reserve_df)} reserve rows to {reserve_path}!")
    print(reserve_df["source_id"].value_counts())

if __name__ == "__main__":
    main()

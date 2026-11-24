"""Audit and ingest SpamAssassin easy_ham and easy_ham_2."""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import glob
from src.text.cleaner import clean_email_text, classify_content_status
import pandas as pd

def parse_rfc822_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return ""
    # Split header and body
    parts = content.split("\n\n", 1)
    if len(parts) > 1:
        return parts[1]
    parts = content.split("\r\n\r\n", 1)
    if len(parts) > 1:
        return parts[1]
    return content

def audit_directory(base_dir, name):
    files = [f for f in glob.glob(os.path.join(base_dir, "**", "*"), recursive=True) if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md") and not f.endswith(".txt")]
    print(f"[{name}] Found {len(files)} files.")
    
    records = []
    status_counts = {}
    
    for f in files:
        body = parse_rfc822_file(f)
        cleaned = clean_email_text(body)
        status, reason = classify_content_status(cleaned)
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "valid":
            records.append({
                "filepath": f,
                "cleaned_text": cleaned,
                "words": len(cleaned.split()),
            })
            
    print(f"[{name}] Status counts: {status_counts}")
    print(f"[{name}] Clean valid rows: {len(records)} / {len(files)} ({len(records) / max(1, len(files)) * 100:.2f}%)")
    return records

def main():
    dir_1 = "dataset/raw/spamassassin_easy_ham/extracted_spamassassin_easy_ham"
    dir_2 = "dataset/raw/spamassassin_easy_ham/extracted_spamassassin_easy_ham_2"
    
    rec_1 = audit_directory(dir_1, "easy_ham")
    rec_2 = audit_directory(dir_2, "easy_ham_2")
    
    total_valid = len(rec_1) + len(rec_2)
    print(f"\nTotal SpamAssassin easy_ham valid safe rows: {total_valid}")

if __name__ == "__main__":
    main()

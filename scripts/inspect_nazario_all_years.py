import os, sys, mailbox
sys.path.insert(0, os.path.abspath("."))
from src.text.cleaner import parse_mbox_message, clean_email_text, validate_email_row

MODERN_DIR = "dataset/raw/nazario_modern"
years = [str(y) for y in range(2015, 2026)]

total_valid = 0
per_year = {}

for y in years:
    mbox_path = os.path.join(MODERN_DIR, f"phishing-{y}.mbox")
    if not os.path.exists(mbox_path):
        continue
    
    mb = mailbox.mbox(mbox_path)
    count = 0
    valid_count = 0
    for msg in mb:
        count += 1
        raw_body = parse_mbox_message(msg)
        cleaned = clean_email_text(raw_body)
        is_val, _ = validate_email_row(cleaned, "phishing")
        if is_val:
            valid_count += 1
            
    per_year[y] = {"total_messages": count, "valid_cleaned": valid_count}
    total_valid += valid_count
    print(f"Year {y}: {count} total msgs, {valid_count} valid cleaned emails")

print(f"\nTotal Nazario Modern Valid Cleaned: {total_valid}")

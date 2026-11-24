"""Operational definition and measurement of Hard Negatives.

Operational Rule (documented in docs/LABEL_GUIDELINES.md):
A safe email (label 0) is classified as a 'Hard Negative' iff it contains:
1. Urgent tone / action cues ('urgent', 'immediately', 'action required', 'attention', 'deadline', 'notice', 'important')
   OR
2. Account / credential cues ('account', 'password', 'login', 'security', 'verify', 'verification', 'authentication', 'access')
   OR
3. Transactional / financial cues ('payment', 'invoice', 'wire', 'transfer', 'billing', 'statement', 'receipt', 'card', 'bank')
   OR
4. Security / system alerts ('suspended', 'unauthorized', 'reset', 'update your', 'confirm your', 'attached', 'attachment')
AND it contains at least one link or action directive ('<url>', 'click', 'please visit', 'log in', 'review', 'download').
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import re
import pandas as pd
from src.text.cleaner import clean_email_text, classify_content_status

HARD_NEGATIVE_CUES = re.compile(
    r"\b(urgent|urgently|immediate|immediately|action required|deadline|important notice|"
    r"account|password|passcode|login|log-in|security|verify|verification|confirm|confirming|"
    r"payment|wire|transfer|invoice|billing|statement|receipt|bank|funds|balance|"
    r"suspended|suspension|reset|compromised|unauthorized|attachment|attached file)\b",
    re.IGNORECASE
)

ACTION_DIRECTIVE_CUES = re.compile(
    r"(?:<url>|\b(click|please visit|log in|log into|sign in|review the attached|download|verify here)\b)",
    re.IGNORECASE
)

def is_hard_negative(cleaned_text: str) -> bool:
    if not isinstance(cleaned_text, str):
        return False
    # Must have both phishing surface cues AND an action/link directive
    has_cue = bool(HARD_NEGATIVE_CUES.search(cleaned_text))
    has_action = bool(ACTION_DIRECTIVE_CUES.search(cleaned_text))
    return has_cue and has_action

def main():
    print("Loading safe sources to measure true Hard Negatives...")
    
    # 1. Enron Clean
    enron_df = pd.read_csv("dataset/raw/enron_clean/Enron.csv")
    enron_safe = enron_df[enron_df["label"] == 0]
    enron_texts = [f"{r['subject']}\n{r['body']}" for _, r in enron_safe.iterrows()]
    
    enron_clean_valid = []
    enron_hn_count = 0
    for t in enron_texts:
        c = clean_email_text(t)
        st, _ = classify_content_status(c)
        if st == "valid":
            enron_clean_valid.append(c)
            if is_hard_negative(c):
                enron_hn_count += 1
                
    print(f"\n--- ENRON SAFE EMAILS ---")
    print(f"Clean valid: {len(enron_clean_valid)}")
    print(f"Hard negatives qualifying: {enron_hn_count} / {len(enron_clean_valid)} ({enron_hn_count / len(enron_clean_valid) * 100:.2f}%)")
    
    # 2. SpamAssassin hard_ham
    # By definition, SpamAssassin hard_ham consists of safe emails specifically selected by SpamAssassin maintainers because they trigger spam/phish filters (HTML, tables, transactional terms)
    # Let's count how many pass
    import glob
    hh_files = glob.glob("dataset/raw/spamassassin_hard_ham/extracted/**/*", recursive=True)
    hh_files = [f for f in hh_files if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md")]
    hh_clean_valid = []
    hh_hn_count = 0
    for f in hh_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        parts = content.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        c = clean_email_text(body)
        st, _ = classify_content_status(c)
        if st == "valid":
            hh_clean_valid.append(c)
            if is_hard_negative(c):
                hh_hn_count += 1
                
    print(f"\n--- SPAMASSASSIN HARD_HAM ---")
    print(f"Clean valid: {len(hh_clean_valid)}")
    print(f"Hard negatives qualifying: {hh_hn_count} / {len(hh_clean_valid)} ({hh_hn_count / len(hh_clean_valid) * 100:.2f}%)")

    # 3. SpamAssassin easy_ham
    eh_files = glob.glob("dataset/raw/spamassassin_easy_ham/extracted*/**/*", recursive=True)
    eh_files = [f for f in eh_files if os.path.isfile(f) and not f.endswith(".bz2") and not f.endswith(".md")]
    eh_clean_valid = []
    eh_hn_count = 0
    for f in eh_files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        parts = content.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        c = clean_email_text(body)
        st, _ = classify_content_status(c)
        if st == "valid":
            eh_clean_valid.append(c)
            if is_hard_negative(c):
                eh_hn_count += 1

    print(f"\n--- SPAMASSASSIN EASY_HAM ---")
    print(f"Clean valid: {len(eh_clean_valid)}")
    print(f"Hard negatives qualifying: {eh_hn_count} / {len(eh_clean_valid)} ({eh_hn_count / len(eh_clean_valid) * 100:.2f}%)")

    # Combined safe pool summary
    total_safe_valid = len(enron_clean_valid) + len(hh_clean_valid) + len(eh_clean_valid)
    total_hn = enron_hn_count + hh_hn_count + eh_hn_count
    pct_total_hn = total_hn / total_safe_valid * 100
    print(f"\n--- COMBINED SAFE POOL HARD NEGATIVE TOTALS ---")
    print(f"Total safe valid emails: {total_safe_valid}")
    print(f"Total qualifying Hard Negatives: {total_hn} ({pct_total_hn:.2f}%)")

if __name__ == "__main__":
    main()

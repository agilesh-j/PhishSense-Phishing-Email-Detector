"""Audit Jose Nazario modern phishing mbox files."""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import mailbox
from bs4 import BeautifulSoup
from src.text.cleaner import clean_email_text, classify_content_status

def extract_body_from_msg(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition", ""))
            if "attachment" not in cdispo:
                if ctype == "text/plain":
                    p = part.get_payload(decode=True)
                    if p:
                        body = p.decode("utf-8", errors="ignore")
                        break
                elif ctype == "text/html" and not body:
                    p = part.get_payload(decode=True)
                    if p:
                        body = p.decode("utf-8", errors="ignore")
    else:
        p = msg.get_payload(decode=True)
        if p:
            body = p.decode("utf-8", errors="ignore")
    return body

def main():
    mbox_path = "dataset/raw/nazario_modern/phishing-2021.mbox"
    if not os.path.exists(mbox_path):
        print(f"File not found: {mbox_path}")
        return
    
    mbox = mailbox.mbox(mbox_path)
    print(f"Total raw messages in {mbox_path}: {len(mbox)}")
    
    valid_records = []
    status_counts = {}
    
    for i, msg in enumerate(mbox):
        subj = msg.get("subject", "")
        body = extract_body_from_msg(msg)
        text = f"{subj}\n{body}".strip()
        cleaned = clean_email_text(text)
        status, reason = classify_content_status(cleaned)
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "valid":
            valid_records.append({
                "index": i,
                "subject": subj,
                "cleaned_text": cleaned,
                "words": len(cleaned.split()),
            })
            
    print("Status counts:", status_counts)
    print(f"Valid clean phishing rows: {len(valid_records)} / {len(mbox)}")
    if valid_records:
        print("\nSample clean modern phishing email:")
        sample = valid_records[0]
        print(f"Subject: {sample['subject']}")
        print(f"Cleaned snippet: {sample['cleaned_text'][:300]}")

if __name__ == "__main__":
    main()

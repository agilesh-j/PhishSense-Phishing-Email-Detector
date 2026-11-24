import mailbox
import email
from email import policy

mbox_path = 'dataset/raw/nazario_modern/phishing-2021.mbox'
mbox = mailbox.mbox(mbox_path)
print(f"Total messages in {mbox_path}: {len(mbox)}")

for i in range(min(10, len(mbox))):
    msg = mbox[i]
    date = msg.get('date', 'Unknown')
    from_ = msg.get('from', 'Unknown')
    subj = msg.get('subject', 'Unknown')
    print(f"\n--- Message {i} ---")
    print(f"Date: {date}")
    print(f"From: {from_}")
    print(f"Subject: {subj}")
    
    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode('utf-8', errors='ignore')
    
    print(f"Body snippet (first 150 chars): {repr(body[:150])}")

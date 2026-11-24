import os, sys
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import random
from src.text.cleaner import clean_email_text, classify_content_status

random.seed(42)

df = pd.read_csv("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")
phish = df[df["Email Type"] == "Phishing Email"].copy()
phish = phish.dropna(subset=["Email Text"])

# Sample 60 rows
sampled = phish.sample(n=60, random_state=42).copy()
sampled["cleaned_text"] = sampled["Email Text"].apply(clean_email_text)
sampled["content_status"], sampled["reason"] = zip(*sampled["cleaned_text"].apply(classify_content_status))

# Check for commercial spam vs true phishing
# True phishing: social engineering, deceptive pretexts, identity spoofing, credential theft
# Commercial spam: marketing, pharmacy, dating, products without spoofing
results = []
true_phish_count = 0

for idx, row in sampled.iterrows():
    c_text = row["cleaned_text"]
    status = row["content_status"]
    reason = row["reason"]
    
    # Assess if true phishing or spam
    is_spam = status in ["commercial_spam_excluded", "borderline_quarantined"] or "viagra" in c_text.lower() or "free gift" in c_text.lower() or "hot singles" in c_text.lower()
    label_eval = "commercial_spam" if is_spam else "phishing"
    if label_eval == "phishing" and len(c_text.split()) >= 15:
        true_phish_count += 1
        
    results.append({
        "row_id": idx,
        "original_text_snippet": row["Email Text"][:120].replace("\n", " "),
        "cleaned_snippet": c_text[:120].replace("\n", " "),
        "content_status": status,
        "evaluated_label": label_eval,
        "reason": reason
    })

audit_df = pd.DataFrame(results)
audit_df.to_csv("results/reference_phishing_audit.csv", index=False)

precision = true_phish_count / len(sampled)
print(f"Audited 60 Reference Phishing rows:")
print(f"True Phishing: {true_phish_count}/{len(sampled)} ({precision:.1%})")
print(f"Commercial Spam / Bad: {len(sampled) - true_phish_count}/{len(sampled)}")
print(f"Audit precision >= 95%: {precision >= 0.95}")

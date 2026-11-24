"""Measure exact and near-duplicate overlap between:
1. Reference dataset (Phishing_Email.csv) 'Safe Email' rows
2. Enron.csv safe rows
"""
import hashlib
import re
import pandas as pd
from datasketch import MinHash, MinHashLSH

def normalize_text_for_hash(text):
    if not isinstance(text, str):
        return ""
    # Lowercase and normalize whitespace
    t = re.sub(r'\s+', ' ', text.strip().lower())
    return t

def get_shingles(text, k=5):
    words = text.split()
    if len(words) < k:
        return [text] if text else []
    return [" ".join(words[i:i+k]) for i in range(len(words) - k + 1)]

def main():
    print("Loading Reference dataset (Phishing_Email.csv)...")
    ref_df = pd.read_csv("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")
    # Identify safe rows
    # Phishing_Email.csv has 'Email Text' and 'Email Type' ('Safe Email', 'Phishing Email')
    ref_safe = ref_df[ref_df["Email Type"] == "Safe Email"].copy()
    print(f"Total Reference 'Safe Email' rows: {len(ref_safe)}")

    print("Loading Enron.csv...")
    enron_df = pd.read_csv("dataset/raw/enron_clean/Enron.csv")
    # Enron.csv has 'Subject', 'Body', 'Label' (0 for ham)
    enron_safe = enron_df[enron_df["label"] == 0].copy()
    print(f"Total Enron safe rows (label == 0): {len(enron_safe)}")

    # Combine subject and body for enron
    enron_texts = []
    for _, row in enron_safe.iterrows():
        s = str(row["subject"]) if pd.notna(row["subject"]) else ""
        b = str(row["body"]) if pd.notna(row["body"]) else ""
        text = f"{s}\n{b}".strip() if s else b.strip()
        enron_texts.append(text)
    
    # Also test just body
    enron_bodies = [str(b).strip() if pd.notna(b) else "" for b in enron_safe["body"]]

    ref_texts = [str(t).strip() if pd.notna(t) else "" for t in ref_safe["Email Text"]]

    # 1. Exact string hashes
    print("\n--- Measuring Exact Matches ---")
    enron_hashes_full = {hashlib.sha256(normalize_text_for_hash(t).encode("utf-8")).hexdigest() for t in enron_texts if t}
    enron_hashes_body = {hashlib.sha256(normalize_text_for_hash(t).encode("utf-8")).hexdigest() for t in enron_bodies if t}
    all_enron_hashes = enron_hashes_full.union(enron_hashes_body)

    exact_matches = 0
    for t in ref_texts:
        h = hashlib.sha256(normalize_text_for_hash(t).encode("utf-8")).hexdigest()
        if h in all_enron_hashes:
            exact_matches += 1

    pct_exact = (exact_matches / len(ref_texts)) * 100 if ref_texts else 0
    print(f"Exact Matches: {exact_matches} / {len(ref_texts)} ({pct_exact:.2f}%)")

    # 2. MinHash LSH for near duplicates (Jaccard >= 0.85)
    print("\n--- Measuring Near-Duplicate Matches (Jaccard >= 0.85) ---")
    lsh = MinHashLSH(threshold=0.85, num_perm=128)
    
    # Index Enron
    print("Indexing Enron into MinHash LSH...")
    for idx, t in enumerate(enron_texts):
        norm = normalize_text_for_hash(t)
        shingles = get_shingles(norm)
        if not shingles:
            continue
        m = MinHash(num_perm=128)
        for s in shingles:
            m.update(s.encode("utf-8"))
        lsh.insert(f"enron_{idx}", m)

    print("Querying Reference Safe Emails against Enron LSH...")
    near_matches = 0
    near_matched_indices = []
    for idx, t in enumerate(ref_texts):
        norm = normalize_text_for_hash(t)
        shingles = get_shingles(norm)
        if not shingles:
            continue
        m = MinHash(num_perm=128)
        for s in shingles:
            m.update(s.encode("utf-8"))
        result = lsh.query(m)
        if result:
            near_matches += 1
            near_matched_indices.append(idx)
        if idx > 0 and idx % 2000 == 0:
            print(f"  Processed {idx} / {len(ref_texts)} ref rows... near matches so far: {near_matches}")

    pct_near = (near_matches / len(ref_texts)) * 100 if ref_texts else 0
    print(f"\nNear-Duplicate Matches (J >= 0.85): {near_matches} / {len(ref_texts)} ({pct_near:.2f}%)")

    # Check non-exact matches for Enron markers
    print("\n--- Checking Enron Entity Markers in Reference Safe Emails ---")
    enron_cue_count = 0
    cues = ["@enron.com", "/hou/ect", "/corp/enron", "houston/ect", "enron", "vince kaminski", "jeff dasovich", "kay mann", "sara shackleton"]
    for t in ref_texts:
        t_low = t.lower()
        if any(c in t_low for c in cues):
            enron_cue_count += 1
    pct_cues = (enron_cue_count / len(ref_texts)) * 100
    print(f"Reference Safe Emails with explicit Enron cues/headers: {enron_cue_count} / {len(ref_texts)} ({pct_cues:.2f}%)")

if __name__ == "__main__":
    main()

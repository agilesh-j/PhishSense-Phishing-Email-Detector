"""Perform comprehensive cleaning audit, borderline review quarantine, and capacity calculation."""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import hashlib
import json
import random
import pandas as pd
import numpy as np
from datasketch import MinHash, MinHashLSH

from src.data.ingest import load_reference_dataset, load_spamassassin_hard_ham, load_tabular_source
from src.text.cleaner import clean_email_text, classify_content_status
from src.data.deduplicate import get_normalized_key, get_shingles, create_minhash

def main():
    random.seed(42)
    np.random.seed(42)
    os.makedirs("results", exist_ok=True)
    
    print("=" * 80)
    print("PHISHSENSE: INGESTION, CLEANING AUDIT & CAPACITY ANALYSIS")
    print("=" * 80)
    
    # 1. Ingest all 5 sources
    print("\n[1/5] Ingesting all raw datasets...")
    df_ref = load_reference_dataset("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")
    df_hard_ham = load_spamassassin_hard_ham("dataset/raw/spamassassin_hard_ham/extracted")
    df_nazario = load_tabular_source("dataset/raw/nazario_phishing/Nazario.csv", "nazario_phishing", 1, "phishing")
    df_nigerian = load_tabular_source("dataset/raw/nigerian_fraud/Nigerian_Fraud.csv", "nigerian_fraud", 1, "phishing")
    df_enron = load_tabular_source("dataset/raw/enron_clean/Enron.csv", "enron_clean", 0, "safe")
    
    sources = {
        "phishing_email_reference": df_ref,
        "spamassassin_hard_ham": df_hard_ham,
        "nazario_phishing": df_nazario,
        "nigerian_fraud": df_nigerian,
        "enron_clean": df_enron,
    }
    
    # 2. Cleaning and Rule-by-Rule Breakdown
    print("\n[2/5] Running text cleaner & rule-by-rule rejection classification...", flush=True)
    cleaning_stats = {}
    borderline_rows = []
    cleaned_records = []
    samples_per_source = {src: [] for src in sources}
    
    for src_name, df_src in sources.items():
        print(f"  Cleaning source '{src_name}' ({len(df_src):,} rows)...", flush=True)
        stats = {
            "raw_total": len(df_src),
            "raw_safe": (df_src["label"] == "safe").sum(),
            "raw_phishing": (df_src["label"] == "phishing").sum(),
            "raw_excluded": (df_src["label"] == "excluded").sum(),
            "empty_text": 0,
            "too_short": 0,
            "commercial_spam_excluded": 0,
            "borderline_quarantined": 0,
            "non_english_or_corrupt": 0,
            "clean_valid": 0,
            "valid_safe": 0,
            "valid_phishing": 0,
        }
        
        valid_cleaned_for_source = []
        
        for idx, row in df_src.iterrows():
            raw_text = row["text"]
            raw_lbl = row["label"]
            raw_id = row.get("raw_id", str(idx))
            
            # If excluded at ingestion (e.g. Enron spam label 1)
            if raw_lbl not in ("safe", "phishing"):
                continue
                
            cleaned = clean_email_text(raw_text)
            status, reason = classify_content_status(cleaned)
            
            if status == "valid":
                stats["clean_valid"] += 1
                if raw_lbl == "safe":
                    stats["valid_safe"] += 1
                elif raw_lbl == "phishing":
                    stats["valid_phishing"] += 1
                    
                rec = {
                    "source_id": src_name,
                    "source_file": row.get("source_file", ""),
                    "raw_id": raw_id,
                    "raw_label": row.get("raw_label", ""),
                    "label": raw_lbl,
                    "text": cleaned,
                    "word_count": len(cleaned.split()),
                    "char_count": len(cleaned),
                }
                cleaned_records.append(rec)
                valid_cleaned_for_source.append(rec)
            else:
                stats[status] += 1
                if status == "borderline_quarantined":
                    borderline_rows.append({
                        "source_id": src_name,
                        "raw_id": raw_id,
                        "label": raw_lbl,
                        "reason": reason,
                        "text": cleaned[:400],
                    })
                    
        cleaning_stats[src_name] = stats
        # Sample 5 random valid cleaned emails
        if valid_cleaned_for_source:
            sampled = random.sample(valid_cleaned_for_source, min(5, len(valid_cleaned_for_source)))
            samples_per_source[src_name] = sampled

    # Save borderline review file
    df_borderline = pd.DataFrame(borderline_rows)
    borderline_csv = "results/borderline_review.csv"
    df_borderline.to_csv(borderline_csv, index=False)
    print(f"Quarantined {len(df_borderline)} borderline rows to {borderline_csv}")
    
    # 3. Exact and Near Deduplication
    print("\n[3/5] Running exact and near-deduplication (MinHash/LSH, threshold=0.85)...")
    df_cleaned_all = pd.DataFrame(cleaned_records)
    print(f"Total clean valid records before deduplication: {len(df_cleaned_all):,} "
          f"({(df_cleaned_all['label']=='safe').sum():,} safe, {(df_cleaned_all['label']=='phishing').sum():,} phish)")

    # Canonical normalized key for exact dedupe
    df_cleaned_all["norm_key"] = df_cleaned_all["text"].apply(get_normalized_key)
    df_cleaned_all["key_hash"] = df_cleaned_all["norm_key"].apply(
        lambda k: hashlib.sha256(k.encode("utf-8")).hexdigest()
    )
    
    # Detect label conflicts
    label_counts_per_hash = df_cleaned_all.groupby("key_hash")["label"].nunique()
    conflict_hashes = set(label_counts_per_hash[label_counts_per_hash > 1].index)
    print(f"Detected {len(conflict_hashes)} conflicting text hashes (differing safe vs phishing labels)")
    
    # Quarantine conflicts
    df_no_conflict = df_cleaned_all[~df_cleaned_all["key_hash"].isin(conflict_hashes)].copy()
    
    # Exact deduplication
    df_exact_deduped = df_no_conflict.drop_duplicates(subset=["key_hash"], keep="first").copy()
    print(f"Total after exact deduplication: {len(df_exact_deduped):,} "
          f"({(df_exact_deduped['label']=='safe').sum():,} safe, {(df_exact_deduped['label']=='phishing').sum():,} phish)")

    # Near deduplication with MinHash LSH (per class)
    print("Running near-deduplication LSH per class...")
    near_deduped_rows = []
    
    for lbl in ["safe", "phishing"]:
        sub_df = df_exact_deduped[df_exact_deduped["label"] == lbl].reset_index(drop=True)
        lsh = MinHashLSH(threshold=0.85, num_perm=128)
        minhashes = {}
        
        for idx, row in sub_df.iterrows():
            shingles = get_shingles(row["text"], k=5)
            mh = create_minhash(shingles, num_perm=128)
            minhashes[idx] = mh
            try:
                lsh.insert(f"doc_{idx}", mh)
            except Exception:
                pass
                
        visited = set()
        kept_idx = []
        for idx in range(len(sub_df)):
            if idx in visited:
                continue
            mh = minhashes[idx]
            matches = lsh.query(mh)
            cluster = [int(m.split("_")[1]) for m in matches if m.startswith("doc_")]
            for c_idx in cluster:
                visited.add(c_idx)
            kept_idx.append(idx)
            
        deduped_sub = sub_df.iloc[kept_idx].copy()
        near_deduped_rows.append(deduped_sub)
        print(f"  Class '{lbl}': {len(sub_df):,} exact -> {len(deduped_sub):,} after LSH near-dedupe (dropped {len(sub_df)-len(deduped_sub):,})")

    df_final_pool = pd.concat(near_deduped_rows).reset_index(drop=True)
    print(f"\nFinal Deduplicated Candidate Pool: {len(df_final_pool):,} rows "
          f"({(df_final_pool['label']=='safe').sum():,} safe, {(df_final_pool['label']=='phishing').sum():,} phishing)")

    # 4. Capacity Table by Source and Class
    print("\n" + "=" * 80)
    print("SECTION 2.E: CAPACITY TABLE")
    print("=" * 80)
    
    pool_summary = df_final_pool.groupby(["source_id", "label"]).size().unstack(fill_value=0)
    print("\nFinal Unique Deduplicated Rows by Source & Class:")
    print(pool_summary)
    
    # 5. Output JSON Summary for Report
    clean_stats_serialized = {
        src: {k: int(v) for k, v in st.items()}
        for src, st in cleaning_stats.items()
    }
    audit_results = {
        "cleaning_stats": clean_stats_serialized,
        "borderline_count": int(len(df_borderline)),
        "conflict_hashes_count": int(len(conflict_hashes)),
        "post_clean_total": int(len(df_cleaned_all)),
        "post_exact_dedupe_total": int(len(df_exact_deduped)),
        "post_lsh_total": len(df_final_pool),
        "final_safe_pool": int((df_final_pool["label"] == "safe").sum()),
        "final_phish_pool": int((df_final_pool["label"] == "phishing").sum()),
        "pool_by_source": {f"{k[0]}_{k[1]}": int(v) for k, v in df_final_pool.groupby(["source_id", "label"]).size().items()},
        "samples_per_source": {
            src: [
                {
                    "raw_id": str(s["raw_id"]),
                    "label": str(s["label"]),
                    "word_count": int(s["word_count"]),
                    "snippet": str(s["text"][:220]),
                }
                for s in samples_per_source[src]
            ]
            for src in samples_per_source
        },
    }
    
    with open("results/capacity_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print("\nWrote results/capacity_audit.json successfully.")

if __name__ == "__main__":
    main()

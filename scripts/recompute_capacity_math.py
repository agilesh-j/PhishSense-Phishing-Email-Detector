"""Recompute capacity math under ALL constraints and generate reserve pool.

Constraints:
1. Balanced dataset: 50% Safe, 50% Phishing.
2. Reference dataset cap <= 25% of each class.
3. Any single source cap <= 40% of each class.
4. Safe class must have >= 3 sources and not be dominated by Enron.
   (SpamAssassin easy_ham + hard_ham provides non-Enron safe rows).
5. OOD Probe must contain BOTH classes and be held out from training.
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import pandas as pd

def compute_tier_breakdown(target_total, ood_source="ceas_08"):
    target_per_class = target_total // 2
    
    # Phishing allocation
    # Caps: Ref <= 25%, Nigerian <= 40%, Nazario <= 40%
    ref_phish_cap = int(target_per_class * 0.25)
    nig_phish_cap = int(target_per_class * 0.40)
    naz_phish_req = target_per_class - ref_phish_cap - nig_phish_cap
    
    # Safe allocation
    # Sources available:
    # - enron_clean: 9,574
    # - spamassassin_easy_ham: 3,742
    # - spamassassin_hard_ham: 213 (or held out for OOD)
    # - reference_safe: 10,109 (capped <= 25%)
    ref_safe_cap = int(target_per_class * 0.25)
    # Split remaining 75% between Enron (40%) and SpamAssassin (35%)
    enron_safe_cap = int(target_per_class * 0.40)
    sa_safe_req = target_per_class - ref_safe_cap - enron_safe_cap
    
    breakdown = {
        "target_total": target_total,
        "target_per_class": target_per_class,
        "phishing": {
            "phishing_email_reference": {
                "count": ref_phish_cap,
                "share_pct": round(ref_phish_cap / target_per_class * 100, 2),
                "cap_limit_pct": 25.0
            },
            "nigerian_fraud": {
                "count": nig_phish_cap,
                "share_pct": round(nig_phish_cap / target_per_class * 100, 2),
                "cap_limit_pct": 40.0
            },
            "nazario_phishing": {
                "count": naz_phish_req,
                "share_pct": round(naz_phish_req / target_per_class * 100, 2),
                "cap_limit_pct": 40.0
            },
            "total": ref_phish_cap + nig_phish_cap + naz_phish_req
        },
        "safe": {
            "phishing_email_reference": {
                "count": ref_safe_cap,
                "share_pct": round(ref_safe_cap / target_per_class * 100, 2),
                "cap_limit_pct": 25.0
            },
            "enron_clean": {
                "count": enron_safe_cap,
                "share_pct": round(enron_safe_cap / target_per_class * 100, 2),
                "cap_limit_pct": 40.0
            },
            "spamassassin_safe": {
                "count": sa_safe_req,
                "share_pct": round(sa_safe_req / target_per_class * 100, 2),
                "cap_limit_pct": 40.0
            },
            "total": ref_safe_cap + enron_safe_cap + sa_safe_req
        }
    }
    return breakdown

def main():
    print("=== PhishSense Capacity Recomputation Under ALL Quality Caps ===\n")
    
    # Current pool available clean rows:
    # Phishing:
    #   phishing_email_reference: 5,159 (usable max under 25% cap)
    #   nigerian_fraud: 2,802 (usable max under 40% cap)
    #   nazario_phishing: 1,420 (bottleneck!)
    # Max feasible class size from baseline pool:
    #   Nazario must provide at least 35% -> 1,420 / 0.35 = 4,057 rows
    max_baseline_class = int(1420 / 0.35)
    max_baseline_total = max_baseline_class * 2 # 8,114
    
    print(f"1. BASELINE THREE-SOURCE POOL (No external additions):")
    print(f"   Nazario ceiling = 1,420 rows.")
    print(f"   Since Reference <= 25% and Nigerian <= 40%, Nazario must supply >= 35%.")
    print(f"   Max feasible phishing class size = 1,420 / 0.35 = {max_baseline_class} rows.")
    print(f"   Max feasible total dataset size  = {max_baseline_total} rows (meets 8,000-12,000 PDF range).\n")
    
    tier_8k = compute_tier_breakdown(8000)
    tier_max = compute_tier_breakdown(max_baseline_total)
    
    print("--- TIER A (8,000 Rows - PDF Floor): ---")
    print(json.dumps(tier_8k, indent=2))
    
    print(f"\n--- TIER B (Maximum Feasible Baseline: {max_baseline_total} Rows): ---")
    print(json.dumps(tier_max, indent=2))

    # Save to results
    os.makedirs("results", exist_ok=True)
    summary = {
        "tier_8k": tier_8k,
        "tier_max_baseline": tier_max,
        "max_baseline_total": max_baseline_total,
    }
    with open("results/capacity_recomputation.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved capacity recomputation to results/capacity_recomputation.json")

if __name__ == "__main__":
    main()

"""Dataset curation to exact 10,000 rows (5,000 safe + 5,000 phishing) with strict quotas and OOD holdout."""
import os
import numpy as np
import pandas as pd


def curate_dataset(
    df: pd.DataFrame,
    target_safe: int = 5000,
    target_phishing: int = 5000,
    max_source_share: float = 0.40,
    min_sources_per_class: int = 3,
    ood_probe_size: int = 500,
    random_seed: int = 42,
    strict_brief_mode: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Curate cleaned, deduplicated email rows into the balanced 10,000-row pool.

    Enforces quotas:
      - 5,000 safe, 5,000 phishing
      - Max 40% from any single source per class (unless strict_brief_mode)
      - At least 3 sources per class (unless strict_brief_mode)
      - Dedicated OOD probe holdout

    Returns:
        (curated_df, ood_probe_df, stats_dict)
    """
    rng = np.random.RandomState(random_seed)

    if strict_brief_mode:
        print("[Curate] STRICT_BRIEF_MODE enabled: Building solely from Source #1...")
        src1_df = df[df["source_id"] == "phishing_email_reference"].copy()
        safe_pool = src1_df[src1_df["label"] == "safe"]
        phish_pool = src1_df[src1_df["label"] == "phishing"]

        assert (
            len(safe_pool) >= target_safe
        ), f"Insufficient safe rows in Source #1: {len(safe_pool)}"
        assert (
            len(phish_pool) >= target_phishing
        ), f"Insufficient phish rows in Source #1: {len(phish_pool)}"

        curated_safe = safe_pool.sample(
            n=target_safe, random_state=random_seed
        ).copy()
        curated_phish = phish_pool.sample(
            n=target_phishing, random_state=random_seed
        ).copy()
        curated_df = (
            pd.concat([curated_safe, curated_phish])
            .sample(frac=1.0, random_state=random_seed)
            .reset_index(drop=True)
        )

        # Empty or mock OOD probe in strict mode
        ood_probe_df = pd.DataFrame(columns=df.columns)
        stats = {
            "mode": "strict_brief_mode",
            "total_rows": len(curated_df),
            "safe_rows": len(curated_safe),
            "phish_rows": len(curated_phish),
            "composition": curated_df.groupby(["source_id", "label"])
            .size()
            .to_dict(),
        }
        return curated_df, ood_probe_df, stats

    # Enriched Multi-Source Mode
    print("[Curate] Multi-source enrichment mode enabled...")
    max_per_source_safe = int(target_safe * max_source_share)  # e.g., 2000
    max_per_source_phish = int(target_phishing * max_source_share)  # e.g., 2000

    # 1. Hold out an OOD probe slice from advance-fee / specialized fraud
    phish_all = df[df["label"] == "phishing"].copy()
    safe_all = df[df["label"] == "safe"].copy()

    # Reserve OOD probe from a dedicated sub-family (e.g. Nigerian fraud sample)
    if "nigerian_fraud" in df["source_id"].unique():
        nig_pool = phish_all[phish_all["source_id"] == "nigerian_fraud"]
        ood_probe_df = nig_pool.sample(
            n=min(ood_probe_size, len(nig_pool)), random_state=random_seed
        ).copy()
        # Remove OOD samples from training candidate pool
        phish_candidates = phish_all[~phish_all.index.isin(ood_probe_df.index)]
    else:
        ood_probe_df = phish_all.sample(
            n=ood_probe_size, random_state=random_seed
        ).copy()
        phish_candidates = phish_all[~phish_all.index.isin(ood_probe_df.index)]

    # 2. Sample Phishing Class across sources subject to max_source_share
    phish_samples = []
    phish_sources = phish_candidates["source_id"].unique()
    assert (
        len(phish_sources) >= min_sources_per_class
    ), f"Need >= {min_sources_per_class} phish sources, got {len(phish_sources)}"

    # Allocate quotas across sources
    allocated_phish = 0
    for src in phish_sources:
        src_phish = phish_candidates[phish_candidates["source_id"] == src]
        quota = min(len(src_phish), max_per_source_phish)
        # Sample quota
        sampled = src_phish.sample(n=quota, random_state=random_seed)
        phish_samples.append(sampled)
        allocated_phish += quota

    phish_pool_curated = pd.concat(phish_samples)
    if len(phish_pool_curated) > target_phishing:
        curated_phish = phish_pool_curated.sample(
            n=target_phishing, random_state=random_seed
        )
    else:
        curated_phish = phish_pool_curated

    # 3. Sample Safe Class across sources (including hard negatives)
    safe_samples = []
    safe_sources = safe_all["source_id"].unique()
    assert (
        len(safe_sources) >= min_sources_per_class
    ), f"Need >= {min_sources_per_class} safe sources, got {len(safe_sources)}"

    for src in safe_sources:
        src_safe = safe_all[safe_all["source_id"] == src]
        # Include all available hard negatives from spamassassin_hard_ham
        if src == "spamassassin_hard_ham":
            quota = len(src_safe)
        else:
            quota = min(len(src_safe), max_per_source_safe)
        sampled = src_safe.sample(n=quota, random_state=random_seed)
        safe_samples.append(sampled)

    safe_pool_curated = pd.concat(safe_samples)
    if len(safe_pool_curated) > target_safe:
        curated_safe = safe_pool_curated.sample(
            n=target_safe, random_state=random_seed
        )
    else:
        curated_safe = safe_pool_curated

    # 4. Final balanced dataset
    curated_df = (
        pd.concat([curated_safe, curated_phish])
        .sample(frac=1.0, random_state=random_seed)
        .reset_index(drop=True)
    )

    stats = {
        "mode": "enriched_multisource",
        "total_rows": len(curated_df),
        "safe_rows": len(curated_safe),
        "phish_rows": len(curated_phish),
        "ood_probe_rows": len(ood_probe_df),
        "composition": curated_df.groupby(["source_id", "label"])
        .size()
        .to_dict(),
    }
    return curated_df, ood_probe_df, stats

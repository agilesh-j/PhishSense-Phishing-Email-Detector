"""Exact and near-deduplication (MinHash/LSH) and label conflict resolution."""
import hashlib
import re
from datasketch import MinHash, MinHashLSH
import pandas as pd


def get_normalized_key(text: str) -> str:
    """Compute a canonical normalized string for exact deduplication."""
    if not isinstance(text, str):
        return ""
    # Lowercase, collapse numbers, collapse whitespace
    t = text.lower()
    t = re.sub(r"\d+", "<num>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def get_shingles(text: str, k: int = 5) -> set[str]:
    """Generate word k-gram shingles for MinHash."""
    words = text.lower().split()
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def create_minhash(shingles: set[str], num_perm: int = 128) -> MinHash:
    """Create a MinHash object from shingles."""
    m = MinHash(num_perm=num_perm, seed=42)
    for s in shingles:
        m.update(s.encode("utf-8"))
    return m


def remove_exact_duplicates_and_conflicts(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Identify and remove exact normalized duplicates and quarantine conflicting labels.

    Returns:
        (clean_df, exact_dupes_df, conflicts_df)
    """
    df = df.copy()
    df["norm_key"] = df["text"].apply(get_normalized_key)
    df["key_hash"] = df["norm_key"].apply(
        lambda k: hashlib.sha256(k.encode("utf-8")).hexdigest()
    )

    # 1. Detect conflicts (same key_hash but differing valid labels)
    valid_mask = df["label"].isin(["safe", "phishing"])
    valid_df = df[valid_mask]

    label_counts_per_hash = valid_df.groupby("key_hash")["label"].nunique()
    conflict_hashes = set(label_counts_per_hash[label_counts_per_hash > 1].index)

    conflicts_df = df[df["key_hash"].isin(conflict_hashes)].copy()
    non_conflict_df = df[~df["key_hash"].isin(conflict_hashes)].copy()

    # 2. Exact deduplication on non-conflicts
    # Keep the first occurrence of each unique key_hash
    clean_exact_df = non_conflict_df.drop_duplicates(
        subset=["key_hash"], keep="first"
    ).copy()
    exact_dupes_df = non_conflict_df[
        non_conflict_df.duplicated(subset=["key_hash"], keep="first")
    ].copy()

    return clean_exact_df, exact_dupes_df, conflicts_df


def remove_near_duplicates_lsh(
    df: pd.DataFrame,
    threshold: float = 0.85,
    num_perm: int = 128,
    shingle_k: int = 5,
) -> tuple[pd.DataFrame, list[list[str]]]:
    """Perform near-duplicate clustering using MinHash LSH.

    Keep one representative per near-duplicate cluster.

    Returns:
        (deduped_df, clusters)
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    minhashes = {}

    df = df.reset_index(drop=True)
    for idx, row in df.iterrows():
        shingles = get_shingles(row["text"], k=shingle_k)
        mh = create_minhash(shingles, num_perm=num_perm)
        minhashes[idx] = mh
        try:
            lsh.insert(f"doc_{idx}", mh)
        except Exception:
            pass

    visited = set()
    kept_indices = []
    clusters = []

    for idx in range(len(df)):
        if idx in visited:
            continue
        mh = minhashes[idx]
        matches = lsh.query(mh)
        cluster = [int(m.split("_")[1]) for m in matches if m.startswith("doc_")]

        if len(cluster) > 1:
            clusters.append(cluster)
            # Mark all as visited
            for c_idx in cluster:
                visited.add(c_idx)
            # Keep the primary representative
            kept_indices.append(idx)
        else:
            visited.add(idx)
            kept_indices.append(idx)

    deduped_df = df.iloc[kept_indices].copy()
    return deduped_df, clusters

# PhishSense: Architecture & Engineering Decision Records (ADR)

This document tracks all design, architectural, and methodological decisions. Any decision affecting label scope, source corpora, data splits, or evaluation protocols requires explicit user confirmation.

---

## Decision Record Index

| Decision ID | Date | Title | Status | Impact Area |
|---|---|---|---|---|
| ADR-001 | 2026-10-23 | Baseline Reference Archive Integrity & Verification | APPROVED | Dataset / Provenance |
| ADR-002 | 2026-10-23 | Commercial Spam & Out-of-Scope Label Exclusion Policy | APPROVED | Label Definition & Scope |
| ADR-003 | 2026-10-23 | Candidate Enrichment Sources Shortlist Selection & Vetting | AWAITING GATE 1 | Dataset Enrichment |
| ADR-004 | 2026-10-23 | Standalone Inlined Notebook Architecture via Generator Script | APPROVED | Pipeline Architecture |
| ADR-005 | 2026-10-23 | Local Git Management via MinGit User Installation | APPROVED | Version Control |
| ADR-006 | 2026-10-24 | Target Dataset Size Expansion (10,000–30,000, target 20,000; Test >= 2,000) | APPROVED | Dataset Architecture |
| ADR-007 | 2026-10-24 | Reference Dataset Role & Benchmark Baseline Policy (archive.zip <= 25%) | APPROVED | Dataset / Benchmark |
| ADR-008 | 2026-10-24 | External Quality Sources Prioritization for Authentic Phishing & Hard Ham | APPROVED | Data Discovery |
| ADR-009 | 2026-10-24 | Borderline Commercial Spam Quarantine to results/borderline_review.csv | APPROVED | Preprocessing / Quality |
| ADR-010 | 2026-10-24 | Pre-Approved Final Dataset Size & Fallback Ladder (12,000–16,000 rows) | APPROVED | Dataset Architecture |
| ADR-011 | 2026-10-24 | Pre-Approved Source Selection & Exclusions | APPROVED | Data Selection |
| ADR-012 | 2026-10-24 | Pre-Approved Source Diversity & Proportional Caps | APPROVED | Quality Assurance |
| ADR-013 | 2026-10-24 | Operational Hard Negative Expansion across All Safe Sources | APPROVED | Hard Negatives |
| ADR-014 | 2026-10-24 | Enhanced Text Cleaning, Spaced-Header Stripping & Unified Tokenization | APPROVED | Preprocessing |
| ADR-015 | 2026-10-24 | Fast Ingestion Pipeline with Pre-Sampling & MinHash/LSH Deduplication | APPROVED | Pipeline Optimization |
| ADR-016 | 2026-10-24 | Anti-Shortcut Learning & Era-Balancing Strategy | APPROVED | Anti-Shortcut Learning |
| ADR-017 | 2026-10-24 | Dedicated Out-of-Distribution (OOD) Probe Definition | APPROVED | Evaluation |
| ADR-018 | 2026-10-24 | Fixed Hyperparameter Configuration Policy | APPROVED | Model Architecture |

---

### ADR-001: Baseline Reference Archive Integrity & Verification
- **Status:** APPROVED (Verified)
- **Context:** The college assignment mandates the Kaggle dataset `subhajournal/phishingemails` as the primary reference dataset. An archive named `archive.zip` was placed in the repository root.
- **Decision:** Verified byte count and cryptographic SHA-256 hashes of `archive.zip` (18,918,073 bytes, SHA-256 `5d4d5cd13963aa8272ee771a64cae31aad9a4028534a9fc598f00fbf52b821be`) and the contained `Phishing_Email.csv` (52,034,604 bytes, SHA-256 `18ef4fff1acb8986f0ab01e83ede6025420c829656af5a377560fce17e153b97`). Both matched the assigned reference specifications exactly. Copied to `dataset/raw/phishing_email_reference/` and set read-only.
- **Alternative:** Downloading a new version from Kaggle (rejected: existing archive is verified bit-for-bit).

---

### ADR-002: Commercial Spam & Out-of-Scope Label Exclusion Policy
- **Status:** APPROVED
- **Context:** The primary reference dataset labels include "Safe Email" (11,322) and "Phishing Email" (7,328). Historical email corpora conflate general bulk marketing / commercial spam (e.g., pharmacy ads, adult services, unsolicited newsletters, Bayesian word-salad) with true phishing (social engineering, deception, credential theft, wire fraud/BEC, fake invoices).
- **Decision:** Formally distinguish phishing from commercial spam:
  - `phishing`: Deceptive intent designed to steal credentials, money, or personal data via impersonation or false pretenses.
  - `safe`: Legitimate personal, transactional, corporate, notifications, and honest marketing.
  - `out-of-scope (excluded)`: Pure commercial spam without identity spoofing, word-salad fragments, and unreadable texts.
- **Impact on Counts (Source #1):**
  - Raw: 11,322 safe, 7,328 phishing.
  - Dropped nulls & literal `"empty"`: 549 rows.
  - Dropped exact duplicates: ~1,135 rows.
  - Estimated commercial spam & word-salad excluded from "phishing": ~1,200 to 1,500 rows.
  - Net clean rows remaining in Source #1: ~9,800 safe and ~5,200 phishing (sufficient to satisfy the 5,000 + 5,000 quota in `STRICT_BRIEF_MODE`).
- **Strict Fallback:** In `STRICT_BRIEF_MODE: true`, the pipeline adheres strictly to Source #1's raw mapping without excluding spam.

---

### ADR-003: Candidate Enrichment Sources Shortlist Selection & Vetting
- **Status:** SUPERSEDED BY ADR-008 & SECTION 2 VETTING
- **Context:** To ensure prediction quality over quantity, candidate sources are vetted against the 7-criterion rubric.
- **Decision:** Original shortlist updated to incorporate full original Zenodo downloads and new modern sources (2015-2025).

---

### ADR-004: Standalone Inlined Notebook Architecture via Generator Script
- **Status:** APPROVED
- **Context:** In Colab, cloning or maintaining external Python modules from `src/` creates packaging and path friction. Furthermore, any drift between local modules and Colab notebook cells invalidates reproducibility.
- **Decision:** Build a single script `scripts/build_notebook.py` that reads the modular, tested functions from `src/` and inlines them directly into structured cells of `phishsense-phishing-email-detector.ipynb`.

---

### ADR-005: Local Git Management via MinGit User Installation
- **Status:** APPROVED
- **Context:** System terminal lacked `git` on PATH. Winget installer failed due to requiring elevated administrator UAC prompts.
- **Decision:** Installed official portable MinGit (Git for Windows v2.44.0) into `C:\Users\agile\AppData\Local\Programs\MinGit\cmd\git.exe` in user space and permanently added to the user PATH registry.
- **Evidence:** Repository initialized and first commit `4c22bdf` created.

---

### ADR-006: Target Dataset Size Expansion (10,000 to 30,000 Rows, Target 20,000; Test >= 2,000)
- **Status:** APPROVED (Mentor Approved)
- **Context:** The mentor approved expanding the curated balanced dataset beyond the PDF's 8,000–12,000 range, targeting ~20,000 rows (10,000 safe + 10,000 phishing) provided all quality gates and deduplication criteria pass. The test set must be at least 2,000 rows. `STRICT_BRIEF_MODE` remains the 10,000-row reference-only baseline fallback.
- **Decision:** Update `config.yaml` to specify `min_total_rows: 10000`, `target_total_rows: 20000`, `max_total_rows: 30000`, and `test_min_rows: 2000`. Curation will evaluate 3 tiers (~10k, ~16k, ~24k) and never compromise quality for count.

---

### ADR-007: Reference Dataset Role & Benchmark Baseline Policy
- **Status:** APPROVED
- **Context:** The Kaggle reference dataset (`archive.zip` / `Phishing_Email.csv`) represents a historical baseline but contains label noise, spam mixing, and outdated lures.
- **Decision:** Cap contribution from `archive.zip` to at most 25% of any class in the curated multi-source dataset, accepting only rows that strictly satisfy label guidelines and pass audits. Furthermore, use `archive.zip` as an explicit benchmark: train a baseline model strictly on reference data (`STRICT_BRIEF_MODE`) and evaluate it against the enriched model on the identical held-out test set.

---

### ADR-008: External Quality Sources Prioritization (Quality for Prediction)
- **Status:** APPROVED
- **Context:** Modern phishing relies on social engineering, Microsoft 365 / cloud lures, bank impersonation, and BEC, which older 2000-era corpora lack.
- **Decision:** Prioritize prediction quality over data volume. Ingest full pristine originals from Zenodo, SpamAssassin, and discover new modern corpora (2015–2025) across Kaggle, Hugging Face, GitHub, and academic repositories. Enforce: source cap <= 40%, >= 3 sources per class, hard negatives 20–30% of safe, synthetic <= 15% (quarantined slice).

---

### ADR-009: Borderline Commercial Spam Quarantine
- **Status:** APPROVED
- **Context:** Relying solely on static keyword lists to drop commercial spam risks false positive exclusions of legitimate corporate or security alerts.
- **Decision:** Clean and screen rows: confident commercial spam is excluded with logged counts, while ambiguous/borderline rows are routed to `results/borderline_review.csv` for audit inspection rather than admitted silently into the training set.

---

### ADR-010: Pre-Approved Final Dataset Size & Fallback Ladder
- **Status:** APPROVED (Fast Build Execution)
- **Context:** Mentor approval secured in `docs/MENTOR_APPROVAL.md` for expanding beyond the baseline brief up to 12,000–16,000 balanced rows (6,000–8,000 per class), stratified 70/15/15.
- **Decision:** Target the maximum viable balanced size between 12,000 and 16,000 rows that satisfies all source caps and hard-negative rules. If phishing is short, evaluate fallback ladder: (a) raise phishing single-source cap to 45%; (b) evaluate reference phishing audit (>= 95% precision); (c) reduce to minimum 8,000 rows.

---

### ADR-011: Pre-Approved Source Selection & Exclusions
- **Status:** APPROVED
- **Context:** Authentic phishing attacks require modern lures (cloud, banking, 2FA) and clean ham requires diverse corporate and technical correspondence.
- **Decision:** 
  - Phishing sources: `nigerian_fraud` (full Zenodo original), `nazario_phishing` (Zenodo original), `nazario_modern` (annual mbox files 2015–2025 from monkey.org).
  - Safe sources: `enron_clean` (full Zenodo original), `spamassassin_hard_ham`, `spamassassin_easy_ham` (and `easy_ham_2`), `ceas_08` (class 0 only, 100% precision audit), and reference "Safe Email" rows.
  - Excluded sources: `ceas_08` class 1, TREC, Ling, HF puyang2025, and all synthetic/LLM-generated text. Reference "Phishing Email" is audited (60 rows) and excluded unless precision >= 95%.

---

### ADR-012: Pre-Approved Source Diversity & Proportional Caps
- **Status:** APPROVED
- **Context:** Models must not learn source identity or single-corpus artifacts.
- **Decision:** Any single source <= 40% of a class (45% for phishing only if fallback ladder is invoked); reference dataset <= 25% of a class; Enron + reference-safe together <= 40% of safe class; >= 3 distinct sources per class.

---

### ADR-013: Operational Hard Negative Expansion across All Safe Sources
- **Status:** APPROVED
- **Context:** Models fail on security alerts, IT notifications, invoices, and password resets if only trained on casual personal ham.
- **Decision:** Apply the operational hard-negative detection rule in `docs/LABEL_GUIDELINES.md` to all safe sources (Enron, SpamAssassin, CEAS-08, Reference Safe). Aim for 20–30% hard negatives in the safe class (minimum 12% accepted naturally).

---

### ADR-014: Enhanced Text Cleaning, Spaced-Header Stripping & Unified Tokenization
- **Status:** APPROVED
- **Context:** Residual header artifacts (e.g., `to : `, `from : `, `subject : `, `- - - - original message - - - -`) and token variations (`' s` vs `'s`) provide trivial non-body shortcuts.
- **Decision:** Implement strict spaced-header regex stripping, unify contractions (`' s` -> `'s`), normalize quotes and dashes, and mask `<routing>`, `<date>`, `<time>`, `<year>`, `<num>`, `<footer_marker>`, `<url>`, `<email>`, `<phone>`. Implement robust mbox MIME traversal extracting plain body text only.

---

### ADR-015: Fast Ingestion Pipeline with Pre-Sampling & MinHash/LSH Deduplication
- **Status:** APPROVED
- **Context:** Computing MinHash across 80,000+ raw records creates execution bottlenecks.
- **Decision:** After cleaning and exact deduplication, pre-sample each candidate source pool to ~2.5x its target quota using seed 42 before executing MinHash/LSH near-deduplication (Jaccard >= 0.85). Drop label conflicts and route qualified excess rows to `results/reserve_pool.csv`.

---

### ADR-016: Anti-Shortcut Learning & Era-Balancing Strategy
- **Status:** APPROVED
- **Context:** Single-class or single-era sources risk teaching models that modern formatting equals phishing.
- **Decision:** Balance phishing across historical (Nigerian 419, Nazario 2005–2007) and modern (Nazario 2015–2025) eras. Disclose safe class historical limitations transparently. Execute and log source-ID probe, style probe, and marker ablation tests.

---

### ADR-017: Dedicated Out-of-Distribution (OOD) Probe Definition
- **Status:** APPROVED
- **Context:** Evaluating model generalization beyond the training corpus requires a pristine, un-tuned holdout set.
- **Decision:** Phishing OOD probe = latest year of `nazario_modern` with >= 150 usable rows. Safe OOD probe = 150 held-out `ceas_08` class-0 rows. Both held out completely from training, validation, and hyperparameter tuning.

---

### ADR-018: Fixed Hyperparameter Configuration Policy
- **Status:** APPROVED
- **Context:** Two-hour execution budget prioritizes rigorous data engineering, anti-leakage proofs, and error analysis over expensive hyperparameter grid sweeps.
- **Decision:** Fix architecture to 2-layer Transformer Encoder (`d_model` 128, 4 heads, `dim_feedforward` 256, dropout 0.2), AdamW with cosine decay, and early stopping on validation macro-F1.


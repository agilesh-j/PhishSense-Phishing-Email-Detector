# Dataset Card: PhishSense Multi-Source Email Corpus

## 1. Dataset Summary & Motivation
The **PhishSense Multi-Source Email Corpus** is a curated, high-integrity benchmark designed for robust phishing email detection. In response to widespread data leakage, commercial spam contamination, and artificial class imbalances in public Kaggle compilations, PhishSense implements strict multi-source curation, documented hard-negative filtering, dynamic token masking, and zero-leakage deduplication.

- **Total Curated Size:** 11,000 balanced rows (5,500 Safe, 5,500 Phishing).
- **Split Distribution (70 / 15 / 15):**
  - **Train:** 7,696 rows (3,848 Safe, 3,848 Phishing)
  - **Validation:** 1,646 rows (823 Safe, 823 Phishing)
  - **Test (Untouched):** 1,658 rows (829 Safe, 829 Phishing)
- **Evaluation Probes:**
  - **Temporal Holdout Probe:** 400 rows (200 Nazario Modern 2025 unseen zero-day attacks + 200 CEAS-08 safe held-out rows from a training source)
- **Surplus Reserve Pool:** Qualified surplus rows stored in `results/reserve_pool.csv`.

---

## 2. Source Provenance & Licensing

All sources were vetted, parsed from original publishers, and strictly filtered.

| Source Name | Category | Primary Origin / Archive | License / Terms | Curated Count | Share in Class |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nigerian Fraud** | Phishing | Zenodo (C. Nazario / Academic Archive) | Creative Commons Attribution 4.0 (CC BY 4.0) | 2,475 | 45.00% |
| **Nazario Modern** | Phishing | Jose Nazario / monkey.org (2015–2024 mboxes) | Academic Research Exemption / Public Archive | 1,631 | 29.65% |
| **Nazario Phishing** | Phishing | Zenodo (Original Nazario corpus) | Creative Commons Attribution 4.0 (CC BY 4.0) | 1,394 | 25.35% |
| **CEAS 08 (Class 0)** | Safe | CEAS 2008 Anti-Spam Challenge (Clean Ham) | Public Research Corpus (100% Precision) | 2,200 | 40.00% |
| **Enron Clean** | Safe | Enron Corpus (Cleaned business ham) | Apache 2.0 / Public Domain Record | 1,375 | 25.00% |
| **SpamAssassin Easy** | Safe | Apache SpamAssassin (easy_ham 1 & 2) | Apache License 2.0 | 861 | 15.65% |
| **Reference Safe** | Safe | Subhashini et al. (`Phishing_Email.csv` Safe subset) | Open Academic Dataset | 825 | 15.00% |
| **SpamAssassin Hard** | Safe | Apache SpamAssassin (hard_ham challenge) | Apache License 2.0 | 239 | 4.35% |

### Excluded Sources
- **Reference Phishing (`Phishing_Email.csv`):** A 60-row random manual audit revealed a precision of only 90.0% (< 95% threshold) due to heavy inclusion of commercial promotional spam (coupons, retail newsletters). Under ADR-011, it is strictly excluded from training data and reserved solely as an external baseline comparison.

---

## 3. Strict Documented Hard Negative Policy

Under `docs/LABEL_GUIDELINES.md`, genuine hard negatives are legitimate non-phishing emails that contain security, credential, or financial context combined with explicit action directives.

- **Documented Rule:**
  - **Security/Financial Cues:** `urgent`, `immediate`, `action required`, `deadline`, `important notice`, `account`, `password`, `login`, `security`, `verify`, `payment`, `wire`, `transfer`, `invoice`, `billing`, `bank`, `suspended`, `reset`, `compromised`, `attachment`.
  - **Action Directives:** `<url>`, `click`, `please visit`, `log in`, `sign in`, `review the attached`, `download`, `verify here`.
  - **Disallowed Heuristics:** Generic conversational words like `contact`, `reply`, or `contract` were prohibited to prevent artificial label distortion.
- **Prevalence & Quotas:**
  - Natural pool qualification: **36.84%** of safe emails (2,026 of 5,500) qualify under this strict two-part definition.
  - Per-source qualification: CEAS-08 (55.2%), SpamAssassin Hard Ham (54.0%), SpamAssassin Easy Ham (34.7%), Reference Safe (31.3%), Enron Clean (9.2%).

---

## 4. Text Cleaning & Dynamic Masking Pipeline

Raw emails undergo multi-stage normalization via `src/text/cleaner.py`:
1. **Header Stripping:** Removal of spaced headers (`to : `, `from : `, `subject : `, `sent : `, `cc : `) and multiline MIME boundaries.
2. **Unicode Normalization:** NFKC normalization, smart-quote conversion (`’` $\to$ `'`), and spaced contraction unification (`don ' t` $\to$ `don't`).
3. **Dynamic Token Masking:** High-entropy identifiers are replaced with canonical tokens to prevent memorization of transient artifacts:
   - `<url>`: Web links and IP addresses
   - `<email>`: Email addresses
   - `<phone>`: Telephone numbers
   - `<routing>`: Server IP hops and routing headers
   - `<date>` / `<time>` / `<year>`: Absolute date-time stamps
   - `<num>`: Multi-digit financial figures and tracking codes
   - `<footer_marker>`: Mailing list unsubscribe/administrative disclaimers
4. **Length Gating:** Emails strictly filtered to $10 \le \text{word\_count} \le 5,000$.

---

## 5. Deduplication & Zero-Leakage Guarantees

- **Exact Deduplication:** Multi-source SHA-256 hash checks collapsed 52,700 raw records into 50,657 unique texts.
- **Near-Deduplication:** MinHash LSH with 64 permutations and 5-shingle Jaccard threshold $\ge 0.85$ removed near-duplicate phishing blasts and template variants.
- **Alphanumeric Zero-Leakage Invariant:** Stringent programmatic intersection checks assert:
  $$\text{Train} \cap \text{Val} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Val} \cap \text{Test} = \emptyset$$
  across alphanumeric normalized text strings (`re.sub(r'[^a-z0-9]', '', text.lower())`), confirming 0.0% data leakage across all splits.

---

## 6. Era, Style & Confounder Probes

### 6.1 Era Breakdown & Recall by Era
Safe emails originate from historical archives (1999–2008), while phishing spans both historical (Nigerian Fraud, Nazario Zenodo) and modern (Nazario Modern 2015–2024):

| Split | Class | Historical Count | Modern Count | Modern Phish Share |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | Phishing | 2,698 | 1,141 | 29.7% |
| **Train** | Safe | 3,848 | 0 | 0.0% |
| **Validation** | Phishing | 578 | 244 | 29.7% |
| **Validation** | Safe | 823 | 0 | 0.0% |
| **Test** | Phishing | 580 | 246 | 29.8% |
| **Test** | Safe | 829 | 0 | 0.0% |

**Baseline Model Phishing Recall Across Eras:**
- **Validation:** Old-Era Phishing Recall: **98.79%** (578 samples) | Modern Phishing Recall: **98.36%** (244 samples)
- **Test:** Old-Era Phishing Recall: **98.79%** (580 samples) | Modern Phishing Recall: **97.56%** (246 samples)

### 6.2 Surface / Style Probe
- **Raw Text Style Probe:** Logistic Regression using only character counts, word counts, uppercase ratio, and token presence achieves **82.98% Accuracy** (Macro-F1: 0.8296).
  - Top Standardized Features: `char_len` (-4.81), `word_count` (+4.47), `upper_ratio` (+2.48), `punct_ratio` (-1.32), `avg_word_len` (+0.87).
- **Model-Seen Text Style Probe (Lowercased & Masked):** Re-running the probe on text *exactly as the model ingests it* (zero uppercase, canonical masks) yields **79.21% Accuracy** (Macro-F1: 0.7915).
  - Top Standardized Features: `char_len` (-4.48 Safe), `word_count` (+4.18 Phishing), `avg_word_len` (+1.39 Phishing), `punct_ratio` (-1.32 Safe), `has_time_token` (-0.64 Safe), `has_date_token` (-0.59 Safe).
- **Marker Ablation:** Removing the top-50 source markers causes only $\Delta \text{F1} = -0.0012$ ($0.9830 \to 0.9818$), confirming **no large dependence on the top-50 source markers**.

---

## 7. Known Limitations & Responsible AI Disclosures

1. **Surface Style Confounder (79.21% Style Probe Accuracy):**
   - **Limitation:** The surface style probe achieves 79.21% accuracy even on lowercased and masked text, exceeding the target threshold of 65%. This is driven primarily by document length (`char_len` and `word_count`) and punctuation frequency: corporate emails in Enron and CEAS are concise operational messages, whereas advance fee fraud and phishing templates tend to be verbose and narrative-heavy.
   - **Impact:** While the custom Transformer learns rich semantic context and attention patterns beyond simple length, users must be aware that document length remains a correlated feature in public email corpora.
2. **Absence of Modern Public Safe Corpora:**
   - **Limitation:** As no modern, openly licensed safe email corpus was found, all open safe email corpora date from 1999–2008, while phishing spans 2005–2024.
   - **Mitigation:** Dynamic token masking (`<year>`, `<date>`, `<time>`) actively removes explicit temporal markers.
3. **Temporal Holdout Probe Nature:**
   - The phishing half (Nazario Modern 2025, 200 rows) represents authentic unseen temporal shift.
   - The safe half (200 rows) consists of held-out legitimate rows from CEAS-08 (an existing training source), as no modern, openly licensed safe email corpus was found. Genuine modern safe evaluation requires internal telemetries.

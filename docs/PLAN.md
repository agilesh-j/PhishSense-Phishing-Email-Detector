# PhishSense: Phishing Email Detector
## Master Engineering & Execution Plan

**Institution:** Arunachala HiTech Engineering College  
**Portal:** ML Training | Applied AI  
**Project:** PhishSense: Phishing Email Detector  
**Team 02:**
- **AGILESH J** (963624243004) — Data Lead: Dataset discovery, ingestion, cleaning, deduplication, provenance
- **AJWIN M** (963624243006) — Model Lead: PyTorch Transformer architecture, training loop, hyperparameter tuning
- **SEEKANTH N L** (963624243049) — Evaluation & Quality Lead: Quality audits, slice analysis, calibration, report, documentation

---

## 1. Executive Summary & Binding Mission

The objective of **PhishSense** is to detect phishing language in raw email text using a custom, from-scratch PyTorch Transformer classifier. The project emphasizes empirical machine learning engineering rigor: data quality, zero-leakage protocols, strict avoidance of shortcut learning, and complete reproducibility.

The final deliverable is an end-to-end, self-contained, executed Jupyter Notebook (`phishsense-phishing-email-detector.ipynb`, under 2 MiB) running seamlessly in Google Colab from Google Drive, with all artifacts, manifests, and reports deposited in `Applied_AI/Team 02/`.

### Binding Assignment Constraints (College Portal Brief)
1. **Scope:** Pure email text only. Strictly **no** URL extraction, domain lookup, attachment analysis, or network features.
2. **Target Labels:** Binary classification with exact string labels: `"safe"` and `"phishing"`.
3. **Dataset Volume:** Balanced sample within 8,000 to 12,000 rows. Target is exactly **10,000 curated rows** (5,000 safe, 5,000 phishing).
4. **Primary Reference Source:** Kaggle `subhajournal/phishingemails` (`archive.zip`, 18,650 raw rows).
5. **Approved Enrichment:** Multi-source enrichment (3–6 vetted sources) to infuse modern attack vectors and hard negatives, governed by a configurable `STRICT_BRIEF_MODE` fallback.
6. **Zero Data Leakage:** Preprocessing, tokenization, vocabulary, and sequence length decisions fitted **strictly on training splits**. No test split leakage.
7. **Standalone Deliverable:** The final notebook must inline all logic (no custom external package imports from `src/`) and execute cleanly top-to-bottom within Colab.

---

## 2. Phase-by-Phase Roadmap & Milestones

The execution strictly maps to the 8 College Portal Milestones and the 15-phase Antigravity engineering workflow:

```
Phase 0: Environment, Config, and Verification
  │
Phase 1: Dataset Discovery & Vetting (GATE 1: Shortlist Approval)
  │
Phase 2: Label Guidelines & Scope Definition (GATE 2: Guidelines Approval)
  │
Phase 3: Dataset Ingestion & Provenance Recording (PDF Milestone 2)
  │
Phase 4: Robust Text-Only Cleaning Pipeline (PDF Milestone 3)
  │
Phase 5: Global Deduplication & Conflict Resolution
  │
Phase 6: Curation to 10,000 Rows & OOD Holdout (GATE 3: Composition Approval)
  │
Phase 7: Leakage-Free Stratified Splits (70/15/15)
  │
Phase 8: Dataset Quality Audit & Shortcut Probes (GATE 4: Dataset Card Approval)
  │
Phase 9: Training-Only Vocabulary & Text Prep (PDF Milestone 4)
  │
Phase 10: PyTorch Transformer from Scratch (PDF Milestone 5)
  │
Phase 11: Reproducible Training & Checkpointing (PDF Milestone 6)
  │
Phase 12: Single-Pass Final Evaluation & Error Analysis (PDF Milestone 7)
  │
Phase 13: Standalone Notebook Generation (< 2 MiB) (PDF Milestone 8a)
  │
Phase 14: Local Smoke Gate, Colab Handoff, and Portal Submission (PDF Milestone 8b)
```

---

## 3. Phase Specifications

### Phase 0: Setup, Configuration & Baseline Verification
- Verify `archive.zip` SHA-256 (`5d4d5cd1...`) and extracted `Phishing_Email.csv` SHA-256 (`18ef4fff...`).
- Establish `config.yaml` with global seed (42), paths, row targets (5,000/5,000), split ratios (0.70 / 0.15 / 0.15), and `STRICT_BRIEF_MODE` toggle.
- Create pinned `requirements.txt` and verify device-agnostic execution (CPU locally, CUDA in Colab).

### Phase 1: Candidate Discovery & Vetting (GATE 1)
- Audit candidate open corpora against the 7-criterion rubric: License, Provenance, Label Methodology, Content Quality, Diversity, Hard Negatives, and Label Noise (< 5%).
- Compile `results/source_vetting.md` and present shortlist for user approval.

### Phase 2: Label Definition & Scope Specification (GATE 2)
- Formalize `docs/LABEL_GUIDELINES.md`:
  - `phishing`: Deceptive emails utilizing false pretexts, brand impersonation, credential harvesting, wire fraud (BEC), advance-fee scams, or malicious coercion.
  - `safe`: Legitimate personal, transactional, corporate, security alerts, and newsletters.
  - `out-of-scope (excluded)`: Plain commercial spam without identity spoofing, word-salad fragments, unparseable bodies.
- Document 5 prototypical examples per class and 5 borderline cases with explicit rulings.

### Phase 3: Collection & Raw Provenance (PDF Milestone 2)
- Ingest approved sources into `dataset/raw/<source>/` keeping original files pristine and read-only.
- Generate `results/source_manifest.json` recording source URLs, licenses, download timestamps, original hashes, schemas, and raw label mappings.

### Phase 4: Text Cleaning Pipeline (PDF Milestone 3)
- Implement regex and BeautifulSoup pipeline:
  - Strip email headers (`From:`, `To:`, `Date:`, `Subject:`, `Received:`, etc.).
  - Strip HTML tags, scripts, CSS styles, and normalize Unicode (NFKC).
  - Mask dynamic tokens: URLs -> `<url>`, Emails -> `<email>`, Phone numbers -> `<phone>`.
  - Strictly forbid extraction of URL hostnames, counts, attachments, or metadata.
  - Filter out blank, placeholder (`empty`), non-English, and ultra-short texts (< 15 words) or excessive characters (> 5,000 chars).
  - Mask PII in corporate archives (Enron).

### Phase 5: Global Deduplication & Conflict Resolution
- Normalize text bodies (lowercase, collapse whitespace, numbers, tokens).
- Compute exact deduplication across all sources.
- Execute MinHash / LSH near-deduplication (Jaccard similarity threshold >= 0.85 on word 5-grams).
- Detect and quarantine label conflicts (identical/near-identical text with conflicting labels).
- Produce before/after counts in `results/deduplication_report.md`.

### Phase 6: Curation to 10,000 Rows & OOD Holdout (GATE 3)
- Assemble the balanced 10,000-row dataset according to quota rules:
  - Exactly 5,000 `safe` and 5,000 `phishing`.
  - Max 40% contribution from any single source per class.
  - Hard negatives comprising 20% to 30% of the `safe` class.
  - Balance source ratios internally to eliminate "source ID" shortcut learning.
  - Hold out an Out-Of-Distribution (OOD) probe (500–1,000 rows) saved to `dataset/processed/ood_probe.csv` (never touched during training or hyperparameter tuning).
- Output `results/dataset_composition.md`.

### Phase 7: Leakage-Free Stratification & Splitting
- Split curated pool into 70% Train (7,000), 15% Validation (1,500), 15% Test (1,500).
- Preserve exact 50:50 class balance in all splits.
- Enforce group-aware clustering: near-duplicate clusters and template families reside strictly in one partition.
- Assert zero token/normalized-text overlap between Train, Validation, and Test.

### Phase 8: Quality Audit & Shortcut Probes (GATE 4)
- Perform stratified manual label audit sample (>= 150 rows per class). Calculate Cohen's kappa.
- Run shortcut probes:
  - Source ID classifier (accuracy must be <= 60%).
  - Surface statistics classifier (length, uppercase ratio, punctuation ratio <= 65%).
  - First-5-token leak test.
- Train out-of-fold TF-IDF + Logistic Regression on Train+Validation to identify label noise.
- Author comprehensive `results/dataset_card.md`.

### Phase 9: Training-Only Vocabulary & Preprocessing (PDF Milestone 4)
- Tokenize training text using a custom whitespace/punctuation tokenizer preserving `<url>`, `<email>`, `<phone>`.
- Build vocabulary from **Train split only**: `<PAD>=0`, `<UNK>=1`, min frequency 2, vocabulary cap ~30,000 tokens.
- Determine sequence cutoff (`max_len`) from Train 95th percentile (capped at 256–384 tokens).
- Save `vocab.json`, `labels.json`, and `preprocessing_config.json` to `artifacts/`.

### Phase 10: PyTorch Transformer from Scratch (PDF Milestone 5)
- Construct custom PyTorch `nn.Module`:
  - Token embedding + learned/sinusoidal position embeddings.
  - Key padding mask handling padding tokens.
  - 2 Transformer Encoder layers (`d_model`: 128–256, `nhead`: 4, `dim_feedforward`: 256–512, dropout: 0.1–0.2).
  - Masked mean pooling across non-padded tokens.
  - Linear classification head (`d_model` -> 2 logits).
- Run one forward/backward pass on a single batch: assert finite logits, finite cross-entropy loss, and non-zero gradients.

### Phase 11: Reproducible Training & Checkpointing (PDF Milestone 6)
- Train with AdamW, linear warmup + cosine decay, gradient clipping (1.0).
- Evaluate per epoch: Train loss, Validation loss, Validation accuracy, and Validation macro-F1.
- Implement early stopping (patience = 3 epochs) monitoring Validation macro-F1.
- Save best model checkpoint (`best_model.pt`) and reload it to verify bit-exact inference.
- Run baseline models (TF-IDF + Logistic Regression, surface-only baseline) for benchmark comparison.

### Phase 12: Final Evaluation & Comprehensive Error Analysis (PDF Milestone 7)
- Freeze model and evaluate **once** on the untouched Test split (`torch.no_grad()`).
- Report: Accuracy, Macro/Weighted Precision, Recall, F1, Confusion Matrix, ROC-AUC, PR-AUC.
- Evaluate model across slices: per-source, real vs. synthetic, hard negatives vs. normal safe, and the OOD probe.
- Compute calibration curve and Expected Calibration Error (ECE).
- Tabulate 15+ error cases with detailed root-cause diagnoses.
- Enforce the **Suspicion Rule**: If test macro-F1 >= 0.99, immediately halt and audit for subtle leaks or shortcuts.

### Phase 13: Standalone Notebook Generation (PDF Milestone 8a)
- Develop `scripts/build_notebook.py` to assemble `phishsense-phishing-email-detector.ipynb`.
- Inline all modules directly (zero imports from `src/`).
- Include team manifest cell, Drive mounting, pipeline execution/loading, training curves, metrics, and interactive `predict(text)` function.
- Enforce strict size check (< 2 MiB) by downsampling static plots and clearing non-essential cell outputs.

### Phase 14: Local Gate, Colab Handoff & Portal Submission (PDF Milestone 8b)
- Run complete test suite (`pytest`) and data validation (`scripts/validate_dataset.py`) in both regular and `STRICT_BRIEF_MODE`.
- Run CPU smoke test end-to-end.
- Prepare `docs/COLAB_RUNBOOK.md` with explicit Google Drive upload, Colab GPU execution, verification, and portal submission receipt steps.

---

## 4. Key Design Decisions & Governance

| Area | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| **Text Scope** | Pure text body only; mask `<url>`, `<email>`, `<phone>` | Assignment brief explicitly forbids URL, attachment, and network features | Extracting domain age/reputation (violates brief) |
| **Spam Policy** | Exclude commercial spam from phishing class | Phishing requires deceptive intent / credential harvesting. Mixing commercial spam introduces noisy decision boundaries | Treating spam as phishing (leads to false positives on legitimate marketing) |
| **Model** | Custom PyTorch 2-layer Transformer Encoder | Strictly adheres to "from scratch in PyTorch" requirement while remaining lightweight for Colab | Pretrained BERT/RoBERTa (violates "small transformer from scratch" brief) |
| **Checkpointing** | Validation macro-F1 only | Balanced optimization across both safe and phishing classes | Validation loss or test accuracy (test tuning strictly forbidden) |
| **Notebook Build** | Automated inlining via `scripts/build_notebook.py` | Eliminates drift between tested local codebase and Colab standalone notebook | Manual notebook editing (prone to copy-paste bugs and drift) |

---

## 5. Risk Assessment & Mitigation Matrix

| Risk | Severity | Probability | Mitigation Strategy |
|---|---|---|---|
| **Data Leakage across Splits** | Critical | Medium | Hash-based exact deduplication + MinHash/LSH near-deduplication; programmatic zero-overlap assertions across train/val/test splits. |
| **Shortcut / Confounder Learning** | High | High | Strip all headers; mask URLs/emails; verify balance across sources; execute source-ID and style shortcut probes. |
| **Colab Disconnect / Ephemeral Loss** | High | Medium | Store all data, checkpoints, and outputs directly in mounted Google Drive (`Applied_AI/Team 02/`). |
| **Notebook Exceeding 2 MiB Portal Limit** | High | Low | Automated assertion in `scripts/build_notebook.py`; downsample figures to 100 DPI; truncate verbose training logs. |
| **Class Label Noise in Public Corpora** | Medium | High | Multi-stage cleaning; manual audit of 150 rows/class; out-of-fold TF-IDF error inspection before training. |
| **Out-Of-Distribution Degradation** | Medium | Medium | Hold out dedicated OOD probe dataset; report slice performance transparently in final documentation. |

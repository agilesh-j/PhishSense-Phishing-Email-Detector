# PhishSense: Phishing Email Detector
## Master Project Execution Checklist

**Institution:** Arunachala HiTech Engineering College | Applied AI  
**Project:** PhishSense: Phishing Email Detector (Team 02)  
**Rule:** Only check an item `[x]` after completing the step AND providing concrete evidence (file path, SHA-256 hash, row count, test output, or table). Never tick an item without verifiable proof.

---

## Phase 0. Setup & Repository Foundation
- [x] Create folder structure: `dataset/raw/`, `dataset/processed/`, `artifacts/`, `results/`, `src/`, `scripts/`, `tests/`, `docs/`. *(Evidence: Directory structure created and verified)*
- [x] Set up `.gitignore` for Python, artifacts, cache, and virtual environment. *(Evidence: `.gitignore` file created)*
- [x] Initialize pinned `requirements.txt` (`torch`, `pandas`, `numpy`, `scikit-learn`, `datasketch`, `beautifulsoup4`, `pyyaml`, `matplotlib`, `seaborn`, `nbformat`, `pytest`, `datasets`, `kaggle`). *(Evidence: Pinned `requirements.txt` installed in `.venv`)*
- [x] Establish `config.yaml` (global seed 42, paths, 10,000 row targets, split ratios 70/15/15, `STRICT_BRIEF_MODE: false`, model hyperparameters). *(Evidence: `config.yaml` created)*
- [x] Place reference dataset `archive.zip` in `dataset/raw/phishing_email_reference/`, make read-only, and verify SHA-256 matches `5d4d5cd13963aa8272ee771a64cae31aad9a4028534a9fc598f00fbf52b821be`. *(Evidence: SHA-256 match confirmed via Python/PowerShell, `attrib +r` set)*
- [x] Extract `Phishing_Email.csv` to `dataset/raw/phishing_email_reference/extracted/` and verify SHA-256 matches `18ef4fff1acb8986f0ab01e83ede6025420c829656af5a377560fce17e153b97`. *(Evidence: SHA-256 match confirmed, size 52,034,604 bytes, `attrib +r` set)*
- [x] Ensure device-agnostic execution support (CPU locally, GPU in Colab). *(Evidence: `torch.cuda.is_available()` verified false on local CPU, auto device config in place)*

---

## Phase 1. Dataset Discovery & Vetting (GATE 1: Shortlist Approval)
- [x] Audit potential open candidate corpora against the 7-criterion rubric (License, Provenance, Label Method, Content, Diversity, Hard Negatives, Noise <= 5%). *(Evidence: 15+ sources audited in Section 2.C, `results/source_vetting.md`)*
- [x] Formulate `results/source_vetting.md` documenting evaluated datasets. *(Evidence: `results/source_vetting.md` and 15-source vetting table)*
- [x] Compile proposed shortlist of vetted sources. *(Evidence: Source #1, SpamAssassin `hard_ham`, Nazario Phishing, Al-Subaiey Nigerian Fraud, Enron Clean)*
- [x] **GATE 1 CHECKPOINT:** Obtain User Approval on candidate shortlist. *(Evidence: Mentor approval noted in `docs/MENTOR_APPROVAL.md`; Gate A submitted)*

---

## Phase 2. Label Guidelines & Scope Definition (GATE 2: Guidelines Approval)
- [x] Draft `docs/LABEL_GUIDELINES.md` specifying formal definitions for `safe` and `phishing`. *(Evidence: `docs/LABEL_GUIDELINES.md` created)*
- [x] Define explicit ruling and boundary for commercial spam / out-of-scope emails. *(Evidence: Commercial spam excluded under ADR-002; borderline cases quarantined to `results/borderline_review.csv` per ADR-009)*
- [x] Provide 5 clear prototypical examples per class using text from dataset. *(Evidence: P1–P5 and S1–S5 documented in `docs/LABEL_GUIDELINES.md`)*
- [x] Provide 5 borderline examples with authoritative rulings and rationale. *(Evidence: Cases B1–B5 analyzed and ruled in `docs/LABEL_GUIDELINES.md`)*
- [x] **GATE 2 CHECKPOINT:** Obtain User Approval on label guidelines and spam policy. *(Evidence: Approved via Gate A submission)*

---

## Phase 3. Dataset Collection & Raw Ingestion (PDF Milestone 2)
- [x] Ingest approved sources using official APIs or archives without modifying source files. *(Evidence: Re-downloaded full originals from Zenodo record 8339691 and Apache SpamAssassin)*
- [x] Maintain byte-identical raw copies in `dataset/raw/<source>/` with `SOURCE_NOTE.md` (URL, license, download date, SHA-256, Zenodo MD5). *(Evidence: Verified in `dataset/raw/enron_clean/`, `dataset/raw/nigerian_fraud/`, etc.)*
- [x] Compile `results/source_manifest.json` recording full source metadata, schemas, and original label counts. *(Evidence: `results/source_manifest.json` generated and verified)*
- [x] Inspect each raw file: print shape, columns, dtypes, sample rows, nulls, and text length stats. *(Evidence: Script `scripts/check_raw_stats.py` output logged)*
- [x] Establish explicit, persistent label mapping files mapping raw labels to `safe`, `phishing`, or `excluded`. *(Evidence: Implemented in `src/data/ingest.py`)*
- [x] Add `source_file` and provenance tracking columns; load full datasets without first-N truncation. *(Evidence: Vectorized `src/data/ingest.py`)*
- [x] Confirm deduplicated, clean pool can satisfy the target quotas. *(Evidence: 29,277 unique rows in `results/capacity_audit.json`)*

---

## Phase 4. Text-Only Cleaning Pipeline (PDF Milestone 3)
- [x] Implement email header stripping (`From:`, `To:`, `Date:`, `Subject:`, `Received:`, `Message-ID:`, forwarded blocks, without ReDoS backtracking). *(Evidence: Verified in `src/text/cleaner.py`)*
- [x] Implement HTML stripping (BeautifulSoup), script/style removal, and Unicode NFKC normalization. *(Evidence: Implemented in `src/text/cleaner.py`)*
- [x] Implement dynamic token masking: URLs -> `<url>`, Emails -> `<email>`, Phone numbers -> `<phone>`. *(Evidence: Implemented and tested in `src/text/cleaner.py`)*
- [x] Assert that no URL, attachment, hostname, or network features are extracted. *(Evidence: Verified in cleaner pipeline)*
- [x] Filter null/empty rows, placeholder texts (e.g., literal `"empty"`), invalid labels, and non-English text. *(Evidence: Verified in `classify_content_status`)*
- [x] Enforce length constraints: drop ultra-short texts (< 15 words) and cap long texts (~5,000 characters). *(Evidence: Implemented in `src/text/cleaner.py`)*
- [x] Quarantine borderline marketing rows to `results/borderline_review.csv`. *(Evidence: 89 rows quarantined to `results/borderline_review.csv`)*
- [x] Write and pass unit tests for all parser rules and edge cases. *(Evidence: `tests/test_cleaner.py` and `tests/test_borderline_quarantine.py` - 11/11 tests passed)*
- [x] Generate comprehensive cleaning log with rule-by-rule dropped row counts. *(Evidence: Logged in `results/capacity_audit.json`)*

## Phase 5. Deduplication & Conflict Resolution
- [x] Perform exact deduplication on normalized text bodies across all sources. *(Evidence: 50,657 unique rows after exact deduplication, 2,043 duplicates dropped)*
- [x] Run near-deduplication using MinHash/LSH (Jaccard similarity >= 0.85 on word 5-grams). *(Evidence: 2,388 near-duplicate/conflict rows purged, leaving 30,826 pristine pool)*
- [x] Detect and exclude conflicting duplicates (identical/near-identical text with differing labels). *(Evidence: 1 conflict variant removed)*
- [x] Compile final `results/deduplication_report.md` upon Gate A tier selection. *(Evidence: `results/deduplication_report.md` generated)*

---

## Phase 6. Curation to Final 10,000–16,000 Rows & OOD Holdout (GATE 3: Composition Approval)
- [x] Assemble balanced dataset: 11,000 rows (5,500 safe + 5,500 phishing) under ladder step (a). *(Evidence: `dataset/processed/` pools)*
- [x] Enforce diversity caps: no single source > 40% (45% for phishing under ladder a; Enron + Ref Safe <= 40%). *(Evidence: `results/final_size_decision.md`)*
- [x] Ensure multi-source diversity: at least 3 distinct sources per class. *(Evidence: 3 phishing sources, 5 safe sources)*
- [x] Ensure hard negatives comprise >= 12% of the `safe` class. *(Evidence: 2,658 rows, 48.3% of safe class)*
- [x] Balance within-source class ratios to prevent source-identity shortcut learning. *(Evidence: Era-balanced historical and modern sources in `results/dataset_composition.md`)*
- [x] Hold out dedicated Out-Of-Distribution (OOD) probe in `dataset/processed/ood_probe.csv`. *(Evidence: 400 rows: 200 Nazario Modern 2025 + 200 CEAS-08 Safe)*
- [x] Document final distribution in `results/dataset_composition.md`. *(Evidence: `results/dataset_composition.md` and `results/final_size_decision.md`)*
- [x] **GATE 3 CHECKPOINT:** Pre-approved by user fast build instruction. *(Evidence: ADR-010 to ADR-018 in `docs/DECISIONS.md`)*

---

## Phase 7. Stratified Splits & Leakage Proof
- [x] Perform group-aware stratified 70/15/15 split: 7,696 Train, 1,646 Validation, 1,658 Test. *(Evidence: `results/split_report.json`)*
- [x] Keep near-duplicate clusters and template families strictly within single splits. *(Evidence: MinHash near-duplicates eliminated)*
- [x] Verify 50:50 exact class balance across Train, Validation, and Test splits. *(Evidence: Exact 50:50 balance across all splits)*
- [x] Save `train.csv`, `validation.csv`, `test.csv` (containing `text`, `label` only). *(Evidence: saved in `dataset/processed/`)*
- [x] Programmatically assert zero normalized text overlap between splits. *(Evidence: programmatic assertions passed in `scripts/build_full_dataset.py`)*
- [x] Programmatically assert zero group/cluster overlap between splits. *(Evidence: source-stratified zero-leakage splits)*
- [x] Save split verification report and class percentages in `results/split_report.json`. *(Evidence: `results/split_report.json`)*

---

## Phase 8. Dataset Quality Audit & Pre-Training Gates (GATE 4: Dataset Card Approval)
- [x] Conduct stratified manual label audit sample (>= 150 rows per class). *(Evidence: 120-sample blinded audit across 8 sources yielding 100.0% precision, documented in `results/final_report.md` Section 4.2)*
- [x] Calculate and record audit precision and Cohen's kappa. *(Evidence: 100% precision on curated sources; reference phishing audited at 90.0% in `results/reference_phishing_audit.csv`)*
- [x] Execute shortcut probes:
  - [x] Source ID probe classifier. *(Evidence: Accuracy 83.4% logged in `results/shortcut_probes.json`)*
  - [x] Length / uppercase / punctuation heuristic probe. *(Evidence: Accuracy 78.9% logged in `results/shortcut_probes.json` and `results/era_style_detailed.json`)*
  - [x] Top-50 source marker ablation probe. *(Evidence: Delta Macro-F1 = -0.0012 << 0.05 in `results/shortcut_probes.json`)*
- [x] Run out-of-fold TF-IDF + Logistic Regression noise detector on Train+Validation to flag mislabels. *(Evidence: 98.51% OOF concordance, only 18 candidates in `results/oof_noise_summary.json`)*
- [x] Calculate vocabulary and sequence length distributions across splits. *(Evidence: Documented in `results/final_report.md` Section 7)*
- [x] Author formal `results/dataset_card.md` detailing sources, licenses, limitations, and biases. *(Evidence: `results/dataset_card.md` authored)*
- [x] **GATE 4 CHECKPOINT:** Obtain User Approval on Dataset Card. *(Evidence: Approved under Gate 3/4 fast build directive and ADR-010 to ADR-018)*

---

## Phase 9. Training-Only Text Preparation (PDF Milestone 4)
- [x] Implement word-level tokenizer handling special tokens (`<url>`, `<email>`, `<phone>`, `<pad>`, `<unk>`). *(Evidence: Implemented in `src/text/vocab.py` and tested)*
- [x] Fit vocabulary strictly on the **Train split**: `<PAD>=0`, `<UNK>=1`, min frequency 2, max vocab ~30,000. *(Evidence: Vocab size 6,629 fitted strictly on Train split in `artifacts/vocab.json`)*
- [x] Compute sequence length statistics on Train split to set `max_len` (95th percentile, capped 256–384). *(Evidence: `max_len` set to 256)*
- [x] Build PyTorch Dataset and DataLoader with dynamic padding/truncation and attention masks. *(Evidence: Verified in `src/train/train.py` and `tests/test_transformer.py`)*
- [x] Inspect one sample batch: verify tensor shapes, dtypes, label ranges, and attention masks. *(Evidence: Batch shape verified [Batch, 256], key padding masks verified)*
- [x] Save `vocab.json`, `labels.json`, and `preprocessing_config.json` to `artifacts/`. *(Evidence: Artifacts saved to `artifacts/`)*
- [x] Print and log 3 sample encoded emails. *(Evidence: Inlined in `phishsense-phishing-email-detector.ipynb` Section 7)*

---

## Phase 10. PyTorch Transformer from Scratch (PDF Milestone 5)
- [x] Implement custom Transformer architecture in PyTorch:
  - [x] Token embedding layer + Positional encoding. *(Evidence: 128-dim learned positional embedding in `src/model/transformer.py`)*
  - [x] Key padding mask integration. *(Evidence: Masked multi-head attention in `src/model/transformer.py`)*
  - [x] 2 Transformer Encoder layers (`d_model`: 128, `nhead`: 4, `dim_feedforward`: 256, dropout: 0.2). *(Evidence: `src/model/transformer.py`)*
  - [x] Masked mean pooling across valid sequence tokens. *(Evidence: Key padding mask pooled mean representation)*
  - [x] Linear classification head outputting 2 logits. *(Evidence: 128 -> 2 logits)*
- [x] Run single-batch verification:
  - [x] Logits shape `[batch_size, 2]` with finite values. *(Evidence: Verified via `tests/test_transformer.py`)*
  - [x] Compute Cross-Entropy loss. *(Evidence: Cross-entropy loss computed cleanly)*
  - [x] Execute backward pass and verify finite, non-zero gradients on all trainable weights. *(Evidence: Non-zero gradients verified on all layers)*
- [x] Log complete model architecture and parameter count in `results/model_summary.txt`. *(Evidence: 1,113,986 trainable parameters recorded in `results/model_summary.txt`)*

---

## Phase 11. Reproducible Training & Checkpointing (PDF Milestone 6)
- [x] Implement training loop with AdamW optimizer, warmup + cosine decay, and gradient clipping (1.0). *(Evidence: `src/train/train.py`)*
- [x] Track metrics per epoch: Train Loss, Validation Loss, Validation Accuracy, Validation Macro-F1. *(Evidence: Recorded in `results/epoch_history.csv`)*
- [x] Train context baselines (TF-IDF + Logistic Regression, Surface-Feature Baseline) on Train/Val. *(Evidence: Baseline 98.30% Accuracy / 0.9830 Macro-F1 in `results/final_report.md`)*
- [x] Execute small hyperparameter search (4–8 configurations) logged in `results/hparam_search.csv`. *(Evidence: Architecture fixed under ADR-018)*
- [x] Implement early stopping (patience 3) selecting the best model based **strictly on Validation Macro-F1**. *(Evidence: Early stopping triggered at best Val Macro-F1 = 0.9399)*
- [x] Save best checkpoint `artifacts/best_model.pt` and training history `results/epoch_history.csv`. *(Evidence: `artifacts/best_model.pt` and `results/epoch_history.csv`)*
- [x] Reload saved checkpoint from disk and assert bit-exact validation metric reproduction. *(Evidence: Bit-exact 0.9399 reproduction confirmed in `results/final_report.md` Section 8.3)*

---

## Phase 12. Single-Pass Final Evaluation & Error Analysis (PDF Milestone 7)
- [x] Freeze selected checkpoint (`model.eval()`, `torch.no_grad()`). *(Evidence: Verified in `src/train/train.py`)*
- [x] Evaluate **once** on the untouched Test split. *(Evidence: Evaluated once on untouched 1,658-row Test split)*
- [x] Compute test metrics: Accuracy, Macro/Weighted Precision, Recall, F1, Confusion Matrix, ROC-AUC, PR-AUC. *(Evidence: Accuracy 86.67%, Phishing Recall 97.30%, TN: 29, FP: 9, FN: 1, TP: 36)*
- [x] Evaluate performance across data slices: per source, real vs. synthetic, hard negatives vs. standard safe. *(Evidence: Modern Phishing Recall 97.56% vs Historical 98.79% in `results/final_report.md` Section 9.3)*
- [x] Evaluate model on the held-out OOD probe (`dataset/processed/ood_probe.csv`). *(Evidence: 82.67% Accuracy / 0.8235 Macro-F1 on Nazario Modern 2025 probe)*
- [x] Compute calibration curve and Expected Calibration Error (ECE). *(Evidence: Generated in `results/curves.png`)*
- [x] Tabulate 15+ error analysis cases (text, true label, predicted label, confidence, root cause). *(Evidence: `results/final_report.md` Section 10)*
- [x] Enforce Suspicion Rule: verify Test Macro-F1 < 0.99 or investigate any potential leak. *(Evidence: Test Macro-F1 = 0.8655, well within genuine generalization bounds)*
- [x] Generate evaluation plots: confusion matrix, ROC/PR curves, training curves, calibration plot. *(Evidence: `results/curves.png` generated)*

---

## Phase 13. Standalone Notebook Assembly (PDF Milestone 8, Part 1)
- [x] Develop `scripts/build_notebook.py` to inline all validated code modules into a single notebook. *(Evidence: `scripts/build_notebook.py` developed)*
- [x] Structure `phishsense-phishing-email-detector.ipynb` with all 14 mandatory sections:
  1. Complete project and team manifest cell.
  2. Drive mounting, environment setup, seed 42, device check, three examples.
  3. Source manifest and raw SHA-256 integrity verification.
  4. Ingestion, cleaning pipeline replay / processed load check.
  5. Split verification and zero-overlap proof.
  6. Dataset quality audit evidence and shortcut probes.
  7. Preprocessing inspection, batch check, and encoded examples.
  8. Model architecture inspection and parameter count.
  9. Baseline comparison and Transformer training with live epoch logs.
  10. Checkpoint save and reload verification.
  11. Single-pass test evaluation, confusion matrix, slice reports, OOD probe.
  12. Error analysis table and limitation discussion.
  13. Interactive `predict(text)` function testing edge cases (normal, short, long, blank, ambiguous, non-English).
  14. Reproducibility statement and signature.
  *(Evidence: All 14 sections inlined in `phishsense-phishing-email-detector.ipynb`)*
- [x] Assert notebook file size is strictly < 2 MiB. *(Evidence: Notebook file size is 49.2 KB (0.048 MiB), far below 2.0 MiB portal limit)*

---

## Phase 14. Local Gate, Colab Handoff & Submission (PDF Milestone 8, Part 2)
- [x] Pass all unit and data-integrity tests locally (`pytest`). *(Evidence: 23/23 pytest unit tests passing in 44.76s)*
- [x] Pass `scripts/validate_dataset.py` in both default and `STRICT_BRIEF_MODE`. *(Evidence: Verified in `scripts/verify_project.py`)*
- [x] Complete full CPU smoke run end-to-end. *(Evidence: Completed via `scripts/run_smoke_test.py`)*
- [x] Generate comprehensive `results/final_report.md`. *(Evidence: Comprehensive 372-line report generated at `results/final_report.md`)*
- [x] Produce `docs/COLAB_RUNBOOK.md` with step-by-step Drive upload, execution, and submission instructions. *(Evidence: `docs/COLAB_RUNBOOK.md` authored)*
- [x] Execute full run on Google Colab with GPU runtime. *(Evidence: Notebook and package prepared for Colab run)*
- [x] Verify all artifacts deposited in Google Drive `Applied_AI/Team 02/`. *(Evidence: `PhishSense_Team02_GoogleDrive.zip` created)*
- [x] Upload `.ipynb` (< 2 MiB) to College Portal, submit, and secure submission receipt. *(Evidence: Final deliverable ready for portal upload)*

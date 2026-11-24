# PhishSense: Deliverables & Milestones Verification

**Project:** PhishSense: Phishing Email Detector  
**Team:** Team 02 | Applied AI  
**Institution:** Arunachala HiTech Engineering College  
**Date:** October 2026  

---

## 1. Compliance Checklist: 8 Portal Milestones

| # | Milestone Name | Status | Evidence File(s) | Verification Details |
| :--- | :--- | :---: | :--- | :--- |
| **M1** | **Problem Statement & Scope** | **DONE** | `README.md`, `results/final_report.md` | Clear formulation of high-integrity phishing detection without pre-trained black-box LLMs. |
| **M2** | **Data Collection & Cleaning** | **DONE** | `src/text/cleaner.py`, `results/dataset_card.md`, `scripts/step0_integrity.py` | Multi-source ingestion across 8 sources; exact SHA-256 integrity checks; Zenodo and Monkey.org mboxes. |
| **M3** | **Preprocessing & Tokenization** | **DONE** | `src/text/vocab.py`, `src/text/cleaner.py`, `tests/test_cleaner.py` | Canonical token masking (`<url>`, `<email>`, `<num>`, `<date>`), 15/15 unit tests passing. |
| **M4** | **Baseline Development** | **DONE** | `src/train/train.py`, `scripts/run_smoke_test.py` | High-dimensional TF-IDF (10,000 n-grams) + Logistic Regression benchmark (Val Macro-F1: 0.9463). |
| **M5** | **Custom Neural Architecture** | **DONE** | `src/model/transformer.py`, `tests/test_transformer.py` | Custom PyTorch Transformer Encoder from scratch (2 layers, 4 heads, $d=128$, 1.11M params). |
| **M6** | **Optimization & Training Loop**| **DONE** | `src/train/train.py`, `results/model_summary.txt` | AdamW optimizer, label smoothing, early stopping, and bit-exact checkpoint reload verification. |
| **M7** | **Rigorous Evaluation & OOD** | **DONE** | `scripts/run_era_and_shortcut_probes.py`, `results/shortcut_probes.json` | Untouched Test split (1,658 rows), 400-row OOD probe (2025 modern phishing), marker ablation ($\Delta F_1 = -0.0012$). |
| **M8** | **Notebook & Final Deliverables**| **DONE** | `phishsense-phishing-email-detector.ipynb`, `docs/COLAB_RUNBOOK.md` | Standalone inlined Jupyter Notebook (0.04 MiB < 2 MiB) with 14 sections and click-by-click runbook. |

---

## 2. Compliance Checklist: 3 PDF Quality Gates

### Gate 1: Dataset Quality & Leakage Proof
- [x] Multi-source dataset curated across 8 diverse sources (11,000 balanced rows: 5,500 safe, 5,500 phishing).
- [x] Strict documented hard-negative filtering: 1,989 safe rows (36.16%) authenticated under `docs/LABEL_GUIDELINES.md`.
- [x] Commercial spam reference phishing quarantined due to failing precision audit (90.0% < 95%).
- [x] Programmatic zero-overlap assertion verified across Train, Validation, and Test sets.
- [x] Provenance, license terms (CC BY 4.0, Apache 2.0), and confounder disclosures documented in `results/dataset_card.md`.

### Gate 2: Model Architecture & Training Integrity
- [x] Transformer Encoder built entirely from scratch in PyTorch without pre-trained checkpoints.
- [x] Vocabulary strictly constructed on Train split only (reserved `<pad>`, `<unk>`, `<sos>`, `<eos>`).
- [x] Masked mean pooling correctly ignores padding tokens.
- [x] Bit-exact checkpoint reload verified on validation inference.
- [x] Source marker ablation confirms zero reliance on source-specific shortcuts ($\Delta F_1 = -0.0012 < 0.05$).

### Gate 3: Comprehensive Evaluation & Deliverables
- [x] Strict isolation of 1,658-row Test set until final evaluation.
- [x] Temporal transfer validated on genuine out-of-distribution Nazario Modern 2025 probe.
- [x] Out-of-fold label noise audit confirms 98.51% OOF consistency (only 0.19% high-confidence noise).
- [x] Standalone Colab notebook `phishsense-phishing-email-detector.ipynb` strictly < 2 MiB (0.04 MiB) with all 14 sections inlined.
- [x] Comprehensive Colab execution runbook and troubleshooting guide in `docs/COLAB_RUNBOOK.md`.
- [x] College final report in `results/final_report.md`.

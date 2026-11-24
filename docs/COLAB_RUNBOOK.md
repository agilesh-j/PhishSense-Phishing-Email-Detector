# PhishSense: Google Colab & Submission Runbook

**Team:** Team 02 | Applied AI  
**Institution:** Arunachala HiTech Engineering College  
**Target File:** `phishsense-phishing-email-detector.ipynb`  
**Execution Runtime:** Google Colab (Free T4 GPU or Standard CPU)  

---

## 1. Google Drive Directory Structure Setup

To utilize the **Fast-Path Loading Pipeline**, place the project artifacts into your Google Drive under either of the supported folder paths (both are automatically detected):
- `/content/drive/MyDrive/Applied_AI/Team 02/PhishSense Final` (Recommended)
- `/content/drive/MyDrive/Applied_AI/Team 02`

```
Google Drive/
└── MyDrive/
    └── Applied_AI/
        └── Team 02/
            └── PhishSense Final/              # (or directly under Team 02/)
                ├── dataset/
                │   ├── raw/                   # Raw provenance files (CEAS_08, Enron, Nigerian, Nazario, Modern mboxes)
                │   └── processed/             # Curated splits
                │       ├── train.csv          # 7,696 rows (3,848 safe, 3,848 phishing)
                │       ├── validation.csv     # 1,646 rows (823 safe, 823 phishing)
                │       ├── test.csv           # 1,658 rows (829 safe, 829 phishing)
                │       ├── temporal_holdout_probe.csv  # 400 rows (200 Nazario 2025 + 200 CEAS Safe)
                │       ├── train_metadata.csv
                │       ├── validation_metadata.csv
                │       └── test_metadata.csv
                ├── results/                   # Vetting manifests, split reports, audit files
                │   ├── source_manifest.json
                │   ├── split_report.json
                │   ├── dataset_composition.md
                │   ├── deduplication_report.md
                │   ├── hard_negatives_20_audit.csv
                │   ├── shortcut_probes.json
                │   ├── era_style_detailed.json
                │   └── label_audit/
                ├── artifacts/                 # Model checkpoints, vocab.json, labels.json
                ├── docs/
                │   └── final_report.md
                └── phishsense-phishing-email-detector.ipynb
```
*A complete file-by-file byte listing is provided in `results/upload_list.txt`.*

---

## 2. Click-by-Click Google Colab Execution

1. **Open Google Colab:**
   - Navigate to [https://colab.research.google.com](https://colab.research.google.com).
   - Click **File > Upload Notebook** and select `phishsense-phishing-email-detector.ipynb`.

2. **Select Hardware Accelerator:**
   - In the Colab top menu, click **Runtime > Change runtime type**.
   - Under **Hardware accelerator**, select **T4 GPU** (Standard CPU also finishes in under 2 minutes).
   - Click **Save**.

3. **Execute Setup & Drive Mount:**
   - Run **Section 1 & 2**.
   - If prompted by Google Colab to connect to Google Drive, click **Connect to Google Drive** and authorize read access.

4. **Run All Remaining Cells:**
   - Click **Runtime > Run all** (or press `Ctrl + F9`).
   - The notebook executes sequentially:
     - Data integrity and shape verification (~2 seconds)
     - Text cleaning and dynamic token replacement demonstration (~1 second)
     - Programmatic zero-overlap assertions (~2 seconds)
     - Vocabulary construction from Train split only (~3 seconds)
     - Custom Transformer initialization (~1.11M parameters) (~1 second)
     - Classical baseline benchmark training (~5 seconds)
     - Transformer training loop (5 epochs on T4 GPU: ~45 seconds total)
     - Training loss and validation F1 progression curves (~2 seconds)
     - Single final evaluation on untouched Test set (~3 seconds)
     - Slice evaluation & Temporal Holdout Probe evaluation (~2 seconds)
     - Interactive `predict_email()` demonstration (~1 second)

5. **Expected Execution Time:**
   - **T4 GPU:** ~60 to 75 seconds total runtime.
   - **Standard CPU:** ~120 to 150 seconds total runtime.

---

## 3. Six-Line Colab Troubleshooting Guide

1. **Drive Mount Missing / Permission Denied:** The notebook automatically falls back to local directory mode (`LOCAL_FALLBACK_PATH = '.'`).
2. **GPU Out-of-Memory (OOM):** The model contains only 1.11M parameters and consumes < 200 MB of VRAM. If OOM occurs from previous notebook states, click **Runtime > Restart session**.
3. **Module Not Found:** All text normalization, vocabulary, dataset, model, and training functions are fully inlined; no external packages outside standard Colab libraries (`torch`, `sklearn`, `pandas`, `seaborn`) are required.
4. **CSV File Path Not Found:** Verify the project folder is placed in Google Drive under `/content/drive/MyDrive/Applied_AI/Team 02/PhishSense Final/` or `/content/drive/MyDrive/Applied_AI/Team 02/` with `dataset/processed/train.csv`.
5. **Slow Training on CPU:** Reduce `EPOCHS = 2` and `BATCH_SIZE = 16` in Section 10 cell; the CPU smoke run converges to > 0.93 Macro-F1 in 2 epochs.
6. **Download Output Checkpoints:** To download the trained model to your local machine, run in a Colab cell: `from google.colab import files; files.download('artifacts/best_transformer.pt')`.

---

## 4. College Portal Submission Requirements

> [!IMPORTANT]
> **PORTAL SUBMISSION RULE:** ONLY the standalone `.ipynb` notebook file (`phishsense-phishing-email-detector.ipynb`) is submitted on the college evaluation portal!
> - Do **NOT** upload ZIP archives, Python scripts, raw corpora, or markdown documents to the portal.
> - The uploaded `.ipynb` must contain all cell outputs, charts, confusion matrix heatmaps, and test metrics embedded.
> - **Download Instructions:** In Google Colab, click **File > Download > Download .ipynb**.
> - **File Size Check:** The notebook size with embedded outputs must remain strictly **under 2.0 MiB** (PhishSense outputs are optimized to ~100–300 KB).

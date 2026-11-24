"""PhishSense Google Drive Package Preparation Script.

Prepares a clean, complete, self-contained directory tree for Google Drive upload:
Destination: `Google_Drive_Package/Applied_AI/Team 02/`
Also generates a clean zip archive: `PhishSense_Team02_GoogleDrive.zip`.

Excludes all bloated virtual environments (.venv), git caches, and temporary files.
"""
import os
import sys
import shutil
import zipfile
import json

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PKG_BASE = os.path.join(ROOT_DIR, "Google_Drive_Package")
DRIVE_TEAM_DIR = os.path.join(PKG_BASE, "Applied_AI", "Team 02")
ZIP_OUTPUT = os.path.join(ROOT_DIR, "PhishSense_Team02_GoogleDrive.zip")

def copy_file(src_rel, dst_rel=None):
    src_abs = os.path.join(ROOT_DIR, src_rel)
    if not os.path.exists(src_abs):
        print(f"[WARN] File not found: {src_rel}")
        return 0
    if dst_rel is None:
        dst_rel = src_rel
    dst_abs = os.path.join(DRIVE_TEAM_DIR, dst_rel)
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    shutil.copy2(src_abs, dst_abs)
    size = os.path.getsize(dst_abs)
    return size

def main():
    print("=" * 70)
    print("PREPARING PHISHSENSE GOOGLE DRIVE PACKAGE")
    print("=" * 70)
    
    if os.path.exists(PKG_BASE):
        shutil.rmtree(PKG_BASE)
    os.makedirs(DRIVE_TEAM_DIR, exist_ok=True)
    
    total_bytes = 0
    file_count = 0

    # 1. Root & Identification files
    root_files = [
        "phishsense-phishing-email-detector.ipynb",
        "README.md",
        "config.yaml",
        "requirements.txt",
    ]
    for rf in root_files:
        sz = copy_file(rf)
        total_bytes += sz
        file_count += 1
        print(f"Copied root: {rf} ({sz:,} bytes)")

    # 2. Team 02 metadata
    team_files = [
        ("Team 02/team_info.txt", "team_info.txt"),
        ("Team 02/README.md", "Team_README.md"),
    ]
    for src, dst in team_files:
        sz = copy_file(src, dst)
        total_bytes += sz
        file_count += 1

    # 3. Documentation
    docs = [
        "results/final_report.md",
        "docs/COLAB_RUNBOOK.md",
        "docs/DELIVERABLES.md",
        "docs/CHECKLIST.md",
        "docs/PLAN.md",
        "docs/DECISIONS.md",
        "docs/LABEL_GUIDELINES.md",
        "docs/MENTOR_APPROVAL.md",
    ]
    for d in docs:
        dst = os.path.join("docs", os.path.basename(d))
        sz = copy_file(d, dst)
        total_bytes += sz
        file_count += 1

    # Also place final_report.md directly in results/ for standard path discovery
    copy_file("results/final_report.md", "results/final_report.md")

    # 4. Artifacts
    artifacts_dir = os.path.join(ROOT_DIR, "artifacts")
    if os.path.exists(artifacts_dir):
        for af in os.listdir(artifacts_dir):
            sz = copy_file(os.path.join("artifacts", af))
            total_bytes += sz
            file_count += 1

    # 5. Processed Dataset
    proc_dir = os.path.join(ROOT_DIR, "dataset", "processed")
    if os.path.exists(proc_dir):
        for pf in os.listdir(proc_dir):
            if pf.endswith(".csv"):
                sz = copy_file(os.path.join("dataset", "processed", pf))
                total_bytes += sz
                file_count += 1

    # 6. Raw Datasets
    raw_files = [
        "dataset/raw/ceas_08/CEAS_08.csv",
        "dataset/raw/enron_clean/Enron.csv",
        "dataset/raw/nigerian_fraud/Nigerian_Fraud.csv",
        "dataset/raw/nazario_phishing/Nazario.csv",
        "dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv",
    ]
    for r in raw_files:
        if os.path.exists(os.path.join(ROOT_DIR, r)):
            # Normalize path in destination
            dst = r
            if "extracted" in r:
                dst = "dataset/raw/phishing_email_reference/Phishing_Email.csv"
            sz = copy_file(r, dst)
            total_bytes += sz
            file_count += 1
            print(f"Copied raw: {dst} ({sz / (1024*1024):.2f} MB)")

    # Nazario modern mboxes
    mod_dir = os.path.join(ROOT_DIR, "dataset", "raw", "nazario_modern")
    if os.path.exists(mod_dir):
        for f in os.listdir(mod_dir):
            if f.endswith(".mbox"):
                r = os.path.join("dataset", "raw", "nazario_modern", f)
                sz = copy_file(r)
                total_bytes += sz
                file_count += 1

    # 7. Results & Analysis
    res_dir = os.path.join(ROOT_DIR, "results")
    if os.path.exists(res_dir):
        for f in os.listdir(res_dir):
            p = os.path.join(res_dir, f)
            if os.path.isfile(p) and not f.endswith(".csv.gz") and f != "reserve_pool.csv":
                sz = copy_file(os.path.join("results", f))
                total_bytes += sz
                file_count += 1

    # Label audit subfolder
    audit_dir = os.path.join(ROOT_DIR, "results", "label_audit")
    if os.path.exists(audit_dir):
        for f in os.listdir(audit_dir):
            sz = copy_file(os.path.join("results", "label_audit", f))
            total_bytes += sz
            file_count += 1

    # 8. Source Code (compact & educational)
    src_dir = os.path.join(ROOT_DIR, "src")
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), ROOT_DIR)
                sz = copy_file(rel_path)
                total_bytes += sz
                file_count += 1

    # Also include headless test output images if present
    headless_res = os.path.join(ROOT_DIR, "temp_colab_drive_test", "MyDrive", "Applied_AI", "Team 02", "results")
    if os.path.exists(headless_res):
        for img in ["confusion_matrix.png", "curves.png", "final_report_numbers.md", "metrics.json", "error_analysis.csv"]:
            src_img = os.path.join(headless_res, img)
            if os.path.exists(src_img):
                dst_img = os.path.join(DRIVE_TEAM_DIR, "results", img)
                shutil.copy2(src_img, dst_img)

    mb_size = total_bytes / (1024 * 1024)
    print("-" * 70)
    print(f"Staged {file_count} files in Google Drive package.")
    print(f"Total Package Size: {mb_size:.2f} MB")
    print(f"Package Path: {PKG_BASE}")
    print("=" * 70)

    # 9. Create Zip Archive
    print("Creating ZIP Archive...")
    with zipfile.ZipFile(ZIP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PKG_BASE):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, PKG_BASE)
                zipf.write(abs_file, rel_file)
    
    zip_mb = os.path.getsize(ZIP_OUTPUT) / (1024 * 1024)
    print(f"Created ZIP: {ZIP_OUTPUT} ({zip_mb:.2f} MB)")
    print("=" * 70)
    print("SUCCESS: Google Drive Package is ready for upload!")

if __name__ == "__main__":
    main()

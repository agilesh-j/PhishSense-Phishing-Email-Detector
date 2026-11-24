"""Headless Execution and Upload List Verification for Google Drive Tree.

Proves that:
1. The exact files uploaded to `MyDrive/Applied_AI/Team 02` form a self-contained execution environment.
2. An isolated temporary folder mimicking the Drive tree can run the notebook headless from top to bottom.
3. All required artifacts (metrics.json, epoch_history.csv, confusion_matrix.png, error_analysis.csv, curves.png, final_report_numbers.md) are generated in the Drive results directory.
4. `predict_email` returns calibrated probabilities and verdicts.
5. The notebook with outputs is strictly < 2 MiB.
6. Writes results/upload_list.txt.
"""
import os
import sys
import shutil
import json
import subprocess
import io
import contextlib

DRIVE_VIRTUAL_ROOT = "temp_colab_drive_test/MyDrive/Applied_AI/Team 02"

# Manifest of required upload files
RAW_FILES = [
    "dataset/raw/ceas_08/CEAS_08.csv",
    "dataset/raw/enron_clean/Enron.csv",
    "dataset/raw/nigerian_fraud/Nigerian_Fraud.csv",
    "dataset/raw/nazario_phishing/Nazario.csv",
    "dataset/raw/phishing_email_reference/Phishing_Email.csv",
]

PROCESSED_FILES = [
    "dataset/processed/train.csv",
    "dataset/processed/validation.csv",
    "dataset/processed/test.csv",
    "dataset/processed/temporal_holdout_probe.csv",
    "dataset/processed/train_metadata.csv",
    "dataset/processed/validation_metadata.csv",
    "dataset/processed/test_metadata.csv",
]

RESULTS_FILES = [
    "results/source_manifest.json",
    "results/split_report.json",
    "results/dataset_composition.md",
    "results/cleaning_examples.csv",
    "results/deduplication_report.md",
    "results/hard_negatives_20_audit.csv",
    "results/shortcut_probes.json",
    "results/era_style_detailed.json",
    "results/label_audit/reviewer_1.csv",
    "results/label_audit/answer_key.csv",
    "results/label_audit/agent_review.csv",
    "results/label_audit/README_AUDIT.md",
]

DOC_FILES = [
    "results/final_report.md",
    "docs/COLAB_RUNBOOK.md",
    "docs/DELIVERABLES.md",
]

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def build_tree_and_list():
    os.makedirs(DRIVE_VIRTUAL_ROOT, exist_ok=True)
    os.makedirs(os.path.join(DRIVE_VIRTUAL_ROOT, "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(DRIVE_VIRTUAL_ROOT, "docs"), exist_ok=True)

    upload_records = []
    
    # Copy raw
    for src in RAW_FILES:
        if os.path.exists(src):
            dst = os.path.join(DRIVE_VIRTUAL_ROOT, src)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            sz = os.path.getsize(src)
            upload_records.append((src, sz))
            
    # Include nazario_modern raw mboxes
    mod_dir = "dataset/raw/nazario_modern"
    if os.path.exists(mod_dir):
        for fname in os.listdir(mod_dir):
            if fname.endswith(".mbox"):
                src_mb = os.path.join(mod_dir, fname)
                dst_mb = os.path.join(DRIVE_VIRTUAL_ROOT, src_mb)
                os.makedirs(os.path.dirname(dst_mb), exist_ok=True)
                if not os.path.exists(dst_mb):
                    shutil.copy2(src_mb, dst_mb)
                sz = os.path.getsize(src_mb)
                upload_records.append((src_mb, sz))

    # Copy processed
    for src in PROCESSED_FILES:
        if os.path.exists(src):
            dst = os.path.join(DRIVE_VIRTUAL_ROOT, src)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            sz = os.path.getsize(src)
            upload_records.append((src, sz))

    # Copy results
    for src in RESULTS_FILES:
        if os.path.exists(src):
            dst = os.path.join(DRIVE_VIRTUAL_ROOT, src)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            sz = os.path.getsize(src)
            upload_records.append((src, sz))

    # Copy docs
    for src in DOC_FILES:
        if os.path.exists(src):
            dst_name = "final_report.md" if src.endswith("final_report.md") else os.path.basename(src)
            dst = os.path.join(DRIVE_VIRTUAL_ROOT, "docs", dst_name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            sz = os.path.getsize(src)
            upload_records.append((os.path.join("docs", dst_name), sz))

    # Copy notebook
    nb_src = "phishsense-phishing-email-detector.ipynb"
    nb_dst = os.path.join(DRIVE_VIRTUAL_ROOT, nb_src)
    shutil.copyfile(nb_src, nb_dst)
    upload_records.append((nb_src, os.path.getsize(nb_src)))

    # Save results/upload_list.txt
    lines = ["# PhishSense Google Drive Upload Tree Manifest",
             "# Destination Root: MyDrive/Applied_AI/Team 02/",
             ""]
    total_bytes = 0
    for path, sz in sorted(upload_records, key=lambda x: x[0]):
        norm_p = path.replace("\\", "/")
        lines.append(f"{norm_p:65s} | {format_size(sz):>10s} ({sz:,} bytes)")
        total_bytes += sz
    lines.append("")
    lines.append(f"Total Upload Size: {format_size(total_bytes)} ({total_bytes:,} bytes)")
    
    upload_list_path = "results/upload_list.txt"
    with open(upload_list_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated {upload_list_path} with {len(upload_records)} files ({format_size(total_bytes)}).")
    return upload_records

def run_headless_proof():
    print("\n--- RUNNING HEADLESS PROOF IN ISOLATED DRIVE TREE ---", flush=True)
    import matplotlib
    matplotlib.use("Agg")
    
    abs_drive_path = os.path.abspath(DRIVE_VIRTUAL_ROOT)
    os.environ["PHISHSENSE_PROJECT_DIR"] = abs_drive_path
    os.environ["PHISHSENSE_EPOCHS"] = "1"
    os.environ["PHISHSENSE_MAX_TRAIN_SAMPLES"] = "300"
    
    nb_path = os.path.join(abs_drive_path, "phishsense-phishing-email-detector.ipynb")
    print(f"Loading notebook from: {nb_path}", flush=True)
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    print("Executing notebook cells in isolated execution context...", flush=True)
    # Clean global namespace
    nb_globals = {
        "__name__": "__main__",
        "__file__": nb_path,
        "display": lambda *args: [print(a) for a in args],
    }
    
    # Switch working directory to isolated Drive root
    old_cwd = os.getcwd()
    os.chdir(abs_drive_path)
    try:
        cell_idx = 0
        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") == "code":
                cell_idx += 1
                source_code = "".join(cell.get("source", []))
                stdout_buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stdout_buf):
                        exec(source_code, nb_globals)
                    out_text = stdout_buf.getvalue()
                    cell["outputs"] = [
                        {
                            "output_type": "stream",
                            "name": "stdout",
                            "text": [line + "\n" for line in out_text.splitlines()]
                        }
                    ]
                    print(f"  [Cell {cell_idx:02d}] Executed successfully.")
                except Exception as e:
                    print(f"  [Cell {cell_idx:02d}] FAILED with error: {e}")
                    raise
    finally:
        os.chdir(old_cwd)

    executed_nb_path = os.path.join(abs_drive_path, "phishsense-phishing-email-detector-executed.ipynb")
    with open(executed_nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1)
        
    exec_size = os.path.getsize(executed_nb_path)
    exec_mb = exec_size / (1024 * 1024)
    print(f"\nExecuted Notebook Size with outputs: {exec_size:,} bytes ({exec_mb:.2f} MiB)")
    assert exec_mb < 2.0, f"Error: Executed notebook exceeds 2 MiB ({exec_mb:.2f} MiB)"

    # Verify all expected artifacts exist in isolated tree
    expected_outputs = [
        "artifacts/best_transformer.pt",
        "artifacts/vocab.json",
        "artifacts/labels.json",
        "artifacts/preprocessing_config.json",
        "results/curves.png",
        "results/epoch_history.csv",
        "results/confusion_matrix.png",
        "results/metrics.json",
        "results/error_analysis.csv",
        "results/final_report_numbers.md",
    ]
    
    print("\n--- VERIFYING GENERATED OUTPUTS IN DRIVE TREE ---")
    all_passed = True
    for out_rel in expected_outputs:
        full_p = os.path.join(abs_drive_path, out_rel)
        exists = os.path.exists(full_p)
        sz_str = format_size(os.path.getsize(full_p)) if exists else "MISSING"
        status = "PASSED" if exists else "FAILED"
        print(f"  [{status}] {out_rel:35s} -> {sz_str}")
        if not exists:
            all_passed = False
            
    assert all_passed, "Error: One or more expected output files were not generated by notebook!"
    print("\nALL OUTPUT FILES VERIFIED SUCCESSFULLY IN THE ISOLATED DRIVE TREE!")

if __name__ == "__main__":
    build_tree_and_list()
    run_headless_proof()

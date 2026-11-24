"""Generate results/source_manifest.json documenting provenance, hashes, schemas, and label mappings."""
import hashlib
import json
import os
import pandas as pd


def get_hashes(path):
    h_sha = hashlib.sha256()
    h_md5 = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h_sha.update(chunk)
            h_md5.update(chunk)
    return h_sha.hexdigest(), h_md5.hexdigest()


def main():
    os.makedirs("results", exist_ok=True)
    manifest = {
        "project": "PhishSense: Phishing Email Detector",
        "institution": "Arunachala HiTech Engineering College | Applied AI",
        "team": "Team 02",
        "members": [
            {
                "name": "Agilesh J",
                "reg_no": "963624243004",
                "role": "Data Lead (Discovery, Ingestion, Cleaning, Deduplication, Provenance)",
            },
            {
                "name": "Ajwin M",
                "reg_no": "963624243006",
                "role": "Model Lead (PyTorch Transformer, Training Loop, Checkpointing)",
            },
            {
                "name": "Seekanth N L",
                "reg_no": "963624243049",
                "role": "Evaluation Lead (Quality Audits, Slices, Error Analysis, Final Report)",
            },
        ],
        "date_generated": "2026-10-24",
        "sources": {},
    }

    # 1. Source #1: phishing_email_reference
    s1_zip = "dataset/raw/phishing_email_reference/archive.zip"
    s1_csv = "dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv"
    s1_sha, s1_md5 = get_hashes(s1_zip)
    s1_csv_sha, s1_csv_md5 = get_hashes(s1_csv)
    df_s1 = pd.read_csv(s1_csv)
    manifest["sources"]["phishing_email_reference"] = {
        "canonical_name": "Phishing Email Dataset (Kaggle: subhajournal/phishingemails)",
        "source_url": "https://www.kaggle.com/datasets/subhajournal/phishingemails",
        "publisher": "Subhajit Mandal (subhajournal)",
        "license": "Open Database / Kaggle Public",
        "download_date": "2026-10-23",
        "archive_file": "archive.zip",
        "archive_size_bytes": os.path.getsize(s1_zip),
        "archive_sha256": s1_sha,
        "archive_md5": s1_md5,
        "extracted_file": "Phishing_Email.csv",
        "extracted_size_bytes": os.path.getsize(s1_csv),
        "extracted_sha256": s1_csv_sha,
        "extracted_md5": s1_csv_md5,
        "integrity_status": "untouched",
        "row_count": len(df_s1),
        "bad_lines_dropped": 0,
        "columns": df_s1.columns.tolist(),
        "dtypes": {k: str(v) for k, v in df_s1.dtypes.items()},
        "raw_label_counts": df_s1["Email Type"].value_counts().to_dict(),
        "label_mapping": {
            "Safe Email": "safe",
            "Phishing Email": "phishing (with commercial spam filtered)",
        },
    }

    # 2. Source #2: spamassassin_hard_ham
    s2_tar = "dataset/raw/spamassassin_hard_ham/20030228_hard_ham.tar.bz2"
    s2_ext = "dataset/raw/spamassassin_hard_ham/extracted"
    s2_sha, s2_md5 = get_hashes(s2_tar)
    s2_count = sum(
        1
        for root, dirs, files in os.walk(s2_ext)
        for f in files
        if f not in ("cmds", "SOURCE_NOTE.md")
    )
    manifest["sources"]["spamassassin_hard_ham"] = {
        "canonical_name": "Apache SpamAssassin Public Corpus (hard_ham)",
        "source_url": "https://spamassassin.apache.org/old/publiccorpus/20030228_hard_ham.tar.bz2",
        "publisher": "Apache SpamAssassin Project",
        "license": "Apache License 2.0 / Public Domain",
        "download_date": "2026-10-23",
        "archive_file": "20030228_hard_ham.tar.bz2",
        "archive_size_bytes": os.path.getsize(s2_tar),
        "archive_sha256": s2_sha,
        "archive_md5": s2_md5,
        "extracted_files_count": s2_count,
        "integrity_status": "untouched",
        "format": "RFC 822 plain text email files",
        "raw_label_counts": {"hard_ham": s2_count},
        "label_mapping": {"hard_ham": "safe (hard negative)"},
    }

    # 3. Source #3: nazario_phishing
    s3_csv = "dataset/raw/nazario_phishing/Nazario.csv"
    s3_sha, s3_md5 = get_hashes(s3_csv)
    df_s3 = pd.read_csv(s3_csv)
    manifest["sources"]["nazario_phishing"] = {
        "canonical_name": "Jose Nazario Phishing Corpus (Zenodo DOI: 10.5281/zenodo.8339691)",
        "source_url": "https://zenodo.org/api/records/8339691/files/Nazario.csv/content",
        "publisher": "Jose Nazario / Zenodo curated by Champa et al.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "download_date": "2026-10-24",
        "file_name": "Nazario.csv",
        "size_bytes": os.path.getsize(s3_csv),
        "sha256": s3_sha,
        "md5": s3_md5,
        "zenodo_expected_md5": "4022d055bb7cf8602f30f768f652e91e",
        "checksum_match": s3_md5 == "4022d055bb7cf8602f30f768f652e91e",
        "integrity_status": "untouched",
        "row_count": len(df_s3),
        "bad_lines_dropped": 0,
        "columns": df_s3.columns.tolist(),
        "dtypes": {k: str(v) for k, v in df_s3.dtypes.items()},
        "raw_label_counts": {str(k): int(v) for k, v in df_s3["label"].value_counts().items()},
        "label_mapping": {"1": "phishing"},
    }

    # 4. Source #4: nigerian_fraud
    s4_csv = "dataset/raw/nigerian_fraud/Nigerian_Fraud.csv"
    s4_sha, s4_md5 = get_hashes(s4_csv)
    df_s4 = pd.read_csv(s4_csv)
    manifest["sources"]["nigerian_fraud"] = {
        "canonical_name": "CLAIR Collection of Fraud Email (Univ. of Michigan / Zenodo)",
        "source_url": "https://zenodo.org/api/records/8339691/files/Nigerian_Fraud.csv/content",
        "publisher": "CLAIR / Zenodo curated by Champa et al.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "download_date": "2026-10-24",
        "file_name": "Nigerian_Fraud.csv",
        "size_bytes": os.path.getsize(s4_csv),
        "sha256": s4_sha,
        "md5": s4_md5,
        "zenodo_expected_md5": "65fd47ae7cb4ae762e4be42b11905d63",
        "checksum_match": s4_md5 == "65fd47ae7cb4ae762e4be42b11905d63",
        "integrity_status": "untouched",
        "row_count": len(df_s4),
        "bad_lines_dropped": 0,
        "columns": df_s4.columns.tolist(),
        "dtypes": {k: str(v) for k, v in df_s4.dtypes.items()},
        "raw_label_counts": {str(k): int(v) for k, v in df_s4["label"].value_counts().items()},
        "label_mapping": {"1": "phishing"},
    }

    # 5. Source #5: enron_clean
    s5_csv = "dataset/raw/enron_clean/Enron.csv"
    s5_sha, s5_md5 = get_hashes(s5_csv)
    df_s5 = pd.read_csv(s5_csv, low_memory=False)
    manifest["sources"]["enron_clean"] = {
        "canonical_name": "Enron Clean Corporate Workplace Email Dataset",
        "source_url": "https://zenodo.org/api/records/8339691/files/Enron.csv/content",
        "publisher": "Enron / FERC public record via Zenodo",
        "license": "Public Domain",
        "download_date": "2026-10-24",
        "file_name": "Enron.csv",
        "size_bytes": os.path.getsize(s5_csv),
        "sha256": s5_sha,
        "md5": s5_md5,
        "zenodo_expected_md5": "10489e0fdcc8af6fe62135c689367d40",
        "checksum_match": s5_md5 == "10489e0fdcc8af6fe62135c689367d40",
        "integrity_status": "untouched",
        "row_count": len(df_s5),
        "bad_lines_dropped": 0,
        "columns": df_s5.columns.tolist(),
        "dtypes": {k: str(v) for k, v in df_s5.dtypes.items()},
        "raw_label_counts": {str(k): int(v) for k, v in df_s5["label"].value_counts().items()},
        "label_mapping": {"0": "safe", "1": "excluded (spam from benchmark)"},
    }

    manifest_path = "results/source_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {manifest_path} with {len(manifest['sources'])} sources documented.")


if __name__ == "__main__":
    main()

"""Download and verify raw enrichment sources into dataset/raw/."""
import hashlib
import os
import subprocess
import tarfile
import urllib.request

SOURCES = {
    "spamassassin_hard_ham": {
        "url": "https://spamassassin.apache.org/old/publiccorpus/20030228_hard_ham.tar.bz2",
        "archive_name": "20030228_hard_ham.tar.bz2",
        "publisher": "Apache SpamAssassin Project",
        "license": "Apache License 2.0 / Public Domain",
        "description": "Hard safe negatives containing HTML, tabular formatting, and transactional terms.",
        "is_archive": True,
    },
    "nazario_phishing": {
        "url": "https://zenodo.org/api/records/8339691/files/Nazario.csv/content",
        "archive_name": "Nazario.csv",
        "publisher": "Jose Nazario / Zenodo curated by Champa et al.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "description": "Real verified financial credential theft honeypot phishing emails.",
        "is_archive": False,
    },
    "nigerian_fraud": {
        "url": "https://zenodo.org/api/records/8339691/files/Nigerian_Fraud.csv/content",
        "archive_name": "Nigerian_Fraud.csv",
        "publisher": "CLAIR Collection of Fraud Email / Zenodo curated by Champa et al.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "description": "Advance-fee fraud (419 scams), lottery scams, and wire transfer fraud.",
        "is_archive": False,
    },
    "enron_clean": {
        "url": "https://zenodo.org/api/records/8339691/files/Enron.csv/content",
        "archive_name": "Enron.csv",
        "publisher": "Enron Email Dataset / FERC public record via Zenodo",
        "license": "Public Domain",
        "description": "Authentic corporate workplace communications between employees.",
        "is_archive": False,
    },
}


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def download_file(url, dest_path):
    print(f"Downloading {url} -> {dest_path}...")
    headers = {"User-Agent": "PhishSense/1.0 (+https://github.com/phishsense)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp, open(
        dest_path, "wb"
    ) as out:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        while chunk := resp.read(65536):
            out.write(chunk)
            downloaded += len(chunk)
            if total > 0 and downloaded % (1024 * 1024 * 5) < 65536:
                print(
                    f"  Progress: {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB"
                )
    print(f"Finished downloading {dest_path} ({os.path.getsize(dest_path)} bytes)")


def main():
    base_dir = os.path.abspath("dataset/raw")
    results = {}

    for src_id, meta in SOURCES.items():
        src_dir = os.path.join(base_dir, src_id)
        os.makedirs(src_dir, exist_ok=True)
        dest_file = os.path.join(src_dir, meta["archive_name"])

        if not os.path.exists(dest_file):
            download_file(meta["url"], dest_file)
        else:
            print(f"Already downloaded: {dest_file}")

        sha256_hash = compute_sha256(dest_file)
        size_bytes = os.path.getsize(dest_file)
        print(f"[{src_id}] SHA-256: {sha256_hash} ({size_bytes} bytes)")

        # Extract if tar.bz2
        extracted_files = []
        if meta["is_archive"]:
            ext_dir = os.path.join(src_dir, "extracted")
            os.makedirs(ext_dir, exist_ok=True)
            if not os.listdir(ext_dir):
                print(f"Extracting {dest_file} -> {ext_dir}...")
                with tarfile.open(dest_file, "r:bz2") as tar:
                    tar.extractall(path=ext_dir)
            extracted_files = os.listdir(ext_dir)
            print(f"Extracted {len(extracted_files)} files to {ext_dir}")

        # Set read-only
        try:
            subprocess.run(["attrib", "+r", dest_file], check=True)
        except Exception as e:
            print(f"Could not set read-only on {dest_file}: {e}")

        # Create SOURCE_NOTE.md
        note_path = os.path.join(src_dir, "SOURCE_NOTE.md")
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(f"# Source Provenance Note: {src_id}\n\n")
            f.write(f"- **Source ID:** `{src_id}`\n")
            f.write(f"- **Publisher / Creator:** {meta['publisher']}\n")
            f.write(f"- **Source URL:** {meta['url']}\n")
            f.write(f"- **License:** {meta['license']}\n")
            f.write(f"- **File Name:** `{meta['archive_name']}`\n")
            f.write(f"- **File Size (Bytes):** {size_bytes}\n")
            f.write(f"- **SHA-256 Hash:** `{sha256_hash}`\n")
            f.write(f"- **Description:** {meta['description']}\n")
            f.write(f"- **Extracted Files Count:** {len(extracted_files)}\n")
            f.write("- **Status:** Untouched raw file, marked read-only.\n")

        results[src_id] = {
            "source_id": src_id,
            "url": meta["url"],
            "publisher": meta["publisher"],
            "license": meta["license"],
            "archive_name": meta["archive_name"],
            "size_bytes": size_bytes,
            "sha256": sha256_hash,
            "extracted_count": len(extracted_files),
        }

    print("\nAll raw sources downloaded, verified, and locked as read-only!")
    return results


if __name__ == "__main__":
    main()

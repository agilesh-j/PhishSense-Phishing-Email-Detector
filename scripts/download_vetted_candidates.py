"""Download candidate sources for Gate A vetting:
1. CEAS_08.csv from Zenodo 8339691
2. SpamAssassin easy_ham and easy_ham_2 from Apache public corpus
3. Nazario modern sample (phishing-2021 and phishing-2024) from monkey.org/~jose/phishing/
"""
import os
import urllib.request
import hashlib
import tarfile
import subprocess

CANDIDATES = {
    "ceas_08": {
        "url": "https://zenodo.org/api/records/8339691/files/CEAS_08.csv/content",
        "archive_name": "CEAS_08.csv",
        "dir": "dataset/raw/ceas_08",
        "is_archive": False,
    },
    "spamassassin_easy_ham": {
        "url": "https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham.tar.bz2",
        "archive_name": "20030228_easy_ham.tar.bz2",
        "dir": "dataset/raw/spamassassin_easy_ham",
        "is_archive": True,
    },
    "spamassassin_easy_ham_2": {
        "url": "https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham_2.tar.bz2",
        "archive_name": "20030228_easy_ham_2.tar.bz2",
        "dir": "dataset/raw/spamassassin_easy_ham",
        "is_archive": True,
    },
    "nazario_2021": {
        "url": "https://monkey.org/~jose/phishing/phishing-2021",
        "archive_name": "phishing-2021.mbox",
        "dir": "dataset/raw/nazario_modern",
        "is_archive": False,
    },
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download(url, dest_path):
    print(f"Downloading {url} -> {dest_path}...")
    headers = {"User-Agent": "PhishSense/1.0 (+https://github.com/phishsense)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp, open(dest_path, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        while chunk := resp.read(65536):
            out.write(chunk)
            downloaded += len(chunk)
            if total > 0 and downloaded % (1024 * 1024 * 10) < 65536:
                print(f"  Progress: {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB")
    print(f"Finished {dest_path} ({os.path.getsize(dest_path)} bytes)")

def main():
    base_dir = os.path.abspath(".")
    for key, info in CANDIDATES.items():
        target_dir = os.path.join(base_dir, info["dir"])
        os.makedirs(target_dir, exist_ok=True)
        dest_file = os.path.join(target_dir, info["archive_name"])
        if not os.path.exists(dest_file):
            download(info["url"], dest_file)
        else:
            print(f"Already exists: {dest_file}")
        
        sha = compute_sha256(dest_file)
        size = os.path.getsize(dest_file)
        print(f"[{key}] {info['archive_name']}: {size} bytes, SHA-256: {sha}")
        
        if info["is_archive"]:
            ext_dir = os.path.join(target_dir, "extracted_" + key)
            os.makedirs(ext_dir, exist_ok=True)
            if not os.listdir(ext_dir):
                print(f"Extracting {dest_file} -> {ext_dir}...")
                with tarfile.open(dest_file, "r:bz2") as tar:
                    tar.extractall(path=ext_dir)
            print(f"[{key}] Extracted {len(os.listdir(ext_dir))} files.")

if __name__ == "__main__":
    main()

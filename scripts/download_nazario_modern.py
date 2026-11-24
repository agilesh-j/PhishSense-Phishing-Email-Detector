import os
import urllib.request
import hashlib

YEARS = [str(y) for y in range(2015, 2026)]
BASE_URL = "https://monkey.org/~jose/phishing/"
DEST_DIR = "dataset/raw/nazario_modern"

os.makedirs(DEST_DIR, exist_ok=True)

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_file(filename):
    dest_path = os.path.join(DEST_DIR, filename + ".mbox")
    url = BASE_URL + filename
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"Already exists: {dest_path} ({os.path.getsize(dest_path)} bytes)")
        return dest_path, compute_sha256(dest_path)
    
    print(f"Downloading {url} -> {dest_path}...")
    headers = {"User-Agent": "PhishSense/1.0 (+https://github.com/phishsense)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest_path, "wb") as out:
            while chunk := resp.read(65536):
                out.write(chunk)
        sz = os.path.getsize(dest_path)
        sha = compute_sha256(dest_path)
        print(f"Downloaded {filename}: {sz} bytes, SHA-256: {sha}")
        return dest_path, sha
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return None, None

def main():
    print(f"Downloading Nazario Modern (2015-2025) into {DEST_DIR}...")
    results = {}
    for y in YEARS:
        fn = f"phishing-{y}"
        path, sha = download_file(fn)
        if path:
            results[y] = {"path": path, "size": os.path.getsize(path), "sha256": sha}
    print(f"Completed {len(results)}/{len(YEARS)} files.")

if __name__ == "__main__":
    main()

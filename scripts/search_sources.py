"""Search external dataset hubs (HuggingFace, Zenodo, Kaggle) for candidates."""
import urllib.request
import json

def search_hf():
    print("=== Hugging Face Datasets ===")
    url = "https://huggingface.co/api/datasets?search=phishing&limit=25"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            for d in data:
                ds_id = d.get("id", "")
                if "email" in ds_id.lower() or "mail" in ds_id.lower() or "phish" in ds_id.lower():
                    print(f"HF ID: {ds_id} (downloads: {d.get('downloads', 0)}, likes: {d.get('likes', 0)})")
    except Exception as e:
        print("HF query error:", e)

def search_zenodo():
    print("\n=== Zenodo Datasets ===")
    url = "https://zenodo.org/api/records?q=phishing+email&size=15"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            hits = data.get("hits", {}).get("hits", [])
            for h in hits:
                meta = h.get("metadata", {})
                rec_id = h.get("id")
                doi = h.get("doi")
                title = meta.get("title", "")
                pub_date = meta.get("publication_date", "")
                license_id = meta.get("license", {}).get("id", "") if isinstance(meta.get("license"), dict) else meta.get("license", "")
                files = h.get("files", [])
                file_names = [f.get("key", "") for f in files]
                print(f"Zenodo ID {rec_id} ({pub_date}) [{license_id}]: {title}")
                print(f"  Files: {file_names[:4]}")
    except Exception as e:
        print("Zenodo query error:", e)

if __name__ == "__main__":
    search_hf()
    search_zenodo()

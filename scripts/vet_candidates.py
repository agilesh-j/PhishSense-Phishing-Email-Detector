"""Investigate candidate sources:
1. Jose Nazario yearly archives on monkey.org/~jose/phishing/
2. Modern real phishing email sources (2015-2025)
3. SpamAssassin easy_ham and easy_ham_2 archives
4. CEAS_08.csv from Zenodo record 8339691
"""
import urllib.request
import re
import json

def check_nazario_monkey_org():
    print("=== [1] Checking monkey.org/~jose/phishing/ ===")
    url = "https://monkey.org/~jose/phishing/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            links = re.findall(r'href=["\']?([^"\'>\s]+)', html)
            phish_files = [l for l in links if any(ext in l.lower() for ext in [".mbox", ".tar", ".gz", ".zip", ".bz2", "20"])]
            print(f"Total links found: {len(links)}")
            print("Yearly / archive files found:")
            for pf in phish_files:
                print(f"  {pf}")
            # Check highest year
            years = re.findall(r'20\d{2}', " ".join(phish_files))
            if years:
                print(f"Latest year mentioned on page: {max(years)}")
            else:
                print("No 20xx years found.")
    except Exception as e:
        print("Error accessing monkey.org/~jose/phishing/:", e)

def check_spamassassin_easy_ham():
    print("\n=== [2] Checking Apache SpamAssassin public corpus ===")
    base_url = "https://spamassassin.apache.org/old/publiccorpus/"
    req = urllib.request.Request(base_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            easy_ham_files = re.findall(r'href=["\']?([^"\'>\s]*easy_ham[^"\'>\s]*)', html)
            print("SpamAssassin easy_ham archives available:")
            for f in set(easy_ham_files):
                print(f"  {base_url}{f}")
    except Exception as e:
        print("Error accessing SpamAssassin public corpus:", e)

if __name__ == "__main__":
    check_nazario_monkey_org()
    check_spamassassin_easy_ham()

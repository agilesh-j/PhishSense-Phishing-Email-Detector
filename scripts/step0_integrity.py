import sys, csv, os, hashlib, glob

csv.field_size_limit(2147483647)

def analyze(path):
    sz = os.path.getsize(path)
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    sha = h.hexdigest()
    
    if path.endswith('.csv'):
        rows = 0
        bad = 0
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            cols = len(header) if header else 0
            for r in reader:
                rows += 1
                if len(r) != cols:
                    bad += 1
        return sz, sha, f"{rows} rows (bad lines: {bad})"
    elif path.endswith('.tar.bz2') or path.endswith('.zip') or path.endswith('.mbox'):
        return sz, sha, "N/A (archive/mbox)"
    elif path.endswith('.md'):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return sz, sha, f"{len(lines)} lines"
    return sz, sha, "N/A"

# Known publisher originals
ZENODO_ORIGINALS = {
    'Phishing_Email.csv': ('dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv', '18ef4fff1acb8986f0ab01e83ede6025420c829656af5a377560fce17e153b97'),
    'archive.zip': ('dataset/raw/phishing_email_reference/archive.zip', '5d4d5cd13963aa8272ee771a64cae31aad9a4028534a9fc598f00fbf52b821be'),
    'Enron.csv': ('dataset/raw/enron_clean/Enron.csv', '11f28a5bdd3603f1829681ab6b55071b5f9af781b4e6694e39216b2996a96883'),
    'Nigerian_Fraud.csv': ('dataset/raw/nigerian_fraud/Nigerian_Fraud.csv', 'f5d6930763cae6feeae6484131c79655a7440abbb97d6f51eab757aea4e6ab4b'),
    'Nazario.csv': ('dataset/raw/nazario_phishing/Nazario.csv', 'b8fbc4158fbdfaff1ed98584c43d72e283c6352d7ade4d457d34c1d79488d184'),
    'CEAS_08.csv': ('dataset/raw/ceas_08/CEAS_08.csv', '22375e7d5f5a8229dbe987914ee9b3705656c590038662a7df6054629b376074'),
    '20030228_hard_ham.tar.bz2': ('dataset/raw/spamassassin_hard_ham/20030228_hard_ham.tar.bz2', 'ce2ce67880643dbde65ea7f85bffbfe4417349c4bd80b6b0de56262ae6b0a9c9'),
    '20030228_easy_ham.tar.bz2': ('dataset/raw/spamassassin_easy_ham/20030228_easy_ham.tar.bz2', '2b7b65904bcfcc31d2b5f51946f2d261370b257402cbbd62930b46ab83367438'),
    '20030228_easy_ham_2.tar.bz2': ('dataset/raw/spamassassin_easy_ham/20030228_easy_ham_2.tar.bz2', 'b4bd3dc5ae5b40f38e99a0e41ad7d16b428b56e818e3a6ffa07330d62004dd38'),
}

files_to_check = []
for root, dirs, files in os.walk('dataset/raw'):
    # don't list thousands of individual spamassassin extracted files in the summary table
    if 'extracted_' in root or ('extracted' in root and 'hard_ham' in root and 'extracted/hard_ham' in root.replace('\\', '/')):
        continue
    for f in files:
        files_to_check.append(os.path.join(root, f))

if os.path.exists('legacy_edited'):
    for root, dirs, files in os.walk('legacy_edited'):
        for f in files:
            files_to_check.append(os.path.join(root, f))

print("| File Path | Size (Bytes) | SHA-256 | Row Count / Type | Matches Publisher Original? |")
print("|---|---|---|---|---|")

for path in sorted(files_to_check):
    p_norm = path.replace('\\', '/')
    sz, sha, info = analyze(path)
    
    # check match
    fn = os.path.basename(path)
    if 'legacy_edited' in p_norm:
        if fn in ZENODO_ORIGINALS:
            orig_sha = ZENODO_ORIGINALS[fn][1]
            matches = "yes" if sha == orig_sha else "no (legacy modified/truncated)"
        else:
            matches = "no (legacy modified)"
    elif fn in ZENODO_ORIGINALS:
        orig_sha = ZENODO_ORIGINALS[fn][1]
        matches = "yes" if sha == orig_sha else "no"
    elif fn.startswith('phishing-') and fn.endswith('.mbox'):
        matches = "yes (direct monkey.org mbox)"
    elif fn.endswith('.md'):
        matches = "N/A (metadata documentation)"
    else:
        matches = "not checked"
        
    print(f"| `{p_norm}` | {sz:,} | `{sha[:16]}...` | {info} | {matches} |")

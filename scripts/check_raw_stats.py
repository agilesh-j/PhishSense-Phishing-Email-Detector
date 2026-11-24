"""Check and log raw file integrity, rows, bad lines, nulls, and distributions."""
import os
import hashlib
import pandas as pd

def check_file(path, exp_md5=None):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = f.read()
    md5 = hashlib.md5(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    
    bad_lines = 0
    def on_bad(line):
        nonlocal bad_lines
        bad_lines += 1
        return None
    
    df = pd.read_csv(path, on_bad_lines=on_bad, engine="python")
    
    print("=" * 60)
    print(f"File: {path}")
    print(f"Size: {size:,} bytes")
    print(f"MD5: {md5} (Expected: {exp_md5}, Match: {md5 == exp_md5 if exp_md5 else 'N/A'})")
    print(f"SHA-256: {sha256}")
    print(f"Rows loaded: {len(df):,}")
    print(f"Bad lines dropped: {bad_lines}")
    print(f"Columns: {list(df.columns)}")
    if "label" in df.columns:
        print(f"Label distribution: {df['label'].value_counts(dropna=False).to_dict()}")
    if "Email Type" in df.columns:
        print(f"Email Type distribution: {df['Email Type'].value_counts(dropna=False).to_dict()}")
    for col in ["body", "Email Text", "text"]:
        if col in df.columns:
            null_count = df[col].isna().sum()
            print(f"Null text in '{col}': {null_count:,} ({null_count/len(df):.2%})")

if __name__ == "__main__":
    check_file("dataset/raw/enron_clean/Enron.csv", "10489e0fdcc8af6fe62135c689367d40")
    check_file("dataset/raw/nigerian_fraud/Nigerian_Fraud.csv", "65fd47ae7cb4ae762e4be42b11905d63")
    check_file("dataset/raw/nazario_phishing/Nazario.csv", "4022d055bb7cf8602f30f768f652e91e")
    check_file("dataset/raw/phishing_email_reference/extracted/Phishing_Email.csv")

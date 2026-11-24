"""Raw dataset ingestion, schema alignment, label mapping, and vertical concatenation."""
import email
from email import policy
import glob
import os
import pandas as pd


def load_reference_dataset(csv_path: str) -> pd.DataFrame:
    """Load Source #1 (Phishing_Email.csv) and align schema."""
    df = pd.read_csv(csv_path)
    label_map = {
        "Safe Email": "safe",
        "Phishing Email": "phishing",
    }
    raw_id = df["Unnamed: 0"].astype(str) if "Unnamed: 0" in df.columns else df.index.astype(str)
    raw_lbl = df["Email Type"].fillna("").astype(str)
    mapped_lbl = raw_lbl.map(label_map).fillna("excluded")
    text_col = df["Email Text"].fillna("").astype(str)
    
    return pd.DataFrame(
        {
            "source_id": "phishing_email_reference",
            "source_file": "Phishing_Email.csv",
            "raw_id": raw_id,
            "raw_label": raw_lbl,
            "text": text_col,
            "label": mapped_lbl,
        }
    )


def load_spamassassin_hard_ham(extracted_dir: str) -> pd.DataFrame:
    """Load RFC 822 emails from SpamAssassin hard_ham extracted folder."""
    records = []
    # Find all email files in extracted directory (handling possible nested hard_ham folder)
    file_paths = glob.glob(os.path.join(extracted_dir, "**", "*"), recursive=True)
    file_paths = [
        f
        for f in file_paths
        if os.path.isfile(f) and not f.endswith(".md") and not f.endswith(".tar.bz2")
    ]

    for fpath in file_paths:
        fname = os.path.basename(fpath)
        if fname in ("cmds", "SOURCE_NOTE.md"):
            continue
        try:
            with open(fpath, "rb") as f:
                raw_bytes = f.read()
            msg = email.message_from_bytes(raw_bytes, policy=policy.default)
            # Extract plain text payload
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type in ("text/plain", "text/html"):
                        try:
                            body += part.get_content() + "\n"
                        except Exception:
                            body += str(part.get_payload()) + "\n"
            else:
                try:
                    body = msg.get_content()
                except Exception:
                    body = str(msg.get_payload())

            # Include subject if available
            subj = str(msg.get("subject", "") or "")
            full_text = f"{subj}\n{body}".strip() if subj else body.strip()

            records.append(
                {
                    "source_id": "spamassassin_hard_ham",
                    "source_file": fname,
                    "raw_id": fname,
                    "raw_label": "ham",
                    "text": full_text,
                    "label": "safe",  # Hard safe negative
                }
            )
        except Exception as e:
            print(f"Error parsing {fname}: {e}")

    return pd.DataFrame(records)


def load_tabular_source(
    csv_path: str,
    source_id: str,
    target_raw_label: int,
    mapped_label: str,
) -> pd.DataFrame:
    """Load tabular email CSV (Nazario, Nigerian_Fraud, Enron) with schema ['sender', 'receiver', 'date', 'subject', 'body', 'urls', 'label'].
    
    Loads the entire file without any first-N rows truncation.
    """
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Clean label parsing
    raw_lbl_numeric = pd.to_numeric(df["label"], errors="coerce")
    is_target = raw_lbl_numeric == target_raw_label
    
    # Combine subject and body
    subjects = df["subject"].fillna("").astype(str).str.strip()
    subjects = subjects.replace("nan", "")
    bodies = df["body"].fillna("").astype(str).str.strip()
    bodies = bodies.replace("nan", "")
    
    has_subj = subjects.str.len() > 0
    full_text = bodies.copy()
    full_text[has_subj] = subjects[has_subj] + "\n" + bodies[has_subj]
    
    assigned_label = pd.Series("excluded", index=df.index)
    assigned_label[is_target] = mapped_label
    
    out_df = pd.DataFrame(
        {
            "source_id": source_id,
            "source_file": os.path.basename(csv_path),
            "raw_id": df.index.astype(str),
            "raw_label": df["label"].astype(str),
            "text": full_text,
            "label": assigned_label,
        }
    )
    return out_df

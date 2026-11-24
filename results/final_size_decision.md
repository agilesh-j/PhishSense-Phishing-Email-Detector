# PhishSense: Final Dataset Size & Fallback Decision Record

- **Final Dataset Size:** 11,000 balanced rows (5,500 Safe, 5,500 Phishing)
- **Target Range Evaluated:** 12,000 to 16,000 rows
- **Ladder Step Invoked:** ladder (a): raised phishing cap to 45%
- **Limiting Factor:** High-standard phishing deduplication and strict anti-shortcut source caps (each <= 40% / 45%).
- **Hard Negative Representation:** 2658/5500 (48.3% of Safe Class)
- **Train / Validation / Test:** 7696 / 1646 / 1658 (70% / 15% / 15%)
- **Held-Out OOD Probe:** 400 rows (untouched)

## Per-Source Share Breakdown

### Phishing Class (5500 rows)
| Source | Share (% of Phishing) |
|---|---|
| `nigerian_fraud` | 44.8% |
| `nazario_modern` | 29.9% |
| `nazario_phishing` | 25.3% |

### Safe Class (5500 rows)
| Source | Share (% of Safe) |
|---|---|
| `ceas_08` | 40.0% |
| `enron_clean` | 25.0% |
| `spamassassin_easy_ham` | 15.7% |
| `reference_safe` | 15.0% |
| `spamassassin_hard_ham` | 4.3% |

# PhishSense: Final Dataset Composition

**Total Curated Rows:** 11,000 (50.0% Safe, 50.0% Phishing)

## Source × Class × Era Matrix

| Class | Source | Era | Row Count | Class Share (%) |
|---|---|---|---|---|
| phishing | `nazario_modern` | modern | 1,645 | 29.9% |
| phishing | `nazario_phishing` | historical | 1,391 | 25.3% |
| phishing | `nigerian_fraud` | historical | 2,464 | 44.8% |
| safe | `ceas_08` | historical | 2,200 | 40.0% |
| safe | `enron_clean` | historical | 1,375 | 25.0% |
| safe | `reference_safe` | historical | 825 | 15.0% |
| safe | `spamassassin_easy_ham` | historical | 861 | 15.7% |
| safe | `spamassassin_hard_ham` | historical | 239 | 4.3% |

## Key Quality Attributes
- **Hard Negative Representation:** 48.3% of Safe Class (2658 rows).
- **Phishing Era Mix:** Historical (3855 rows) + Modern (1645 rows).
- **Multi-Source Diversity:** 5 safe sources, 3 phishing sources (all >= 3).
- **Proportional Caps:** Every source satisfies <= 40% cap (or fallback 45%), Enron + Ref Safe is 40.0% (cap: 40%).

# Label Audit Package (STOP 1)
1. Open `results/label_audit/reviewer_1.csv` and enter `safe` or `phishing` in `my_label` for the 120 blinded emails.
2. Refer to prototype definitions in `docs/LABEL_GUIDELINES.md` for guidance on borderline cases.
3. Save the CSV, then run `python scripts/score_audit.py` to calculate precision, agreement, and Cohen's kappa.
4. If any source achieves < 95% precision, replacement rows will be automatically drawn from `results/reserve_pool.csv`.
5. Independent second review is pre-recorded in `results/label_audit/agent_review.csv`.

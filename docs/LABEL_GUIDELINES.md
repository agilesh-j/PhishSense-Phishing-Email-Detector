


# PhishSense: Annotation & Label Guidelines (Phase 2)

**Institution:** Arunachala HiTech Engineering College | Applied AI  
**Project:** PhishSense: Phishing Email Detector (Team 02)  
**Target Labels:** Exactly `"safe"` and `"phishing"`  
**Status:** Draft Formalized & Approved under ADR-002  

---

## 1. Scope & Core Definitions

PhishSense detects deceptive language in email text. In accordance with the project brief and threat modeling standards, the label space is partitioned as follows:

### 1.1 `phishing` (Positive Class)
An email whose primary intent is **deceptive social engineering** designed to:
- **Impersonate** a trusted entity (bank, e-commerce brand, cloud provider, government agency, executive, or colleague).
- **Induce risky action** through fabricated urgency, panic, or excitement (account suspension threats, fake security alerts, unexpected invoices, lottery winnings, loan approvals).
- **Harvest credentials or sensitive data** (passwords, PINs, bank details, MFA codes).
- **Defraud the recipient** of funds (Business Email Compromise / wire fraud, advance-fee / 419 scams, fake check deposits).

*Attack Families Included:*
1. **Credential Harvesting:** Fake login portals, account verification requests, password reset lures.
2. **Brand Spoofing:** Unauthorized access alerts from eBay, PayPal, Microsoft, Google, banks.
3. **Business Email Compromise (BEC):** Executive/CEO impersonation, urgent confidential wire transfer requests, payroll routing updates.
4. **Advance-Fee & Lottery Fraud:** Nigerian prince / bank director inheritances, lottery prize notifications, counterfeit check transactions.
5. **Invoice & Payment Fraud:** Fake billing notifications, overdue payment warnings with malicious action pretexts.

### 1.2 `safe` (Negative Class)
An email representing legitimate human or automated correspondence:
- **Workplace & Professional Communications:** Internal team discussions, status updates, scheduling, meeting minutes, contract reviews.
- **Personal Correspondence:** Authentic conversations between friends, family, or mailing list peers.
- **Genuine Transactional & System Notices (Hard Negatives):** Real banking statements, order confirmations, shipping tracking updates, genuine security change confirmations.
- **Honest Marketing & Newsletters:** Commercial mailings from verified brands that explicitly identify themselves, provide real contact information, and sell legitimate goods/services without deceptive spoofing.

### 1.3 `out-of-scope` (Excluded from Both Classes)
Emails that degrade model quality or introduce conflicting decision boundaries:
- **Unsolicited Commercial Spam (Bulk Marketing):** Cheap pharmaceuticals, adult entertainment, generic clearance sales, and stock tips that lack identity spoofing or credential theft.
- **Bayesian Word-Salad:** Random dictionary words assembled by historical spammers to bypass Bayesian filters.
- **Placeholders & Corrupted Records:** Emails with null bodies, literal `"empty"`, or fewer than 15 valid words.
- **Unreadable / Multi-language Fragments:** Truncated server logs, base64 raw blobs, or non-English emails.

---

## 2. Clear Exemplars from Dataset (Masked)

### Prototypical `phishing` Examples

#### Example P1: Account Suspension Threat (Brand Spoofing / Credential Theft)
> **Subject:** Urgent Safeharbor Department Warning  
> **Body:** Urgent Safeharbor department warning. We recently have determined that different computers have logged into your eBay account, and multiple password failures were present. As a security precaution, we have temporarily limited access to your account. To restore your access and confirm your identity, please verify your account information immediately at `<url>`. Failure to update within 24 hours will result in permanent account suspension.

#### Example P2: Advance-Fee Fraud (Nigerian 419 Scam)
> **Subject:** Urgent Proposal from Pacific Bank  
> **Body:** Dear Sir, I am `<name>`, Provincial Director at Pacific Bank of Nigeria. I am writing to solicit your confidential assistance in transferring `<amount>` belonging to a deceased foreign contractor. For your assistance and provision of a nominated bank account, you will receive 30% of the total funds. Please reply urgently with your full name, direct telephone number, and banking details to `<email>`.

#### Example P3: Fake Loan / Financial Pretexting
> **Subject:** Application Processed and Accepted  
> **Body:** Dear Applicant, Your recent application for financial assistance was reviewed and accepted. You qualify for an unsecured loan of $350,000 at a fixed 2.4% rate. To finalize disbursement and verify your personal identity, please confirm your Social Security and bank routing numbers here: `<url>`.

#### Example P4: Lottery Fraud / Fake Reward
> **Subject:** National Lottery Euro Millions Prize Notification  
> **Body:** Congratulations! You have won the National Lottery Euro Millions Promo. Reference: UK/9420-X2. Your email address was selected in a computer balloting system. Your cash award of 1,500,000 GBP is waiting to be processed. Contact our foreign claims agent immediately at `<email>` with your personal details to release payment.

#### Example P5: Executive Impersonation (BEC)
> **Subject:** Urgent and Confidential Request  
> **Body:** Are you available at your desk? I am currently in a closed meeting with our acquisition partners and cannot take calls. I need an urgent international wire transfer processed before 3:00 PM today to close the transaction. Please let me know immediately so I can send the vendor wire instructions. Keep this confidential.

---

### Prototypical `safe` Examples

#### Example S1: Workplace Operational Coordination
> **Subject:** RE: Equistar Deal Tickets  
> **Body:** Are you still available to assist Robert with entering the new deal tickets for Equistar? After talking with Bryan and Anita, Kyle and I decided that having extra help would ensure we meet the end-of-day settlement deadline. Please let me know your availability for this afternoon. Thanks.

#### Example S2: Technical Mailing List Discussion
> **Subject:** Re: [Spambayes] Guidance re pickles versus DB for Outlook  
> **Body:** So then, Mark Hammond was mentioning that ZODB is sounding attractive. I would package it up, so a few hundred extra KB is probably no big deal. The code could fall back to the slow-loading pickles so people running from source still work. I haven't used ZODB much, but let me know what you think.

#### Example S3: Hard Negative — Authentic Financial Notice
> **Subject:** Your Monthly Account Statement is Ready  
> **Body:** Dear Customer, Your monthly account statement for checking account ending in `<num>` is now available. Your current balance is $3,241.18. To view your complete transaction history, log into your online banking account at `<url>`. Thank you for banking with us.

#### Example S4: Hard Negative — Legitimate Security Alert
> **Subject:** New Sign-in from Chrome on Windows  
> **Body:** We noticed a new sign-in to your account from a new Windows device. Device: Windows 11, Browser: Chrome, Location: Dallas, TX. If this was you, you can safely ignore this email. If this was not you, please secure your account immediately at `<url>`.

#### Example S5: Corporate Meeting Logistics
> **Subject:** Meeting on Feb 8: Agenda and Room Confirmation  
> **Body:** Dear Team, Thank you for your prompt responses regarding the Q1 operational review. Our meeting is confirmed for February 8 at 10:00 AM in Conference Room 4B. Attached is the presentation outline. Please review pages 3 through 7 prior to our session.

---

## 3. Borderline Cases & Explicit Rulings

| Case # | Candidate Email Text Summary | Content Analysis | Official Ruling | Rationale & Policy |
|---|---|---|---|---|
| **B1** | *"Would you like to save 80% on printer, fax, and copier ink cartridges? High-yield toners for HP, Canon, Epson. Order online at `<url>`."* | Unsolicited bulk marketing / commercial retail advertisement. | **OUT OF SCOPE (EXCLUDED)** | Lacks deceptive identity spoofing, credential theft, or social engineering pretexts. Treating bulk retail spam as phishing degrades the decision boundary. |
| **B2** | *"Your automated shipping notification: Package #`<num>` has shipped via UPS Ground. Estimated delivery is Friday by 7:00 PM. Track status at `<url>`."* | Automated transactional notice with links and delivery terminology. | **SAFE (HARD NEGATIVE)** | Genuine transactional communication. Does not pressure recipient to provide credentials or panic over a false problem. |
| **B3** | *"Dear Beneficiary, You have won the Euro Millions Prize. To claim your 2,000,000 GBP, reply directly to `<email>` with your bank details. No website."* | Social engineering advance-fee fraud conducted purely via email reply (zero external URLs). | **PHISHING** | Deceptive identity and fraudulent pretext aimed at financial theft. Phishing does not require external hyperlinks. |
| **B4** | *"IT Helpdesk Notice: Your domain password expires in 3 days. Change your password on your workstation or visit internal portal `<url>`."* | System administrative password change notification. | **SAFE (HARD NEGATIVE)** | Legitimate enterprise administrative maintenance. Must be recognized as safe to prevent false alarms on internal IT emails. |
| **B5** | *"OTC Investor Alert: Stock ticker XYZ is the #1 stock to watch tomorrow. Massive revenue growth anticipated. Read the independent report."* | Stock pump-and-dump promotional commercial spam. | **OUT OF SCOPE (EXCLUDED)** | Commercial financial promotion. Excluded under the commercial spam rule unless it spoofed a licensed broker or banking identity. |

---

## 4. Review Protocol for Ambiguous Records

During Phase 4 and Phase 5 cleaning:
1. Records identified as commercial marketing spam without brand spoofing are routed to `results/excluded_spam_log.csv`.
2. Borderline records that cannot be confidently classified using the rules above are quarantined in `results/borderline_review.csv` for human inspection during the Phase 8 audit.
3. In `STRICT_BRIEF_MODE: true`, all filtering of commercial spam is bypassed, mapping raw Source #1 labels directly to preserve the college baseline.

---

## 5. Operational Definition of Hard Negatives (Tightened Two-Part Rule)

A safe email (`label == "safe"`) is classified as an authenticated **Hard Negative** if and only if it satisfies both of the following programmatic criteria:

1. **Real Phishing-Like Cues (Authentic Attack Context):**
   The text must contain genuine urgency, credential/account threat, financial/banking transaction, or explicit security alert terminology:
   - *Urgent tone / directive pressure:* `urgent`, `urgently`, `immediate`, `immediately`, `action required`, `important notice`
   - *Credential / authentication threats:* `password`, `passcode`, `login`, `log-in`, `verify`, `verification`, `suspended`, `suspension`, `reset`, `compromised`, `unauthorized`
   - *Transactional / financial cues:* `payment`, `wire`, `invoice`, `billing`, `statement`, `receipt`, `bank`, `funds`, `balance`
   - *Phrasal security / administrative alerts:* `security alert`, `security notice`, `security update`, `security warning`, `security verification`, `account verification`, `account suspended`, `account locked`, `account access`
   *(Explicit Quality Exclusion: Standalone generic words like `account`, `security`, `confirm`, `download`, `deadline`, or `attachment` alone do NOT qualify, eliminating false positives on academic calls for papers or benign software downloads).*

2. **Action Directive Cue:**
   The email must contain an explicit action directive or hyperlink:
   - `<url>`, `click`, `please visit`, `log in`, `log into`, `sign in`, `review the attached`, `verify here`

### Cue Word Audit & Weak Word Elimination
In our empirical cue frequency audit of 5,500 curated safe rows:
- High-frequency weak cues: `security` (593), `deadline` (367), `account` (351), `attachment` (130), `confirm` (103).
- **Audit Finding:** Under the historical permissive rule, **612 of 2,026 rows (30.2%)** qualified solely on a single weak word (e.g., an academic computer security call for papers or a conference submission deadline with a `<url>`).
- **Tightened Standard:** Requiring at least one real phishing-like cue plus an action directive eliminates these 612 weak rows while preserving **982 authenticated hard negatives (17.85% of safe rows)** across all 5 safe sources, well exceeding the 12% requirement without sacrificing semantic quality.

---

## 6. Candidate Vetting Decisions & Quality Rules

### 6.1 CEAS_08 from Zenodo 8339691
- **Raw Volume:** 39,154 rows (21,842 labeled 1, 17,312 labeled 0).
- **Safe Class (Label 0):** 17,185 clean rows; 100/100 audited rows passed as authentic personal/work emails (**100.0% precision**).
- **Spam/Phishing Class (Label 1):** Pre-screening commercial spam share was 19.24%. Post-screening pool contains 18,537 rows with 18.29% commercial spam. Stratified audit of 100 rows showed only 14 rows met genuine phishing deception criteria (**14.0% precision**; 86% were bulk advertisements, newsletters, or generic discount spam).
- **Ruling:** **REJECTED AS A TRAINING PHISHING SOURCE** under the mandatory $\ge 95\%$ precision threshold. May only be used as an out-of-domain (OOD) spam-robustness probe.

### 6.2 SpamAssassin Easy Ham (Archives 1 and 2)
- **Raw Volume:** 3,902 RFC 822 email files.
- **Yield:** 3,742 clean, valid safe rows (95.9% yield).
- **Ruling:** **APPROVED AS NON-ENRON SAFE ENRICHMENT SOURCE**. Completely diversifies the safe class and prevents Enron monoculture.

### 6.3 Jose Nazario Modern Archives (monkey.org/~jose/phishing/)
- **Availability:** 11 yearly mbox archives from 2015 to 2025 totaling 98.2 MB of real honeypot credential-theft phishing emails.
- **Ruling:** Verified real modern phishing. Approved for use as either modern phishing training enrichment or dedicated modern OOD test probe.

---

## 7. Anti-Shortcut Token Masking & Confounder Mitigation

Because source IDs can correlate with class labels when single-class enrichment sources are used, the following era, boilerplate, and routing markers are strictly masked with generic tokens:
- `<routing>`: Internal Enron routing paths (`/hou/ect`, `/corp/enron`, `@ect`, `@enron`, etc.)
- `<date>`: Dates (`October 24, 2002`, `10/24/2001`, `24-Oct-2001`, etc.)
- `<time>`: Times (`08:30 AM`, `14:22`, `4:15pm`, etc.)
- `<year>`: 4-digit years (`1998` through `2025`)
- `<num>`: Long numeric strings of 5+ digits (account numbers, tracking IDs)
- `<footer_marker>`: Mailing list unsubscribe and listserv boilerplates
- `<url>`, `<email>`, `<phone>`: Hyperlinks, email addresses, and formatted telephone numbers

---

## 8. Reference Dataset vs. Enron Overlap Accounting

Empirical MinHash and exact hash analysis demonstrated that **41.89%** of the Reference dataset's "Safe Email" rows are exact or near-duplicates ($J \ge 0.85$) of `Enron.csv`, and 20.88% contain explicit internal Enron headers.

**Accounting Policy:**
1. Reference safe emails are recognized as originating predominantly from the Enron corpus.
2. In calculating source diversity and capping, Reference Safe emails are counted alongside Enron Clean against the combined Enron corpus ceiling.
3. Reference Dataset is strictly capped at $\le 25\%$ per class.
4. SpamAssassin safe emails provide 35.0% of the safe class, guaranteeing substantial non-Enron representation.

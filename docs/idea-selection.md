# LandTech 2026 — idea discovery and selection

Prepared 15 October 2026 (Asia/Dhaka) for the ShareTally team, following the team brief. Labels used below: **Verified** = read on a fetched page (URL and date given); **Inference** = our reasoning from verified facts; **Assumption** = stated without evidence; **Proposed** = behaviour of our prototype.

## 0. Status flags to resolve first

| Item | What we know | Action |
| --- | --- | --- |
| Round 1 deadline | Rule book (pages 4 and 6) says **16 Oct 2026**. The pasted submission page says 18 Oct 2026. The event site (landtech.diu.edu.bd/landtech) is behind a bot-check and could not be read. | Confirm with organizers (csetech@diu.edu.bd, +880 1756-808027). **Plan for 16 Oct.** Neither source is assumed to supersede the other. |
| Required vs optional uploads | The form marks several links and the concept note optional; the rule book §10.1 lists concept note (≤4 pages PDF), repository, demo video (≤3 min), live link (recommended). | Prepare everything the rule book lists. |
| LA-60 | Treated only as the submission-page label, not a problem-statement number. | — |
| Team details | Participant: Tanvir Hossin. Other student and both mentors unknown. | Fill placeholders; do not invent. |
| Public showcase consent | A participant choice. | Leave unselected unless the team decides. |

## 1. Research summary

### 1.1 Verified facts (desk research, pages fetched 15 Oct 2026)

| # | Fact | Source |
| --- | --- | --- |
| F1 | The rule book itself names "records split between the sub-registry office (registration) and the AC Land office (mutation)" as a root of land disputes. | Rule book p.3 |
| F2 | The registering officer must not accept a transfer instrument without a Land Transfer notice and must transmit it to the Revenue Officer (SAT Act 1950 s.89(1)(a), s.89(5)). | bdlaws, act-241 section-7068 |
| F3 | "The Revenue-officer on receipt of the notice under section 89 shall open a file for mutation" (SAT Act s.143C(1)). | bdlaws, act-241 section-7261 |
| F4 | A sale deed is not registered unless the latest khatian in the seller's (or predecessor's) name, a 25-year ownership description, and an affidavit that the executant "has not transferred the property to any person" are attached (Registration Act 1908 s.52A, inserted 2004, widened by Act 14 of 2026). | bdlaws, act-90 section-22972 |
| F5 | Later rights over the same property are "subject to the rights previously created" (Transfer of Property Act 1882 s.48). | bdlaws, act-print-48 |
| F6 | Land Crimes Prevention and Remedy Act 2023 (Act 36 of 2023): s.4(1)(গ) covers transferring land beyond one's own holding; s.5 forging documents; up to 7 years' imprisonment. No explicit "double sale" offence. | bdlaws, act-print-1454 |
| F7 | e-Mutation piloted 2016, nationwide from 2019; target 28 days; average 43 days in a 2022 Land Ministry data sample. | Prothom Alo, 16 Sep 2019 and 28 Sep 2022 |
| F8 | In a 2018 trial across 46 upazilas (30,000+ transfers), about 30% of new owners applied for mutation within 3 months. | Behavioural Insights Team, 20 Aug 2020 |
| F9 | Cabinet approved automatic mutation and sub-registry access to khatian data in Nov 2020 (pilot); in June 2026 integration was still described as a plan; Feb 2026 reporting describes a coordination gap between the two ministries. | TBS 9 Nov 2020, 30 Jun 2026; The Daily Star 7 Feb 2026 |
| F10 | e-mutation khatians and DCRs carry QR codes since July 2022; in Jan 2026 the ministry warned of fake documents with copied QR codes and asked people to scan only with its Bhumi app. | Ittefaq 30 Jul 2022; Dhaka Tribune 18 Jan 2026 |
| F11 | Records portal moved: land.gov.bd links land records to dlrms.land.gov.bd; eporcha.gov.bd did not resolve on 15 Oct 2026. Hotline 16122. | land.gov.bd (fetched 15 Oct 2026) |
| F12 | Cases in 2026 where a mutation on a forged deed was caught by an AC (Land) officer's manual review (Babuganj) or reversed after a Sub-Registry check of the original volume (Alfadanga). | Ittefaq 18 Jul 2026; Dhaka Times 3 Jun 2026 |
| F13 | Bangladesh Digital Survey: 274 of 58,590 mouzas surveyed in 14 years; old survey series (CS, SA, RS, BS) will coexist for a long time. | TBS Bangla, 1 Oct 2026 |
| F14 | 16 anna = whole share; 1 anna = 20 gonda; 1 gonda = 4 kora. Kora → kranti → til ratios disagree between sources. Bigha/katha vary by region. | landregistrationbd.com (updated 23 Jul 2025); legalseba.com; arXiv 2609.03597 |
| F15 | Precedents: Karnataka captures land details from Bhoomi during registration "thereby avoiding duplicate registration"; Telangana's 2020 law registered sales only when consistent with the Record of Rights and amended it instantly — later replaced (Bhu Bharati, 2025) partly over the lack of notice and appeal. UK Property Alert emails owners about activity on watched titles. | tumkur.nic.in (7 Mar 2025); Telangana Act 9 of 2020; Deccan Chronicle 16 Apr 2025; gov.uk (10 Oct 2025) |
| F16 | TIB household survey 2023: 51% of households using land services faced corruption. An official said land disputes are almost 80% of legal cases (statement, no data shown). | TIB 3 Dec 2024; Daily Observer 8 Nov 2025 |
| F17 | Tesseract is "designed for printed text"; a 2026 study of handwritten RS khatians found no OCR pipeline recognised anna glyphs. | tesseract-ocr FAQ; arXiv 2609.03597 |
| F18 | Hosting: Render free web services sleep after 15 min, ~1 min wake-up, ephemeral disk; Hugging Face Docker Spaces now need a paid plan. | render.com/docs/free; huggingface.co docs |

**Not verified (do not claim):** that sellers or recorded owners receive SMS/calls about mutation filings; what a QR scan of a khatian displays; any current automatic-mutation rollout; a prescribed deed form row for the 25-year history (the duty is statutory); civil-case-only land statistics.

### 1.2 The precise gap (inference)

Digitisation, online mutation and QR copies already exist (F7, F10, F11). What is missing is a **computed remaining balance per seller per plot** that spans both offices. Registration checks the seller against the latest khatian plus the seller's own affidavit (F4); the khatian lags because most buyers do not mutate promptly (F8); the L.T. notice that would close the gap already flows by law (F2, F3) but is not reconciled arithmetically against the khatian. Detection of forged-deed mutations depends on individual vigilance (F12). Integrated checks exist elsewhere (F15), so the mechanism is not new worldwide; our contribution is a transparent, Bangladesh-notation-aware version that refuses to call incomplete data clean, demonstrated on synthetic data.

## 2. Six candidates

Each: P-code · user · one failure · mechanism (inputs → checks → outputs → human decision) · difference · 3-minute demo moment · data · dependency · likely failure · 24-hour demo.

### A. ShareTally — share-conservation ledger (P3)
- **User:** AC (Land) mutation reviewer; Sub-Registry clerk for a pre-registration check.
- **Failure:** First buyer never mutates; khatian still shows seller; a second deed for the same share passes s.52A checks and may be mutated first.
- **Mechanism:** khatian shares + registered transfers (digital L.T. notices) + succession records + mutation applications + index coverage → exact fraction ledger, oldest first, conservation and cross-reference rules → per-case status with evidence → reviewer holds/notices/approves.
- **Difference:** Existing services record and display; none (in public documentation found) computes remaining share across registered-but-unmutated deeds. Not new globally (F15).
- **Demo moment:** "Joynal held 30, sold 20 in 2023, now sells 20 again — 10 more than remains" with both deeds and an overflowing share strip.
- **Data:** fully synthetic. **Dependency:** a digital transfer feed in reality. **Likely failure:** incomplete historic data → many Incomplete results; false conflicts from unregistered partitions.
- **24 h:** engine, 18 scenarios, 3–5 screens — feasible.

### B. Plot Watch — owner alerts on any filing (P3)
- **User:** recorded owners, especially absentee and expatriate owners.
- **Failure:** A forged deed or mutation is filed against an absentee owner's plot; the owner learns years later (2026 expatriate case reported by Ittefaq).
- **Mechanism:** verified owner subscribes to a dag → registration/mutation/case events matched on normalised plot IDs (incl. old-survey aliases) → SMS/e-mail alert → owner lodges objection that appears to the reviewer.
- **Difference:** UK Property Alert is a direct precedent; in Bangladesh notices go to parties named by the applicant (not verified for recorded owners).
- **Demo:** filing a forged mutation triggers the owner's alert in seconds.
- **Data:** synthetic. **Dependency:** live event feeds plus identity verification (NID) — privileged. **Likely failure:** subscriber verification and privacy (stalking risk), alert fatigue.
- **24 h:** subscription, simulated feed, matching, alert log.

### C. Living Certified Copy — signed, status-aware copies (P2)
- **User:** buyer, bank or lawyer receiving a khatian/deed copy.
- **Failure:** Fake documents with copied QR codes circulate (F10); a genuine but superseded copy is also used.
- **Mechanism:** issuer signs canonical record (Ed25519, RFC 8032) → QR carries record ID, version, signature → verifier checks signature against the published key, queries supersession status, shows field differences → human decides.
- **Difference:** binds QR to content and version, not just a lookup link.
- **Demo:** altered share fails verification; untouched 2019 copy shows "authentic but superseded by mutation 2022".
- **Data:** synthetic. **Dependency:** government signing keys and re-issuance. **Likely failure:** adoption; does not stop upstream fraud (forged deed producing a genuine new khatian).
- **24 h:** keys, signing, QR, verifier page — easy.

### D. Self-checking Khatian Digitiser (P1)
- **User:** record-digitisation operators.
- **Failure:** OCR/entry errors in shares and areas enter digital records.
- **Mechanism:** scan → OCR → field extraction → invariants (shares sum to 16 anna; areas reconcile; digits vs words) → highlight failing cells for correction.
- **Difference:** domain invariants focus human checking.
- **Demo:** misread share caught by the sum check.
- **Data:** synthetic scans only. **Dependency:** Bangla OCR quality (F17). **Likely failure:** handwritten/anna glyphs unreadable; synthetic scans prove little.
- **24 h:** printed synthetic images only — risky.

### E. L.T.-Notice Handoff — registration-to-mutation workflow (P4)
- **User:** Sub-Registry clerk and AC (Land) office.
- **Failure:** L.T. notices delayed or lost; buyer must apply separately; khatian stays stale.
- **Mechanism:** registration event → structured notice → auto-drafted mutation case with pre-checks (seller in khatian, LDT paid, khas/acquisition list) → SLA tracking → AC Land order.
- **Difference:** limited — automatic mutation was approved in 2020 (F9) and exists elsewhere (F15).
- **Demo:** register a deed, case appears with a pre-check failure.
- **Data:** synthetic. **Dependency:** inter-ministry integration. **Likely failure:** seen as workflow software overlapping government plans.
- **24 h:** state machine and forms — feasible.

### F. Coverage-aware Pre-Purchase Report (P5)
- **User:** prospective buyer or their lawyer.
- **Failure:** a buyer sees the seller's name online and assumes the land is clear; "not found" in one source is read as "safe".
- **Mechanism:** plot + seller → simulated checks across khatian, mutation history, LDT, khas register, acquisition notices, cases, registry search, each with coverage metadata → Found / Not found (covered) / Not covered / Ambiguous → checklist of offices to visit.
- **Difference:** honest coverage reporting; existing services are manual lawyer checks.
- **Demo:** same plot shows "acquisition notices not covered" → Incomplete, not Safe.
- **Data:** synthetic. **Dependency:** many agencies' data (no APIs; scraping forbidden). **Likely failure:** cannot be real without multi-agency integration; over-trust.
- **24 h:** lookups and report — feasible.

## 3. Comparison (proposed internal framework, not the official rubric)

Score 1–5; weighted total = Σ weight × score / 5.

| Candidate | Problem & BD relevance (20) | Mechanism & differentiation (20) | Feasibility, 2 students (25) | Demo & measurable evaluation (20) | Data compliance & adoption (15) | **Total /100** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. ShareTally (P3) | 5 | 4 | 4 | 5 | 3 | **85** |
| C. Living Certified Copy (P2) | 4 | 3 | 5 | 4 | 3 | **78** |
| F. Pre-Purchase Report (P5) | 5 | 3 | 4 | 4 | 2 | **74** |
| B. Plot Watch (P3) | 4 | 3 | 4 | 4 | 2 | **70** |
| E. L.T.-Notice Handoff (P4) | 4 | 2 | 4 | 3 | 3 | **65** |
| D. Self-checking Digitiser (P1) | 4 | 3 | 2 | 3 | 3 | **59** |

**Uncertainty behind the scores.** Real judging weights are unknown. A's adoption score assumes the land office can obtain a digital transfer feed — legally mandated (F2, F3) but politically contested between ministries; with no feed it would drop to 2 (total 82). C's problem score rests on the January 2026 fake-QR warning; if the Bhumi app already binds QR to content, its differentiation drops to 2 (74). F's adoption depends entirely on agency APIs that do not publicly exist. D's feasibility could be 3 with only printed synthetic scans, but that weakens its evidence. Differences under ~5 points are within our judgement error.

## 4. Shortlist, objections, decision

**A. ShareTally — strongest objection:** *"The data you need does not exist digitally. Historic deeds sit in paper volumes; without a complete feed most plots will show Incomplete, and integrating two ministries is not in a student team's hands."*
Response: the feed is already a legal duty (s.89) and already opens a mutation file (s.143C), so the change is digitising an existing notice, not inventing a new flow. Coverage is explicit: from the date notices are digitised, new double sales are caught; older periods are flagged Incomplete instead of passing silently. Historic backfill is a later P1 task.

**C. Living Certified Copy — strongest objection:** *"Signing proves a copy matches the issuer's database, not that the record is right. A forged deed that gets mutated produces a perfectly genuine-looking signed khatian; and QR verification via the Bhumi app already exists."*
Response: partly unanswerable — it moves trust to the issuer but does not touch the double-sale mechanism.

**Decision: A — ShareTally (P3).** It attacks the mechanism behind double selling that the rule book itself names (F1), uses only deterministic checks that a reviewer can audit, can be fully demonstrated and measured on synthetic data, and needs no privileged access for the prototype. C remains a good later add-on (signed ledger extracts).

## 5. Recommendation

- **Name:** ShareTally · Bangla: **অংশ-হিসাব** (share accounting)
- **Primary statement:** P3 — Fraud & Double-Selling Detection (P4 workflow as context)
- **One-line pitch:** ShareTally checks every registered sale against what the seller still holds, so a plot cannot be sold twice just because the khatian has not caught up.
- **Target user:** the AC (Land) office reviewer who decides mutation applications; secondary: the Sub-Registry clerk (pre-registration check).
- **Narrow problem:** a second or excessive sale passes registration and reaches mutation because the khatian is stale and nobody reconciles registered transfers against recorded shares.
- **Plain-language mechanism:** treat each plot like a bank account of shares. The khatian opens the account; every registered deed moves shares from one holder to another, oldest first. A deed that tries to move more than the seller has left bounces, with the earlier deeds shown as proof. Missing statements make the account "unconfirmed", never "fine".
- **Worked example (fictional):** see README — Joynal Namuna holds ৮ আনা (30 decimal) of BS dag 1201; deed 2023/0457 moves 20 decimal to Mizan (never mutated); deed 2026/0688 moves 20 decimal to Shapla; output `OVER_TRANSFER`, shortfall 10.00 decimal, status Conflict, action "hold and notify every earlier buyer".

## 6. Assumptions register

| Assumption | Why it matters |
| --- | --- |
| Two students with basic Python and HTML; laptops; no budget | Stack choice (Python + FastAPI + SQLite, no build step) |
| A pilot land office could receive L.T. notices digitally | Adoption path |
| Reviewers would accept a computed ledger as decision support | Adoption; to be tested with a real AC (Land) officer as mentor feedback |
| Demo clock fixed at 2026-10-01 | Reproducible results |
| Katha = 720 sq ft only in demo mouza JL 902 | Shows the converter; real values must come from land offices |

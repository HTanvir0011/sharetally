# Demo video script (≤ 3 minutes) and judge questions

## Before recording

- Run locally (`uvicorn sharetally.web:app --port 8765`), not on the free host — no cold start during recording.
- Delete `data/sharetally.db` first so the demo starts from the clean synthetic dataset.
- Browser at 1280×800, zoom 110%, light theme, other tabs closed. Use OBS Studio or the Windows Game Bar (Win+G).
- Both students speak (one drives, one narrates), in Bangla or English. Keep the "SYNTHETIC DATA" ribbon visible.
- Rehearse twice with a timer; cut words, not steps.

## Script

| Time | Screen | Say (English; adapt to Bangla) |
| --- | --- | --- |
| 0:00–0:20 | About page or title slide | "A registered sale reaches the khatian only after mutation. In a 2018 trial only about 30% of new owners mutated within three months. Until then the khatian still shows the seller, and the only safeguard against a second sale is the seller's own affidavit. ShareTally closes that window." |
| 0:20–0:50 | Clerk → *Record L.T. notice*: BS 1101, seller P-0002 (Kamrul), new buyer "Ruma Namuna", 10 decimal → **Run pre-registration check** → *No conflict found in supplied records* → **Check and save notice** | "This is the Sub-Registry clerk. Every registered deed already has to send a Land Transfer notice to the land office. Here we record one. Kamrul holds 25 decimal; selling 10 fits, so the check is clear — within the records and coverage shown. Saved." |
| 0:50–1:50 | Reviewer → *Mutation queue* → **DEMO-MC/2026/0312** (Conflict). Point at the finding, the share strip's red overflow, the timeline row for deed 2023/0457. Choose **Hold — issue notice**, type a reason, **Record decision**. | "This is the AC Land reviewer's queue, most serious first. Shapla applied for mutation with a valid-looking deed. But Joynal held 30 decimal, already sold 20 to Mizan in 2023 — Mizan never mutated, so the khatian still showed Joynal. That leaves 10, and this deed moves 20. The red stripe is land that no longer existed. The suggested action is to hold and notify the earlier buyer. 'Proceed' is disabled while a conflict exists. The decision goes into a tamper-evident log with the engine version." |
| 1:50–2:20 | Open **DEMO-MC/2026/0425** (Incomplete — coverage gap), then **DEMO-MC/2026/0410** (old RS dag) | "Honesty matters as much as detection. Here the arithmetic looks fine, but the digital index for this mouza starts in 2016 and the record dates from 2010, so the result is Incomplete, not clean. Here the deed names RS dag 245, which became two BS dags — we do not guess which. ShareTally never decides ownership; it shows whether the records add up." |
| 2:20–2:45 | *Evaluation* page | "We measured on synthetic scenarios with expected results written in advance: all 70 matched, no false flags on 30 clean plots, no incomplete case called clean. A khatian-only check would have cleared 8 of 12 problem cases. These are designed tests, not real-world accuracy — the next step is blind cases from our mentors." |
| 2:45–3:00 | Back to the case or the title | "The data feed already exists in law — SAT Act section 89. Digitise the L.T. notice, run this check inside e-mutation, pilot in one upazila. ShareTally: every share accounted for." |

**If something breaks while recording:** cut to the same screen from `docs/img/` screenshots and keep narrating; re-record only the broken segment.

## Five likely judge questions, with candid answers

1. **"Where does the deed data come from? The two offices are not integrated."**
   By law the Sub-Registrar must send an L.T. notice for every registered transfer, and the land office must open a mutation file when it receives one (SAT Act ss. 89, 143C). We only need that notice in digital form. Historic deeds are paper; for those periods we report Incomplete until they are digitised. In the prototype the feed is simulated and labelled as such.

2. **"Isn't this just a database query? Why not blockchain?"**
   Listing deeds is a query; deciding whether a seller still holds enough is not — shares come as anna notation, decimals, acres or local units, plots get split across surveys, heirs inherit fractions, and earlier deeds must keep priority. Blockchain would make the records harder to edit but not more correct: a false or missing deed stays false or missing. An append-only hash-chained audit log gives tamper evidence for our decisions at much lower cost.

3. **"What about legitimate cases — an oral family partition, or a seller holding land under another khatian?"**
   Those are false-conflict risks. The tool never rejects anything: the reviewer sees the evidence and can record "explained by evidence" with a reason. A missing khatian shows as "part of the plot has no recorded holder" (Incomplete). We expect more of these on real data, which is why the next step is testing with anonymised, organizer-approved samples.

4. **"What exactly did AI do, and can you explain the code?"**
   Claude Code helped research, draft code, tests and documents; it is disclosed in the README. In the product, AI is optional and outside the decision path: it drafts a Bangla notice that is rejected if it adds any number not in the engine's facts, and it proposes form fields that the clerk must confirm. [Each student: be ready to walk through `engine/ledger.py` and explain OVER_TRANSFER, COVERAGE_GAP and the rounding allowance.]

5. **"How would this run countrywide, and is personal data safe?"**
   Each plot's ledger is computed independently in under a millisecond on a laptop, so it scales by plot. Deployment would sit inside e-mutation as a pre-approval check, then at the Sub-Registry as a pre-registration check, owned by the Ministry of Land. The prototype holds only synthetic data; the design uses role-based access, hashed passwords, CSRF protection, audit logging, and sends no personal names to the AI (people are replaced by tokens).

Backup questions: *Why 90 days for record lag?* — a configurable threshold, chosen as roughly three times the 28-day mutation target; to be set by the ministry. *Why not compute inheritance shares?* — personal-law calculation is a legal judgement; we take fractions from the succession record and only check that they add up.

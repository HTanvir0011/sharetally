# Team plan, costs and final review

Reference time: 15 Oct 2026, 09:00 Asia/Dhaka. Conservative Round 1 deadline: **16 Oct 2026** (confirm the exact time and whether 18 Oct applies). Submit at least 3 hours before the cut-off.

The working prototype, tests and draft documents already exist (built with AI assistance, disclosed). The next 24 hours are therefore about **owning, verifying and packaging** it — the rule book requires both students to explain the code and design.

## Next 24 hours (dependency-ordered)

| Hours | Student A — engine & data | Student B — app, video & documents |
| --- | --- | --- |
| 0–1 | Confirm deadline/time with organizers. Create GitHub repo; set your own git identity; first commit. | Install and run locally (README quick start); run `pytest`; click through all three roles. |
| 1–4 | Read `engine/units.py` and `engine/ledger.py` line by line; run `pytest -k engine`; change one scenario and watch a test fail, then revert. Write a one-paragraph explanation of each rule in your own words. | Read `web.py` (routes, roles, CSRF) and `security.py`; run `pytest tests/test_security.py`; read `ai.py` and its fact check. Write your own explanation of the security design. |
| 4–6 | Ask a mentor to describe 3 new cases in plain words (without seeing the rules); turn them into scenarios in `synthetic.py`; declare the expected result **before** running; run `scripts/evaluate.py`; record the outcome honestly in `docs/evaluation.md`. | Deploy to Render (free) from the repo; set the `SHARETALLY_PW_*` secrets; check the live link on a phone; note the cold-start time. |
| 6–8 | Swap: B explains the engine to A, A explains security to B. Fix any part neither can explain (simplify or delete it). | — |
| 8–10 | Fill team/mentor names in `docs/concept-note.html`; re-export the PDF (Edge: Print → Save as PDF, or the command in that file's comment); check it is ≤ 4 pages. | Rehearse the demo script twice; record the ≤ 3-minute video; upload (unlisted). |
| 10–12 | Final README edits: AI disclosure in your own words, team table, links. | Paste `docs/submission-text.md` into the form; add repo, video, live link, PDF. |
| 12–14 | Both: final check list (below), submit, take screenshots of the confirmation. | |
| 14–24 | Rest. Buffer for platform problems. | |

### Optional 72-hour extension (only if the confirmed deadline allows, otherwise for the Final Round)

1. Blind evaluation: 10 mentor-written scenarios; report matches and misses.
2. Ask an AC (Land) officer or land lawyer (via mentors) to review the rule catalogue; adjust thresholds (90-day lag, rounding allowance) and wording.
3. "Explained by evidence" attachments (partition deed reference) that suppress a specific finding on re-check.
4. Signed ledger extract (QR + Ed25519) for a case decision — candidate C as an add-on.
5. Bangla-first UI pass and screen-reader check; reviewer timing study (time to find the conflict with and without ShareTally on 5 cases).
6. Pitch deck (≤ 10 slides, PDF) for the Final Round; record "Changes since Round 1" in the README.

### Fallbacks

| If this fails | Do this |
| --- | --- |
| Deployment | Submit without a live link (recommended, not mandatory); the video shows the local run. |
| AI calls (no key, network, refusal) | Nothing to do — templates and the rule-based reader are the default path. |
| A student cannot explain a component | Remove or simplify it (e.g. drop RAPID_RESALE or the deed-text reader) rather than present code you cannot defend. |
| Video recording | Record the screen with narration in one take per segment; use screenshots from `docs/img` for any broken step. |
| PDF export over 4 pages | Remove the screenshot figure first, then shorten section 6. |

### Cost assumptions

| Item | Cost |
| --- | --- |
| Hosting (Render free web service) | 0 BDT; sleeps after 15 min idle, ~1 min wake-up, data resets on restart |
| Domain | none (use the host's subdomain) |
| AI (optional) | Claude Opus 5.5 is priced at $4 / $20 per million input/output tokens; a notice draft is roughly 1.5 thousand input and up to 1 thousand output tokens, i.e. about 2–3 US cents per click. A few dozen demo clicks cost around $1. |
| Tools | Python, VS Code, OBS — free |

## What to cut first if time runs out

1. Deed-text reader (keep the manual form).
2. AI notice drafting (keep the template text).
3. Rapid-resale and record-lag attention codes.
Keep at all costs: `OVER_TRANSFER`, `DEED_NOT_IN_INDEX`, the Incomplete statuses, the reviewer decision with audit log, and the evaluation page.

## Final critical review

**Biggest weakness.** Real value depends on a complete digital feed of registered transfers that does not exist publicly today, and on two ministries agreeing to use it. Without it, most real plots would show Incomplete. The prototype demonstrates the check, not the integration.

**Verify before submitting.**
- Deadline date and time; which uploads are mandatory.
- Legal citations (SAT Act ss. 89, 143C; Registration Act s.52A; TPA s.48; Land Crimes Act s.4) — read them yourselves on bdlaws and ask the faculty mentor to confirm the wording in the concept note.
- That every screen and file shows only synthetic data (search the repo for any real name or NID-like number).
- AI disclosure written in your own words; team and mentor names correct; no invented credentials.
- `pytest` passes on a clean clone; the live link loads (or is omitted).

**Precise next action.** Student A: confirm the deadline with the organizers and create the GitHub repository with your own git identity. Student B: run `pytest` and the app locally, then start reading `engine/ledger.py` together.

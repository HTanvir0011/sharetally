# 0006 — AI is optional, outside the decision path and behind a deterministic fallback

**Status:** Accepted; amendment proposed · **Date:** 2026-10-15

## Context

AI can help with two narrow tasks: drafting a plain-Bangla notice from findings, and reading pasted deed text into form fields. It must never decide ownership, label anyone fraudulent or change a status, and the demo must work offline.

## Decision

`ai.py` calls a Claude model only when credentials exist. Notice drafts are checked against the engine's facts and replaced by deterministic template text when a check fails or the API is unavailable. Extracted fields are proposals in a form the clerk must confirm; the app, not the model, matches people and plots to database IDs.

**Amendment (proposed):**

1. Correct the documented claim. The check rejects digit sequences not in the facts, unknown person tokens and a listed set of accusatory words; it does **not** catch numbers written as words, swapped values or ownership statements (AI-1, re-verified). Fix the wording now (F-00a) in the README, submission text, concept note (HTML and PDF), deck (HTML and PDF), demo script, case page (`case.html`), About page (`about.html`), the success label returned by `ai.draft_notice` ("numbers match engine facts", shown by `app.js`) and the `ai.py` docstring.
2. Switch AI off on the public demo (F-00c) and on any pilot data regardless of configuration.
3. Pseudonymise at the source by giving the explanation layer token names, instead of replacing names in finished text (AI-2); merge extracted fields instead of replacing the rule parser's (AI-3). Deed-text extraction currently sends the pasted text, names included, unchanged (register VER-3): either tokenise it first or say so plainly wherever data minimisation is described.
4. Later: slot-based drafting (the model writes `{F1.held_dec}` placeholders and may not write any number), with a small offline evaluation before any model or prompt change.

## Alternatives considered

- **No AI at all:** simplest and safest; loses a useful Bangla drafting aid.
- **AI ranking or classifying fraud risk:** rejected — no lawful training data, not explainable, risks harming people.

## Consequences

- AI quality, cost and latency are not measured today (AI-4); claims about them must stay out of the pitch until measured.
- Blocking AI calls currently stall the single server process (WEB-1); calls must move off the event loop with a short timeout (F-05).

## Related

Audit AI-1 to AI-5, WEB-1, OPS-1 · Improvements F-00a, F-00c, F-05

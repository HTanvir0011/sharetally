# 0010 — One finding catalogue and rule configuration, not a plugin registry

**Status:** Proposed · **Date:** 2026-10-15

## Context

`compute_ledger()` is a single function of about 300 lines. Each finding's level is passed as a literal at its call site; the plot-wide set lives in `ledger.py`, the code list is repeated in `evaluation.py`, and titles and actions live in `explain.py`. Fact keys for the same code differ between call sites (ENG-12). Thresholds (90-day lag, 90-day rapid resale, tolerance floors) are hard-coded and not recorded on results (ENG-14). Adding a rule means editing three or four files, which makes the rules harder for both students to explain.

## Decision

- `engine/codes.py`: one frozen `Code` record per finding code — level, plot-wide flag, English and Bangla title and action, required fact keys, and basis (a verified citation or "design policy"). `PLOT_WIDE`, the evaluation code list and the explanation titles are derived from it, and a test checks that every emitted finding carries its required facts.
- `engine/policy.py`: a frozen `RuleConfig` (lag days, rapid-resale days, tolerance policy, grace days, supported deed types, order key) passed to `compute_ledger` and recorded on every `Ledger`.
- Later, behind golden snapshots: split `compute_ledger` into named phase functions over a shared state object.

## Alternatives considered

- **A dynamic rule-plugin registry:** flexible, but overkill for 14 codes today (about 20 after the proposed additions) and harder to explain.
- **Leave as is:** works today, but every new rule risks drift between files.

## Consequences

- A "new finding code" checklist in CONTRIBUTING becomes short and testable.
- In a pilot, `RuleConfig` grows into versioned rule sets approved by a land official and cited on every result.

## Related

Audit ENG-12, ENG-14 · Improvement Tier C (catalogue), pilot rule sets

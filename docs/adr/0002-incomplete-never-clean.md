# 0002 — Missing or unmodelled data is reported as Incomplete, never clean

**Status:** Accepted · **Date:** 2026-10-15

## Context

Real land records are incomplete: older deeds are on paper, digital indexes start at different dates, units vary by locality, old-survey dags were split, and heir lists can be partial. A check that reports "no conflict" whenever it found nothing would give false assurance in exactly the cases where a reviewer most needs caution.

## Decision

The engine has four statuses ranked conflict > incomplete > attention > no conflict. Any condition that prevents a confident answer — a gap in registry coverage, an undefined unit, an ambiguous old-survey reference, heir shares that do not add up, a seller with no recorded source — produces an **incomplete** finding. The No conflict verdict on case and plot pages says "Within the records and coverage shown, shares add up. This is not a title guarantee." (Short labels in the queue, plot list and dashboard, and the "proceed" decision label, still say plain "No conflict" and should become "No conflict in supplied records".) The reviewer cannot record "proceed" while a case is Conflict or Incomplete.

## Alternatives considered

- **Best-guess resolution** (for example assume a standard bigha, or pick the larger of two split dags): fewer Incomplete results, but silent guesses would be indefensible.
- **Two statuses only** (pass/fail): simpler, but hides the difference between "records disagree" and "records are missing".

## Consequences

- On real data a large share of results will be Incomplete until historic deeds are digitised; this is reported, not hidden.
- Every new input path must keep the rule. The audit and the documentation review found paths that broke it: deed items whose reference cannot be placed disappear (DATA-1), unmodelled deed types still move shares (ENG-8), and a case the engine did not evaluate is shown as No conflict (VER-1). A related gap hides a Conflict behind Incomplete: share quantities are skipped when the plot area is unknown (ENG-11). Fixes F-14, F-15 and F-18 restore the rule; the pilot inbox must make quarantined notices hold back coverage.

## Related

Audit DATA-1, ENG-8, ENG-11, DATA-2, VER-1 · Improvements F-13, F-14, F-15, F-18 · ADR 0011

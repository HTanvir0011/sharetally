# 0011 — Registry coverage per office with a "complete through" date

**Status:** Proposed · **Date:** 2026-10-15

## Context

Coverage is stored per mouza with an open end that the code treats as `date.max`, and the coverage test (`_covered`) never considers which office registered a cited deed; the office is used only to look the deed up. A mutation citing a deed registered two days ago, whose L.T. notice has not arrived, or a deed from an office whose index is not loaded, is reported as **Conflict** (deed not in index) instead of unverifiable (DATA-2, re-verified). This is the most likely false conflict a judge could trigger ("what if the notice is late?"). The L.T. notice itself is not stored as an entity, so there is no received date to reason with.

## Decision

- New `lt_notice` table: deed, sending office, notice number, received date, received by, channel.
- `coverage` becomes `(office, mouza_id, start_date, complete_through, note)`.
- A cited deed that **is found** in the index is always compared on parties, date, quantity and plot, whatever its date.
- A cited deed that **is not found** is classified in bands:
  1. office not indexed for the mouza → `CITED_DEED_UNVERIFIABLE` (incomplete; reason "office not indexed");
  2. date before the index start or inside a gap → `CITED_DEED_UNVERIFIABLE` (incomplete; reason "older than the index"), and the plot also carries `COVERAGE_GAP`;
  3. date after `complete_through` minus grace days (the trailing window) → `CITED_DEED_UNVERIFIABLE` (incomplete; reason "the L.T. notice may not have arrived; index complete through D");
  4. otherwise → `DEED_NOT_IN_INDEX` (conflict).
- For the plot's own replay, gaps are `COVERAGE_GAP`; the trailing window is not a gap, and every result states `records_complete_through` per office instead.
- A mouza counts as complete through date D only if every office with jurisdiction is (including the District Registrar's office unless confirmed otherwise — Q4).

## Alternatives considered

- **Keep per-mouza open-ended coverage:** simple, but produces false conflicts for late notices.
- **Treat the trailing window as a coverage gap:** with a live feed, which always trails today, every check would become Incomplete.
- **Skip cited deeds dated in the trailing window:** rejected in review — a fictitious deed given a recent date would then get no finding at all, a new false-clean path.

## Consequences

- Grace days are a labelled demo assumption, never a legal or statistical claim.
- `CITED_DEED_UNVERIFIABLE` broadens from "older than the index" to "cannot be checked against the index", with the reason carried in its facts; its title and explanation in `explain.py` change accordingly. Scenario S05 keeps its expected codes.
- In a pilot, a quarantined notice must hold back `complete_through` for its office and mouza until resolved, or quarantine becomes a new false-clean path.

## Related

Audit DATA-2 · Improvement F-13 · ADR 0002 · Open question Q4

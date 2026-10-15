# 0008 — Deterministic event order; "already reflected" decided by registration date

**Status:** Proposed, pending legal review · **Date:** 2026-10-15

## Context

Two choices determine who keeps a share when sales compete, and which deeds the khatian already reflects:

1. **Replay order.** Today events are sorted by execution date, then kind (an inheritance before a transfer on the same day), registration date, the proposed flag and the deed reference *as a string*, and ties keep database row order. So "2024/99" vs "2024/0100", or the order of items within one deed, can decide which buyer is flagged (ENG-3), and a re-entered notice with different zero-padding is credited twice (DATA-5).
2. **Reflection gate.** Today any transfer *executed* on or before the khatian's record date is treated as already reflected and is never replayed. A deed executed before the record date but registered after it cannot be reflected, so a later double sale reads only as Attention (ENG-2, re-verified).

## Decision

- **Total, deterministic order:** `(execution_date, kind, registration_date, proposed, office, reg_year, serial, item_id)` with canonical integer deed numbers and `UNIQUE(office, reg_year, serial)`. Every input list is sorted on entry and rows have a full tie-break, so output is identical under any input order.
- **Same-day ties stay Conflict:** when one seller's transfers on the same execution date together exceed the holding, report `OVER_TRANSFER` with subtype `same_day_priority_undetermined`, naming every deed, without picking a winner.
- **Reflection gate by registration date, for saved and proposed deeds alike:** a transfer is pre-record only if `registration_date <= record_date`; if no approved mutation cites it, add `PRE_RECORD_UNCONFIRMED` — incomplete when the same seller has a later transfer on the dag, otherwise attention.

## Alternatives considered

- **Order by registration date throughout:** a back-dated deed could then never displace an earlier-registered one. This may be the legally correct rule; it is kept as the alternative to decide with the mentor (Q1).
- **Report same-day ties as Incomplete:** rejected — an over-transfer is certain; only its attribution is not.

## Consequences

- Results no longer depend on database row order; golden snapshots can be compared byte for byte.
- Whether priority follows execution or registration date is open question Q1 (Registration Act s.47 and Transfer of Property Act s.48 are relevant; we have not interpreted them). That answer, and the meaning of `record_date` for survey khatians (Q3), are needed before the rule is presented as more than a design choice.

## Related

Audit ENG-2, ENG-3, DATA-5 · Improvements F-03, F-10 · Open questions Q1, Q3

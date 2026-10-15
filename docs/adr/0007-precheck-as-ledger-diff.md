# 0007 — The pre-registration check compares the ledger without and with the proposal

**Status:** Proposed · **Date:** 2026-10-15

## Context

The clerk's check currently shows only findings on the proposed deed plus plot-wide incomplete or conflict findings. A proposal given an earlier execution date than a deed already registered is replayed first, takes priority, and pushes the earlier deed into OVER_TRANSFER — but that finding is not on the proposal, so the clerk sees "No conflict" (ENG-1, re-verified). This is the core double-selling pattern, at the one moment it could be raised before registration. Whether a Sub-Registrar may refuse or defer registration on such a finding is a legal question; ShareTally itself never blocks a registration (ADR 0009).

## Decision

`engine/precheck.py` computes the ledger without and with the proposal and reports:

- the proposal's own findings;
- findings it induces, keyed by **(code, subject)** — the transfer, case or holding the finding is about — and classified as new, worsened, unchanged or resolved;
- every mutation case whose status gets worse;
- plot-wide incomplete or conflict findings.

The check status is the worst of these. A back-dating finding is defined by registration order: flag transfer T when another transfer U by the same seller on the dag has `U.registration_date < T.registration_date` and `T.execution_date < U.execution_date`, so T is replayed ahead of a deed registered before it. It is attention level on its own; the conflict is the induced `OVER_TRANSFER` when the reordering reduces what U can move. Same-day executions are handled by ADR 0008 (`same_day_priority_undetermined`). The wording states the dates neutrally. One implementation in `services/intake.py` serves both the form and the API, and proposals pass through the same record-date gate as saved deeds so the check and the stored ledger agree.

## Alternatives considered

- **Show the full ledger to the clerk:** complete, but buries the effect of this specific deed.
- **Key induced findings by their related-record set:** a reviewer showed this misattributes findings that already existed.
- **Define back-dating by replay order:** lands the finding on the wrong (honest) deed.
- **Compare T's execution date with U's registration date:** would also flag ordinary sales whose execution-to-registration windows merely overlap.

## Consequences

- The clerk sees the proposal's effect on everyone else on the dag.
- After saving, the stored ledger attaches the back-dating finding to the later-registered deed, and the `OVER_TRANSFER` explanation names the deed that took priority by execution date. Under execution-date priority the earlier-registered deed and its mutation case still show Conflict; whether that is right depends on Q1.
- Which date decides priority is a legal question (ADR 0008, Q1).

## Related

Audit ENG-1, WEB-8 · Improvement F-02 · ADR 0008

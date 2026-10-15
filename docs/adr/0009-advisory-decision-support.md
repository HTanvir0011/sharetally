# 0009 — Advisory, read-only decision support beside e-Mutation

**Status:** Proposed · **Date:** 2026-10-15

## Context

Mutation is ordered by the Assistant Commissioner (Land) through the e-Mutation system; deeds are registered by Sub-Registry offices. ShareTally has no access to either system, and no public API for them is known. Automatic blocking or automatic mutation without notice and appeal was criticised where it was tried elsewhere (Telangana's 2020 system was replaced in 2025).

## Decision

ShareTally is decision support beside the officer, never inside the decision:

- It keeps its own copy of notices and record snapshots and publishes a versioned, read-only check contract (for example `GET /api/v1/mutation-cases/{case}/check`) returning status, findings, evidence references, rule set, `records_complete_through` per office and a disclaimer.
- If a check cannot run, the result is **Not checked**, never clean.
- It never writes to e-Mutation, DLRMS or the registration system, never blocks a registration and never auto-approves or rejects a case. Mutation decisions stay in e-Mutation (assumption); ShareTally records the officer's override reason when it is fed back.
- Every counterpart interface in the documents is marked as an **assumption** until an owner agrees to it.

## Alternatives considered

- **Embedded gate in e-Mutation that blocks approval on Conflict:** stronger, but turns a records-consistency signal into a legal decision and needs an integration that does not exist.
- **Automatic mutation on registration:** outside the project's scope and authority.

## Consequences

- On the e-Mutation side, adoption needs only a read-only call, or none (officers can use the web UI). The inbound data (L.T. notices, a khatian extract and coverage per office) still needs the government cooperation listed in the improvement architecture, section 5, none of which exists today.
- The pilot's shadow mode needs a safety escalation so that a likely double sale is not withheld while a mutation proceeds.

## Related

Improvement architecture sections 5 and 6 · ADR 0002

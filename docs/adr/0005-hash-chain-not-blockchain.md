# 0005 — Tamper evidence through a hash chain and external checkpoints, not a blockchain

**Status:** Accepted; amendment proposed (serialisation, checkpoints) · **Date:** 2026-10-15

## Context

Reviewers' decisions and recorded notices should be tamper-evident. Blockchain is often suggested for land records, but it cannot make a false or missing deed correct, and putting personal data on an immutable shared ledger would make correcting or erasing it impossible, which is likely to conflict with data-protection requirements (which rules apply in Bangladesh is a question for the mentor).

## Decision

Keep an append-only `audit_log` in which each entry stores SHA-256(previous hash + canonical JSON of the entry); `verify()` recomputes the chain. Each decision's audit entry records the decision, engine status, engine version and a SHA-256 of the note. The review row itself, and the content of a recorded notice (its audit entry holds only the deed number, plot and status at entry), are outside the chain.

**Amendment (proposed, F-04 and pilot):** take the database write lock at the start of each transaction and write the domain rows and the audit row together; include the sequence number in the hash under a `hash_version`; make `prev_hash` unique; keep anonymous login failures out of the chain; publish a checkpoint (sequence, head hash, entry count) outside the database — printed and countersigned in a pilot — so that rewriting or truncating the log can be detected.

## Alternatives considered

- **Public or permissioned blockchain:** high cost and key management, no protection against false inputs, conflicts with erasure of personal data.
- **No tamper evidence:** simpler, but weakens trust in recorded decisions.

## Consequences

- Honest wording is required: the chain proves "no change since the last checkpoint", nothing about whether records were true.
- The chain shows only that audit entries are unchanged; deed and review rows can be edited without breaking it (DATA-6) until record hashes are added in the pilot.
- The audit found that appends fork the chain under concurrent writers (WEB-2, DATA-8, re-verified with threads); in today's single-process app all writers run on the event loop, so the fork is latent until handlers move to threads (F-05) or extra workers are added. Deleting the newest rows still verifies (WEB-3). The amendment removes the fork and limits undetectable tail deletion to entries written after the latest published checkpoint.

## Related

Audit WEB-2, WEB-3, WEB-4, DATA-6, DATA-8 · Improvement F-04 · ADR 0004

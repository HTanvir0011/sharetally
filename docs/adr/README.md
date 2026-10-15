# Architecture decision records

Each record states one decision, why it was made, what was rejected and what follows from it. Records 0001–0006 describe the prototype as built for Round 1 (proposed amendments inside them are marked as proposed); 0007–0011 are proposals from the [improvement architecture](../improvement-architecture.md) and become "Accepted" only when implemented and reviewed by the team.

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-exact-fraction-arithmetic.md) | Exact fraction arithmetic for all shares and areas | Accepted |
| [0002](0002-incomplete-never-clean.md) | Missing or unmodelled data is reported as Incomplete, never clean | Accepted |
| [0003](0003-server-rendered-ui.md) | Server-rendered pages without a JavaScript framework | Accepted |
| [0004](0004-sqlite-prototype-postgres-pilot.md) | SQLite in one process for the prototype; PostgreSQL for a pilot | Accepted (prototype), Proposed (F-17 guardrails, pilot) |
| [0005](0005-hash-chain-not-blockchain.md) | Tamper evidence through a hash chain and external checkpoints, not a blockchain | Accepted, amendment proposed |
| [0006](0006-ai-outside-decision-path.md) | AI is optional, outside the decision path and behind a deterministic fallback | Accepted, amendment proposed |
| [0007](0007-precheck-as-ledger-diff.md) | The pre-registration check compares the ledger without and with the proposal | Proposed |
| [0008](0008-event-order-and-reflection-gate.md) | Deterministic event order; "already reflected" decided by registration date | Proposed, pending legal review |
| [0009](0009-advisory-decision-support.md) | Advisory, read-only decision support beside e-Mutation | Proposed |
| [0010](0010-finding-catalogue.md) | One finding catalogue and rule configuration, not a plugin registry | Proposed |
| [0011](0011-office-aware-coverage.md) | Registry coverage per office with a "complete through" date | Proposed |

Template for new records: **Status · Date · Context · Decision · Alternatives considered · Consequences · Related**. Write them in plain language; both students must be able to defend every record in Q&A.

These records were drafted with AI assistance (Claude Code) on 15 October 2026 and must be reviewed by the team.

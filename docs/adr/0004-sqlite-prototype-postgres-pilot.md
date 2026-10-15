# 0004 — SQLite in one process for the prototype; PostgreSQL for a pilot

**Status:** Accepted for the prototype; Proposed for the Final Round guardrails (F-17) and the pilot · **Date:** 2026-10-15

## Context

The prototype holds only synthetic, reseedable data and must run on a laptop and a free host. A pilot would hold officials' decisions and an audit log that must not be lost, with several concurrent users and access control.

## Decision

- **Prototype (as built):** SQLite in WAL mode, one uvicorn process, a connection per request, schema created at start-up.
- **Final Round (proposed, F-17):** add `meta.schema_version` and a dataset hash; bootstrap refuses a stale demo database or reseeds on request, instead of adopting a migration framework.
- **Pilot:** PostgreSQL 16 only, with numbered plain-SQL migrations, append-only grants on audit and record tables, encrypted backups and restore drills. Freeze the SQLite demo at the Final Round tag instead of maintaining two backends.

## Alternatives considered

- **PostgreSQL from day one:** more realistic, but adds setup and hosting cost with no benefit for synthetic demo data.
- **Keep SQLite and PostgreSQL in parallel through the pilot:** a reviewer showed this conflicts with PostgreSQL-only features the pilot relies on (row locking, grants).

## Consequences

- The prototype is easy to run and reset; on Render the disk is ephemeral and the demo resets on restart.
- SQLite-specific SQL is spread across `web.py`, `security.py` and `audit.py` (DATA-9); moving it behind storage functions is part of the pilot work.
- Concurrency must be handled explicitly: audit appends need a write lock taken at the start of the transaction (ADR 0005, F-04).

## Related

Audit DATA-9, OPS-3, WEB-2 · Improvements F-17, F-04

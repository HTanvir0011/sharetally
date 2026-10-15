"""Append-only, hash-chained audit log.

Each entry stores SHA-256(previous hash + canonical JSON of the entry). Editing or
deleting any earlier row breaks every later hash, which :func:`verify` reports.
Limit: someone with write access to the whole database could rebuild the entire
chain; publishing or printing the head hash periodically closes that gap.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

GENESIS = "0" * 64


def _canonical(ts: str, actor: str, role: str, action: str, obj: str, detail: str) -> str:
    return json.dumps({"ts": ts, "actor": actor, "role": role, "action": action, "object": obj, "detail": detail},
                      sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(prev: str, canonical: str) -> str:
    return hashlib.sha256((prev + canonical).encode()).hexdigest()


def append(conn: sqlite3.Connection, actor: str, role: str, action: str, obj: str, detail: dict | None = None) -> str:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    detail_json = json.dumps(detail or {}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    row = conn.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
    prev = row["hash"] if row else GENESIS
    digest = _digest(prev, _canonical(ts, actor, role, action, obj, detail_json))
    conn.execute("INSERT INTO audit_log (ts, actor, role, action, object, detail, prev_hash, hash) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ts, actor, role, action, obj, detail_json, prev, digest))
    conn.commit()
    return digest


def verify(conn: sqlite3.Connection) -> dict:
    prev = GENESIS
    count = 0
    for r in conn.execute("SELECT * FROM audit_log ORDER BY seq"):
        count += 1
        expected = _digest(prev, _canonical(r["ts"], r["actor"], r["role"], r["action"], r["object"], r["detail"]))
        if r["prev_hash"] != prev or r["hash"] != expected:
            return {"ok": False, "entries": count, "first_bad_seq": r["seq"], "head": None}
        prev = r["hash"]
    return {"ok": True, "entries": count, "first_bad_seq": None, "head": prev}

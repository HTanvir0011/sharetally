"""SQLite storage: schema, connection helper and synthetic-data seeding."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS mouza (
    id TEXT PRIMARY KEY, name_en TEXT NOT NULL, name_bn TEXT NOT NULL, jl_no TEXT NOT NULL,
    upazila TEXT NOT NULL, district TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS local_unit (
    mouza_id TEXT NOT NULL REFERENCES mouza(id), unit TEXT NOT NULL, decimals TEXT NOT NULL, note TEXT,
    PRIMARY KEY (mouza_id, unit));

CREATE TABLE IF NOT EXISTS person (id TEXT PRIMARY KEY, name_en TEXT NOT NULL, name_bn TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS plot (
    id TEXT PRIMARY KEY, mouza_id TEXT NOT NULL REFERENCES mouza(id), survey TEXT NOT NULL, dag_no TEXT NOT NULL,
    area_raw TEXT NOT NULL, record_date TEXT NOT NULL, record_ref TEXT NOT NULL, scenario TEXT, title TEXT,
    UNIQUE (mouza_id, survey, dag_no));

CREATE TABLE IF NOT EXISTS holding (
    id TEXT PRIMARY KEY, plot_id TEXT NOT NULL REFERENCES plot(id), person_id TEXT NOT NULL REFERENCES person(id),
    khatian_no TEXT NOT NULL, share_raw TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS deed (
    id TEXT PRIMARY KEY, office TEXT NOT NULL, deed_no TEXT NOT NULL, deed_type TEXT NOT NULL,
    execution_date TEXT NOT NULL, registration_date TEXT NOT NULL, received_via TEXT NOT NULL,
    created_by TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE (office, deed_no));

CREATE TABLE IF NOT EXISTS deed_item (
    id TEXT PRIMARY KEY, deed_id TEXT NOT NULL REFERENCES deed(id), mouza_id TEXT NOT NULL REFERENCES mouza(id),
    plot_ref TEXT NOT NULL DEFAULT '', plot_id TEXT REFERENCES plot(id),
    seller_id TEXT NOT NULL REFERENCES person(id), buyer_id TEXT NOT NULL REFERENCES person(id),
    quantity_raw TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS crosswalk (
    mouza_id TEXT NOT NULL, old_survey TEXT NOT NULL, old_dag TEXT NOT NULL, plot_id TEXT NOT NULL REFERENCES plot(id),
    note TEXT);

CREATE TABLE IF NOT EXISTS inheritance (
    id TEXT PRIMARY KEY, plot_id TEXT NOT NULL REFERENCES plot(id), deceased_id TEXT NOT NULL REFERENCES person(id),
    event_date TEXT NOT NULL, certificate_ref TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS heir (
    inheritance_id TEXT NOT NULL REFERENCES inheritance(id), person_id TEXT NOT NULL REFERENCES person(id),
    fraction_raw TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS mutation_case (
    id TEXT PRIMARY KEY, case_no TEXT NOT NULL UNIQUE, plot_id TEXT NOT NULL REFERENCES plot(id),
    filed_date TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('pending','approved','rejected')),
    basis_office TEXT NOT NULL, basis_deed_no TEXT NOT NULL, basis_deed_date TEXT NOT NULL,
    from_id TEXT NOT NULL REFERENCES person(id), to_id TEXT NOT NULL REFERENCES person(id),
    quantity_raw TEXT NOT NULL, decided_date TEXT);

CREATE TABLE IF NOT EXISTS coverage (
    id TEXT PRIMARY KEY, mouza_id TEXT NOT NULL REFERENCES mouza(id), source TEXT NOT NULL,
    start_date TEXT NOT NULL, end_date TEXT, note TEXT);

CREATE TABLE IF NOT EXISTS expected (
    object_type TEXT NOT NULL, object_id TEXT NOT NULL, status TEXT NOT NULL, codes TEXT NOT NULL,
    scenario TEXT NOT NULL, description TEXT NOT NULL, PRIMARY KEY (object_type, object_id));

CREATE TABLE IF NOT EXISTS review (
    id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL REFERENCES mutation_case(id),
    decision TEXT NOT NULL, note TEXT NOT NULL, reviewer TEXT NOT NULL, engine_status TEXT NOT NULL,
    engine_version TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS app_user (
    username TEXT PRIMARY KEY, role TEXT NOT NULL CHECK (role IN ('reviewer','clerk','auditor')),
    display_name TEXT NOT NULL, pw_salt TEXT NOT NULL, pw_hash TEXT NOT NULL, pw_iterations INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS session (
    token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES app_user(username), csrf TEXT NOT NULL,
    created_at REAL NOT NULL, expires_at REAL NOT NULL);

CREATE TABLE IF NOT EXISTS login_attempt (key TEXT NOT NULL, ts REAL NOT NULL);

CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, actor TEXT NOT NULL, role TEXT NOT NULL,
    action TEXT NOT NULL, object TEXT NOT NULL, detail TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE INDEX IF NOT EXISTS idx_item_plot ON deed_item(plot_id);
CREATE INDEX IF NOT EXISTS idx_case_plot ON mutation_case(plot_id);
CREATE INDEX IF NOT EXISTS idx_holding_plot ON holding(plot_id);
CREATE INDEX IF NOT EXISTS idx_attempt_key ON login_attempt(key, ts);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _insert(conn: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])


def seed(conn: sqlite3.Connection, dataset: dict) -> None:
    """Load a dataset produced by :func:`sharetally.synthetic.build_dataset`."""
    with transaction(conn):
        _insert(conn, "mouza", dataset["mouzas"])
        _insert(conn, "local_unit", dataset["local_units"])
        _insert(conn, "coverage", dataset["coverage"])
        _insert(conn, "person", dataset["persons"])
        _insert(conn, "plot", dataset["plots"])
        _insert(conn, "holding", dataset["holdings"])
        _insert(conn, "deed", dataset["deeds"])
        _insert(conn, "deed_item", dataset["deed_items"])
        _insert(conn, "crosswalk", dataset["crosswalk"])
        _insert(conn, "inheritance", dataset["inheritances"])
        _insert(conn, "heir", [{"inheritance_id": h["inheritance_id"], "person_id": h["person_id"],
                                "fraction_raw": h["fraction_raw"]} for h in dataset["heirs"]])
        _insert(conn, "mutation_case", dataset["mutation_cases"])
        _insert(conn, "expected", [{**e, "codes": json.dumps(e["codes"])} for e in dataset["expected"]])
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('as_of', ?)", (dataset["as_of"],))


def is_seeded(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM plot").fetchone()[0] > 0

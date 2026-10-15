"""Read model: turns database rows into engine inputs and display helpers."""

from __future__ import annotations

import re
import sqlite3
from datetime import date
from fractions import Fraction

from .engine.ledger import (Heir, Holding, Inheritance, Ledger, MutationCase, Period, PlotRecord, RegistryEntry,
                            Transfer, compute_ledger)

_OLD_REF = re.compile(r"^\s*(CS|SA|RS|BS|BRS)\s*(?:dag\s*)?([0-9A-Za-z/-]+)\s*$", re.IGNORECASE)


def d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def deed_ref(office: str, deed_no: str) -> str:
    return f"{office} {deed_no}"


def get_as_of(conn: sqlite3.Connection) -> date:
    row = conn.execute("SELECT value FROM meta WHERE key = 'as_of'").fetchone()
    return date.fromisoformat(row["value"]) if row else date.today()


def registry_lookup(conn: sqlite3.Connection):
    def lookup(office: str, deed_no: str) -> RegistryEntry | None:
        row = conn.execute("SELECT * FROM deed WHERE office = ? AND deed_no = ?", (office, deed_no)).fetchone()
        if row is None:
            return None
        return RegistryEntry(row["id"], deed_ref(row["office"], row["deed_no"]), d(row["execution_date"]),
                             d(row["registration_date"]))
    return lookup


def crosswalk_candidates(conn: sqlite3.Connection, mouza_id: str, plot_ref: str) -> tuple[str, ...]:
    m = _OLD_REF.match(plot_ref or "")
    if not m:
        return ()
    rows = conn.execute(
        "SELECT plot_id FROM crosswalk WHERE mouza_id = ? AND upper(old_survey) = ? AND old_dag = ? ORDER BY plot_id",
        (mouza_id, m.group(1).upper(), m.group(2))).fetchall()
    return tuple(r["plot_id"] for r in rows)


def _transfer_from_row(row: sqlite3.Row, candidates: tuple[str, ...] = ()) -> Transfer:
    return Transfer(
        id=row["item_id"], deed_id=row["deed_id"], deed_ref=deed_ref(row["office"], row["deed_no"]),
        office=row["office"], deed_no=row["deed_no"], deed_type=row["deed_type"],
        execution_date=d(row["execution_date"]), registration_date=d(row["registration_date"]),
        seller_id=row["seller_id"], buyer_id=row["buyer_id"], quantity_raw=row["quantity_raw"],
        plot_ref=row["plot_ref"], candidates=candidates)


_ITEM_SQL = """
SELECT di.id AS item_id, di.deed_id, di.plot_id, di.plot_ref, di.mouza_id, di.seller_id, di.buyer_id,
       di.quantity_raw, de.office, de.deed_no, de.deed_type, de.execution_date, de.registration_date
FROM deed_item di JOIN deed de ON de.id = di.deed_id
"""


def load_plot(conn: sqlite3.Connection, plot_id: str, extra_transfers: tuple[Transfer, ...] = (),
              extra_cases: tuple[MutationCase, ...] = ()) -> PlotRecord | None:
    plot = conn.execute("SELECT * FROM plot WHERE id = ?", (plot_id,)).fetchone()
    if plot is None:
        return None
    holdings = [Holding(r["id"], r["person_id"], r["share_raw"], r["khatian_no"])
                for r in conn.execute("SELECT * FROM holding WHERE plot_id = ? ORDER BY id", (plot_id,))]

    transfers = [_transfer_from_row(r) for r in conn.execute(_ITEM_SQL + " WHERE di.plot_id = ?", (plot_id,))]
    for r in conn.execute(_ITEM_SQL + " WHERE di.plot_id IS NULL AND di.mouza_id = ?", (plot["mouza_id"],)):
        candidates = crosswalk_candidates(conn, r["mouza_id"], r["plot_ref"])
        if plot_id in candidates:
            transfers.append(_transfer_from_row(r, candidates if len(candidates) > 1 else ()))
    transfers.extend(extra_transfers)

    inheritances = []
    for r in conn.execute("SELECT * FROM inheritance WHERE plot_id = ? ORDER BY event_date", (plot_id,)):
        heirs = tuple(Heir(h["person_id"], h["fraction_raw"])
                      for h in conn.execute("SELECT * FROM heir WHERE inheritance_id = ?", (r["id"],)))
        inheritances.append(Inheritance(r["id"], r["deceased_id"], d(r["event_date"]), r["certificate_ref"], heirs))

    mutations = [case_from_row(r) for r in
                 conn.execute("SELECT * FROM mutation_case WHERE plot_id = ? ORDER BY filed_date", (plot_id,))]
    mutations.extend(extra_cases)

    coverage = [Period(d(r["start_date"]), d(r["end_date"]) or date.max)
                for r in conn.execute("SELECT * FROM coverage WHERE mouza_id = ? AND source = 'registry_index'",
                                      (plot["mouza_id"],))]
    local_units = {r["unit"]: Fraction(r["decimals"])
                   for r in conn.execute("SELECT * FROM local_unit WHERE mouza_id = ?", (plot["mouza_id"],))}
    return PlotRecord(plot_id, plot_label(conn, plot_id), plot["area_raw"], d(plot["record_date"]),
                      plot["record_ref"], holdings, transfers, inheritances, mutations, coverage, local_units)


def case_from_row(r: sqlite3.Row) -> MutationCase:
    return MutationCase(r["id"], r["case_no"], d(r["filed_date"]), r["status"], r["basis_office"],
                        r["basis_deed_no"], d(r["basis_deed_date"]), r["from_id"], r["to_id"], r["quantity_raw"],
                        d(r["decided_date"]))


def ledger_for(conn: sqlite3.Connection, plot_id: str, as_of: date | None = None,
               extra_transfers: tuple[Transfer, ...] = (), extra_cases: tuple[MutationCase, ...] = ()) -> Ledger | None:
    record = load_plot(conn, plot_id, extra_transfers, extra_cases)
    if record is None:
        return None
    return compute_ledger(record, as_of or get_as_of(conn), registry_lookup(conn))


def plot_label(conn: sqlite3.Connection, plot_id: str) -> str:
    r = conn.execute("""SELECT p.survey, p.dag_no, m.name_en, m.jl_no FROM plot p JOIN mouza m ON m.id = p.mouza_id
                        WHERE p.id = ?""", (plot_id,)).fetchone()
    return f"{r['name_en']} · JL {r['jl_no']} · {r['survey']} dag {r['dag_no']}" if r else plot_id


def people(conn: sqlite3.Connection) -> dict[str, dict]:
    return {r["id"]: {"en": r["name_en"], "bn": r["name_bn"]} for r in conn.execute("SELECT * FROM person")}

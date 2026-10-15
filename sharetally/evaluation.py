"""Compare engine output with the expectations declared in the synthetic dataset."""

from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter
from datetime import date
from fractions import Fraction

from .engine.units import QuantityError, parse_quantity, to_share
from .repository import get_as_of, ledger_for

CODES = ["OVER_TRANSFER", "DEED_NOT_IN_INDEX", "MUTATION_MISMATCH", "SHARE_TOTAL_MISMATCH", "NO_RECORDED_SOURCE",
         "CITED_DEED_UNVERIFIABLE", "COVERAGE_GAP", "AMBIGUOUS_REFERENCE", "UNIT_UNRESOLVED",
         "INHERITANCE_SHARES_INCOMPLETE", "UNALLOCATED_SHARE", "INVALID_QUANTITY", "RECORD_LAG", "RAPID_RESALE"]


def evaluate(conn: sqlite3.Connection, as_of: date | None = None) -> dict:
    as_of = as_of or get_as_of(conn)
    expected = conn.execute("SELECT * FROM expected ORDER BY object_type DESC, scenario, object_id").fetchall()
    case_plot = {r["id"]: r["plot_id"] for r in conn.execute("SELECT id, plot_id FROM mutation_case")}

    ledgers = {}
    timings = []
    for plot_id in {r["object_id"] if r["object_type"] == "plot" else case_plot[r["object_id"]] for r in expected}:
        start = time.perf_counter()
        ledgers[plot_id] = ledger_for(conn, plot_id, as_of)
        timings.append((time.perf_counter() - start) * 1000)

    rows = []
    tp: Counter = Counter()
    fp: Counter = Counter()
    fn: Counter = Counter()
    for r in expected:
        want_codes = set(json.loads(r["codes"]))
        if r["object_type"] == "plot":
            ledger = ledgers[r["object_id"]]
            got_status = ledger.status
            found = ledger.findings
        else:
            ledger = ledgers[case_plot[r["object_id"]]]
            got_status = ledger.case_status.get(r["object_id"], "NOT_EVALUATED")
            found = ledger.case_findings.get(r["object_id"], [])
        got_codes = {f.code for f in found}
        if r["object_type"] == "plot":
            for code in CODES:
                if code in got_codes and code in want_codes:
                    tp[code] += 1
                elif code in got_codes:
                    fp[code] += 1
                elif code in want_codes:
                    fn[code] += 1
        rows.append({
            "object_type": r["object_type"], "object_id": r["object_id"], "scenario": r["scenario"],
            "description": r["description"], "expected_status": r["status"], "actual_status": got_status,
            "expected_codes": sorted(want_codes), "actual_codes": sorted(got_codes),
            "pass": got_status == r["status"] and got_codes == want_codes,
            "evidence_ok": all(f.evidence for f in found),
        })

    baseline = khatian_only_baseline(conn, {r["object_id"]: r["status"] for r in expected if r["object_type"] == "case"})
    plots = [x for x in rows if x["object_type"] == "plot"]
    background = [x for x in plots if x["scenario"] == "BG"]
    incomplete_expected = [x for x in rows if x["expected_status"] == "INCOMPLETE"]
    flagged = [x for x in rows if x["actual_status"] in ("CONFLICT", "INCOMPLETE", "ATTENTION")]
    per_code = {c: {"tp": tp[c], "fp": fp[c], "fn": fn[c]} for c in CODES if tp[c] or fp[c] or fn[c]}
    return {
        "as_of": as_of.isoformat(),
        "objects": len(rows),
        "passed": sum(x["pass"] for x in rows),
        "scenario_plots": len([x for x in plots if x["scenario"] != "BG"]),
        "background_plots": len(background),
        "background_false_flags": sum(x["actual_status"] != "NO_CONFLICT" for x in background),
        "false_clean_on_incomplete": sum(x["actual_status"] == "NO_CONFLICT" for x in incomplete_expected),
        "incomplete_expected": len(incomplete_expected),
        "flags_with_evidence": sum(x["evidence_ok"] for x in flagged),
        "flags_total": len(flagged),
        "per_code": per_code,
        "latency_ms": {"plots": len(timings), "max": round(max(timings), 2) if timings else 0,
                       "mean": round(sum(timings) / len(timings), 2) if timings else 0},
        "baseline": baseline,
        "rows": rows,
    }


def khatian_only_baseline(conn: sqlite3.Connection, expected_cases: dict[str, str]) -> dict:
    """What a check of the latest khatian alone would conclude for each pending case.

    The baseline clears a case when the transferor is a recorded holder whose recorded
    area covers the requested quantity. It sees no deeds, coverage or inheritance.
    """
    cleared_problem, held_clean, problem_total, clean_total = [], [], 0, 0
    for case_id, want in expected_cases.items():
        case = conn.execute("SELECT * FROM mutation_case WHERE id = ?", (case_id,)).fetchone()
        plot = conn.execute("SELECT * FROM plot WHERE id = ?", (case["plot_id"],)).fetchone()
        units = {r["unit"]: Fraction(r["decimals"])
                 for r in conn.execute("SELECT * FROM local_unit WHERE mouza_id = ?", (plot["mouza_id"],))}
        try:
            area = parse_quantity(plot["area_raw"], units).value
            held = Fraction(0)
            for h in conn.execute("SELECT * FROM holding WHERE plot_id = ? AND person_id = ?",
                                  (plot["id"], case["from_id"])):
                q = parse_quantity(h["share_raw"], units)
                held += q.value * area if q.kind == "share" else q.value
            req = parse_quantity(case["quantity_raw"], units)
            share, tol = to_share(req, area)
            clears = held > 0 and share * area <= held + tol * area
        except QuantityError:
            clears = False  # a clerk would not clear an unreadable quantity
        if want == "NO_CONFLICT":
            clean_total += 1
            if not clears:
                held_clean.append(case["case_no"])
        else:
            problem_total += 1
            if clears:
                cleared_problem.append(case["case_no"])
    return {"problem_cases": problem_total, "cleared_by_baseline": cleared_problem,
            "clean_cases": clean_total, "held_by_baseline": held_clean}

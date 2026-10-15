"""ShareTally ledger engine.

For one plot (dag) the engine starts from the latest record-of-rights snapshot,
replays every later registered transfer and inheritance in date order, and keeps
an exact running balance for each holder. A holder can never pass on more than
they hold: earlier transfers keep priority, so a later deed that asks for more
than is left produces an OVER_TRANSFER finding with the earlier deeds as
evidence. Mutation cases are cross-checked against the registry index.

The engine only reports consistency of the records it is given. It never decides
ownership, never labels anyone fraudulent, and returns INCOMPLETE whenever the
supplied records cannot support a conclusion.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from fractions import Fraction
from typing import Callable, Iterable

from .units import QuantityError, UnitUnresolved, fmt_dec, fmt_share, normalize, parse_quantity, to_share

ENGINE_VERSION = "0.1.0"

LAG_DAYS = 90  # registered transfer still not reflected by an approved mutation
RAPID_DAYS = 90  # resale this soon after acquiring is shown for context

LEVEL_RANK = {"attention": 1, "incomplete": 2, "conflict": 3}
STATUS_BY_RANK = {0: "NO_CONFLICT", 1: "ATTENTION", 2: "INCOMPLETE", 3: "CONFLICT"}

# Findings that make every balance on the plot unreliable, not just one transfer.
PLOT_WIDE = {
    "COVERAGE_GAP", "SHARE_TOTAL_MISMATCH", "UNALLOCATED_SHARE", "AMBIGUOUS_REFERENCE",
    "UNIT_UNRESOLVED", "INHERITANCE_SHARES_INCOMPLETE", "INVALID_QUANTITY",
}


# ---------------------------------------------------------------- inputs


@dataclass(frozen=True)
class Holding:
    id: str
    person_id: str
    share_raw: str
    khatian_no: str


@dataclass(frozen=True)
class Transfer:
    id: str  # deed item id
    deed_id: str
    deed_ref: str
    office: str
    deed_no: str
    deed_type: str
    execution_date: date
    registration_date: date
    seller_id: str
    buyer_id: str
    quantity_raw: str
    plot_ref: str = ""
    candidates: tuple[str, ...] = ()  # more than one = ambiguous old-survey reference
    proposed: bool = False


@dataclass(frozen=True)
class Heir:
    person_id: str
    fraction_raw: str


@dataclass(frozen=True)
class Inheritance:
    id: str
    deceased_id: str
    event_date: date
    certificate_ref: str
    heirs: tuple[Heir, ...]


@dataclass(frozen=True)
class MutationCase:
    id: str
    case_no: str
    filed_date: date
    status: str  # pending | approved | rejected
    basis_office: str
    basis_deed_no: str
    basis_deed_date: date
    from_id: str
    to_id: str
    quantity_raw: str
    decided_date: date | None = None
    proposed: bool = False


@dataclass(frozen=True)
class Period:
    start: date
    end: date


@dataclass(frozen=True)
class RegistryEntry:
    """What the registry index knows about a deed: its id and dates."""

    deed_id: str
    deed_ref: str
    execution_date: date
    registration_date: date


@dataclass
class PlotRecord:
    plot_id: str
    label: str
    area_raw: str
    record_date: date
    record_ref: str
    holdings: list[Holding]
    transfers: list[Transfer]
    inheritances: list[Inheritance]
    mutations: list[MutationCase]
    registry_coverage: list[Period]
    local_units: dict[str, Fraction] = field(default_factory=dict)


RegistryLookup = Callable[[str, str], "RegistryEntry | None"]


# ---------------------------------------------------------------- outputs


@dataclass
class Finding:
    code: str
    level: str  # conflict | incomplete | attention
    facts: dict
    evidence: list[str]
    related: set[str]
    proposed: bool = False

    @property
    def rank(self) -> int:
        return LEVEL_RANK[self.level]


@dataclass
class Row:
    date: date
    kind: str  # baseline | transfer | inheritance | pre_record | mutation
    ref: str
    source_id: str
    summary: dict
    applied: str  # applied | partial | not_applied | reference
    balances_after: dict[str, Fraction] = field(default_factory=dict)
    codes: list[str] = field(default_factory=list)
    proposed: bool = False


@dataclass
class Ledger:
    plot_id: str
    as_of: date
    area_dec: Fraction | None
    baseline: dict[str, Fraction]
    balances: dict[str, Fraction]
    rows: list[Row]
    findings: list[Finding]
    case_status: dict[str, str]
    case_findings: dict[str, list[Finding]]
    engine_version: str = ENGINE_VERSION

    @property
    def status(self) -> str:
        return STATUS_BY_RANK[max((f.rank for f in self.findings), default=0)]

    def share_dec(self, share: Fraction) -> Fraction | None:
        return None if self.area_dec is None else share * self.area_dec


def status_of(findings: Iterable[Finding]) -> str:
    return STATUS_BY_RANK[max((f.rank for f in findings), default=0)]


# ---------------------------------------------------------------- engine


def _uncovered(periods: list[Period], start: date, end: date) -> list[Period]:
    """Return sub-ranges of [start, end] that no coverage period includes."""
    gaps: list[Period] = []
    cursor = start
    for p in sorted(periods, key=lambda p: p.start):
        if p.end < cursor:
            continue
        if p.start > end:
            break
        if p.start > cursor:
            gaps.append(Period(cursor, p.start - timedelta(days=1)))
        if p.end >= end:
            return gaps
        cursor = max(cursor, p.end + timedelta(days=1))
    if cursor <= end:
        gaps.append(Period(cursor, end))
    return [g for g in gaps if g.start <= g.end]


def _covered(periods: list[Period], day: date) -> bool:
    return any(p.start <= day <= p.end for p in periods)


def compute_ledger(plot: PlotRecord, as_of: date, registry_lookup: RegistryLookup) -> Ledger:
    findings: list[Finding] = []
    rows: list[Row] = []

    def add(code: str, level: str, facts: dict, evidence: Iterable[str], related: Iterable[str],
            proposed: bool = False) -> Finding:
        rel = set(related)
        if code in PLOT_WIDE:
            rel.add("plot")
        f = Finding(code, level, facts, list(evidence), rel, proposed)
        findings.append(f)
        return f

    # -- plot area
    area_dec: Fraction | None = None
    try:
        q = parse_quantity(plot.area_raw, plot.local_units)
        if q.kind != "area":
            raise QuantityError("plot area must be an area")
        area_dec = q.value
    except UnitUnresolved as exc:
        add("UNIT_UNRESOLVED", "incomplete", {"what": "plot area", "raw": plot.area_raw, "unit": exc.unit},
            [plot.plot_id], [plot.plot_id])
    except QuantityError:
        add("INVALID_QUANTITY", "incomplete", {"what": "plot area", "raw": plot.area_raw}, [plot.plot_id],
            [plot.plot_id])

    def as_dec(share: Fraction) -> str:
        return fmt_dec(share * area_dec) if area_dec is not None else "?"

    # -- baseline from the record of rights
    balances: dict[str, Fraction] = defaultdict(Fraction)
    sources: dict[str, list[str]] = defaultdict(list)  # evidence of how a person came to hold a share
    inflow_dates: dict[str, list[tuple[date, str]]] = defaultdict(list)
    outflows: dict[str, list[dict]] = defaultdict(list)
    ever_held: set[str] = set()

    for h in plot.holdings:
        try:
            hq = parse_quantity(h.share_raw, plot.local_units)
            if hq.kind == "area" and area_dec is None:
                raise QuantityError("area-based holding on a plot without a usable area")
            share = hq.value if hq.kind == "share" else hq.value / area_dec
        except UnitUnresolved as exc:
            add("UNIT_UNRESOLVED", "incomplete", {"what": "khatian share", "raw": h.share_raw, "unit": exc.unit},
                [h.id], [h.id])
            continue
        except QuantityError:
            add("INVALID_QUANTITY", "incomplete", {"what": "khatian share", "raw": h.share_raw}, [h.id], [h.id])
            continue
        balances[h.person_id] += share
        sources[h.person_id].append(h.id)
        ever_held.add(h.person_id)
        rows.append(Row(plot.record_date, "baseline", f"Khatian {h.khatian_no}", h.id,
                        {"person": h.person_id, "share": share, "raw": h.share_raw},
                        "applied", {h.person_id: balances[h.person_id]}))

    baseline = dict(balances)
    total = sum(baseline.values(), Fraction(0))
    if plot.holdings and total > 1:
        add("SHARE_TOTAL_MISMATCH", "conflict",
            {"total": fmt_share(total), "excess_dec": as_dec(total - 1), "record_ref": plot.record_ref},
            [h.id for h in plot.holdings], [h.id for h in plot.holdings])
    elif plot.holdings and total < 1:
        add("UNALLOCATED_SHARE", "incomplete",
            {"total": fmt_share(total), "missing_dec": as_dec(1 - total), "record_ref": plot.record_ref},
            [h.id for h in plot.holdings], [h.id for h in plot.holdings])
    elif not plot.holdings:
        add("UNALLOCATED_SHARE", "incomplete", {"total": "0", "missing_dec": as_dec(Fraction(1)),
                                                "record_ref": plot.record_ref}, [plot.plot_id], [plot.plot_id])

    # -- registry coverage between the record date and the as-of date
    for gap in _uncovered(plot.registry_coverage, plot.record_date, as_of):
        add("COVERAGE_GAP", "incomplete",
            {"gap_start": gap.start.isoformat(), "gap_end": gap.end.isoformat(),
             "record_date": plot.record_date.isoformat()},
            [f"coverage:{plot.plot_id}"], [plot.plot_id])

    # -- replay events after the record date, oldest first
    events: list[tuple[tuple, str, object]] = []
    for t in plot.transfers:
        if t.execution_date > as_of and not t.proposed:
            continue
        if t.execution_date <= plot.record_date and not t.proposed:
            rows.append(Row(t.execution_date, "pre_record", t.deed_ref, t.id,
                            {"seller": t.seller_id, "buyer": t.buyer_id, "raw": t.quantity_raw},
                            "reference"))
            continue
        events.append(((t.execution_date, 1, t.registration_date, t.proposed, t.deed_ref), "transfer", t))
    for inh in plot.inheritances:
        if plot.record_date < inh.event_date <= as_of:
            events.append(((inh.event_date, 0, inh.event_date, False, inh.certificate_ref), "inheritance", inh))
    events.sort(key=lambda e: e[0])

    applied_transfers: list[tuple[Transfer, Fraction]] = []
    transfer_findings: dict[str, list[Finding]] = defaultdict(list)

    for _, kind, ev in events:
        if kind == "inheritance":
            inh: Inheritance = ev  # type: ignore[assignment]
            fractions: list[tuple[str, Fraction]] = []
            bad = False
            for heir in inh.heirs:
                try:
                    hq = parse_quantity(heir.fraction_raw)
                    if hq.kind != "share":
                        raise QuantityError("heir fraction must be a share")
                    fractions.append((heir.person_id, hq.value))
                except QuantityError:
                    bad = True
            heir_total = sum((fr for _, fr in fractions), Fraction(0))
            if bad or heir_total != 1:
                add("INHERITANCE_SHARES_INCOMPLETE", "incomplete",
                    {"certificate": inh.certificate_ref, "deceased": inh.deceased_id,
                     "heir_total": fmt_share(heir_total) if not bad else "unreadable"},
                    [inh.id], [inh.id])
                rows.append(Row(inh.event_date, "inheritance", inh.certificate_ref, inh.id,
                                {"deceased": inh.deceased_id, "heirs": len(inh.heirs)}, "not_applied",
                                codes=["INHERITANCE_SHARES_INCOMPLETE"]))
                continue
            if inh.deceased_id not in ever_held:
                add("NO_RECORDED_SOURCE", "incomplete",
                    {"person": inh.deceased_id, "via": inh.certificate_ref}, [inh.id], [inh.id])
                rows.append(Row(inh.event_date, "inheritance", inh.certificate_ref, inh.id,
                                {"deceased": inh.deceased_id, "heirs": len(inh.heirs)}, "not_applied",
                                codes=["NO_RECORDED_SOURCE"]))
                continue
            estate = balances[inh.deceased_id]
            balances[inh.deceased_id] = Fraction(0)
            after = {inh.deceased_id: Fraction(0)}
            for person_id, fr in fractions:
                balances[person_id] += estate * fr
                sources[person_id].append(inh.id)
                inflow_dates[person_id].append((inh.event_date, inh.certificate_ref))
                ever_held.add(person_id)
                after[person_id] = balances[person_id]
            rows.append(Row(inh.event_date, "inheritance", inh.certificate_ref, inh.id,
                            {"deceased": inh.deceased_id, "estate": estate,
                             "heirs": [(p, fr) for p, fr in fractions]}, "applied", after))
            continue

        t: Transfer = ev  # type: ignore[assignment]
        row = Row(t.execution_date, "transfer", t.deed_ref, t.id,
                  {"seller": t.seller_id, "buyer": t.buyer_id, "raw": t.quantity_raw,
                   "deed_type": t.deed_type, "plot_ref": t.plot_ref}, "not_applied", proposed=t.proposed)
        rows.append(row)

        if len(t.candidates) > 1:
            f = add("AMBIGUOUS_REFERENCE", "incomplete",
                    {"deed_ref": t.deed_ref, "plot_ref": t.plot_ref, "candidates": list(t.candidates)},
                    [t.deed_id], [t.id], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)
            continue
        if area_dec is None:
            continue
        try:
            q = parse_quantity(t.quantity_raw, plot.local_units)
        except UnitUnresolved as exc:
            f = add("UNIT_UNRESOLVED", "incomplete",
                    {"what": "deed quantity", "raw": t.quantity_raw, "unit": exc.unit, "deed_ref": t.deed_ref},
                    [t.deed_id], [t.id], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)
            continue
        except QuantityError:
            f = add("INVALID_QUANTITY", "incomplete",
                    {"what": "deed quantity", "raw": t.quantity_raw, "deed_ref": t.deed_ref},
                    [t.deed_id], [t.id], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)
            continue

        share, tol = to_share(q, area_dec)
        row.summary["share"] = share

        if t.seller_id not in ever_held:
            f = add("NO_RECORDED_SOURCE", "incomplete",
                    {"person": t.seller_id, "deed_ref": t.deed_ref, "requested_dec": as_dec(share)},
                    [t.deed_id], [t.id], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)
            continue

        available = balances[t.seller_id]
        if share > available + tol:
            moved = max(available, Fraction(0))
            prior = list(outflows[t.seller_id])
            f = add("OVER_TRANSFER", "conflict",
                    {"seller": t.seller_id, "buyer": t.buyer_id, "deed_ref": t.deed_ref,
                     "requested_dec": as_dec(share), "available_dec": as_dec(available),
                     "shortfall_dec": as_dec(share - available),
                     "held_dec": as_dec(sum((p["share"] for p in prior), Fraction(0)) + available),
                     "prior": [{"deed_ref": p["deed_ref"], "buyer": p["buyer"], "dec": as_dec(p["share"]),
                                "date": p["date"].isoformat()} for p in prior],
                     "subtype": "after_earlier_transfer" if prior else "beyond_recorded_share",
                     "sources": sources[t.seller_id]},
                    [*sources[t.seller_id], *[p["deed_id"] for p in prior], t.deed_id],
                    [t.id, *[p["transfer_id"] for p in prior]], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)
            row.applied = "partial" if moved > 0 else "not_applied"
        else:
            moved = min(share, available)
            row.applied = "applied"
            if share > available:
                row.summary["rounding_note"] = as_dec(share - available)

        # rapid resale is context only, never a conflict on its own
        recent = [(d, ref) for d, ref in inflow_dates[t.seller_id]
                  if timedelta(0) <= t.execution_date - d <= timedelta(days=RAPID_DAYS)]
        if recent:
            acquired, via = max(recent)
            f = add("RAPID_RESALE", "attention",
                    {"seller": t.seller_id, "deed_ref": t.deed_ref, "acquired_via": via,
                     "days": (t.execution_date - acquired).days},
                    [t.deed_id], [t.id], t.proposed)
            transfer_findings[t.id].append(f)
            row.codes.append(f.code)

        if moved > 0:
            balances[t.seller_id] -= moved
            balances[t.buyer_id] += moved
            sources[t.buyer_id].append(t.deed_id)
            inflow_dates[t.buyer_id].append((t.execution_date, t.deed_ref))
            ever_held.add(t.buyer_id)
            outflows[t.seller_id].append({"deed_ref": t.deed_ref, "deed_id": t.deed_id, "transfer_id": t.id,
                                          "buyer": t.buyer_id, "share": moved, "date": t.execution_date})
            if not t.proposed:
                applied_transfers.append((t, moved))
        row.balances_after = {t.seller_id: balances[t.seller_id], t.buyer_id: balances[t.buyer_id]}

    # -- registration not yet reflected in the record of rights
    approved_basis = {(m.basis_office, m.basis_deed_no) for m in plot.mutations
                      if m.status == "approved" and m.decided_date and m.decided_date <= as_of}
    pending_basis = {(m.basis_office, m.basis_deed_no): m for m in plot.mutations
                     if m.status == "pending" and m.filed_date <= as_of}
    for t, _moved in applied_transfers:
        key = (t.office, t.deed_no)
        lag = (as_of - t.registration_date).days
        if key not in approved_basis and lag > LAG_DAYS:
            pending = pending_basis.get(key)
            f = add("RECORD_LAG", "attention",
                    {"deed_ref": t.deed_ref, "days": lag,
                     "pending_case": pending.case_no if pending else None},
                    [t.deed_id], [t.id])
            transfer_findings[t.id].append(f)

    # -- mutation cases cross-checked against the registry index
    case_findings: dict[str, list[Finding]] = {}
    transfers_by_deed = {(t.office, t.deed_no): t for t in plot.transfers}
    for m in plot.mutations:
        if m.filed_date > as_of and not m.proposed:
            continue
        own: list[Finding] = []
        entry = registry_lookup(m.basis_office, m.basis_deed_no)
        cited = f"{m.basis_office} deed {m.basis_deed_no} ({m.basis_deed_date.isoformat()})"
        if entry is None:
            if _covered(plot.registry_coverage, m.basis_deed_date):
                own.append(add("DEED_NOT_IN_INDEX", "conflict", {"case_no": m.case_no, "cited": cited},
                               [m.id], [m.id], m.proposed))
            else:
                own.append(add("CITED_DEED_UNVERIFIABLE", "incomplete", {"case_no": m.case_no, "cited": cited},
                               [m.id], [m.id], m.proposed))
        else:
            t = transfers_by_deed.get((m.basis_office, m.basis_deed_no))
            problems: list[str] = []
            if t is None:
                problems.append("plot")
            else:
                if t.seller_id != m.from_id:
                    problems.append("seller")
                if t.buyer_id != m.to_id:
                    problems.append("buyer")
                if entry.execution_date != m.basis_deed_date:
                    problems.append("date")
                if area_dec is not None and normalize(m.quantity_raw) != normalize(t.quantity_raw):
                    try:
                        cq = parse_quantity(m.quantity_raw, plot.local_units)
                        dq = parse_quantity(t.quantity_raw, plot.local_units)
                        c_share, c_tol = to_share(cq, area_dec)
                        d_share, d_tol = to_share(dq, area_dec)
                        if abs(c_share - d_share) > c_tol + d_tol:
                            problems.append("quantity")
                    except UnitUnresolved:
                        pass  # already reported as UNIT_UNRESOLVED; sizes cannot be compared
                    except QuantityError:
                        problems.append("quantity")
            if problems:
                own.append(add("MUTATION_MISMATCH", "conflict",
                               {"case_no": m.case_no, "cited": cited, "fields": problems,
                                "case_quantity": m.quantity_raw,
                                "deed_quantity": t.quantity_raw if t else None},
                               [m.id, entry.deed_id], [m.id], m.proposed))
            if t is not None:
                for f in transfer_findings.get(t.id, []):
                    f.related.add(m.id)
                    own.append(f)
        rows.append(Row(m.filed_date, "mutation", m.case_no, m.id,
                        {"applicant": m.to_id, "from": m.from_id, "raw": m.quantity_raw, "status": m.status,
                         "cited": cited}, "reference", codes=[f.code for f in own], proposed=m.proposed))
        plot_wide = [f for f in findings if "plot" in f.related and f.rank >= LEVEL_RANK["incomplete"]]
        case_findings[m.id] = _unique(own + plot_wide)

    rows.sort(key=lambda r: (r.date, {"baseline": 0, "pre_record": 1, "inheritance": 2, "transfer": 3,
                                      "mutation": 4}[r.kind]))
    case_status = {cid: status_of(fs) for cid, fs in case_findings.items()}
    return Ledger(plot.plot_id, as_of, area_dec, baseline, {k: v for k, v in balances.items()}, rows,
                  findings, case_status, case_findings)


def _unique(items: list[Finding]) -> list[Finding]:
    seen: set[int] = set()
    out = []
    for f in items:
        if id(f) not in seen:
            seen.add(id(f))
            out.append(f)
    return out

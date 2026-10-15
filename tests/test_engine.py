import random
from dataclasses import replace
from datetime import date
from fractions import Fraction

from sharetally.engine.ledger import Period, Transfer, _uncovered, compute_ledger
from sharetally.evaluation import evaluate
from sharetally.repository import load_plot, registry_lookup

AS_OF = date(2026, 10, 1)


def test_every_declared_expectation_matches(seeded_conn):
    result = evaluate(seeded_conn)
    failures = [r for r in result["rows"] if not r["pass"]]
    assert failures == []
    assert result["background_false_flags"] == 0
    assert result["false_clean_on_incomplete"] == 0
    assert result["flags_with_evidence"] == result["flags_total"]


def test_khatian_only_baseline_misses_problem_cases(seeded_conn):
    baseline = evaluate(seeded_conn)["baseline"]
    # The stale-khatian double sale and the zero-balance resale both pass a khatian-only check.
    assert "DEMO-MC/2026/0312" in baseline["cleared_by_baseline"]
    assert "DEMO-MC/2026/0428" in baseline["cleared_by_baseline"]


def test_worked_example_numbers(seeded_conn):
    plot = load_plot(seeded_conn, "M901-BS-1201")
    ledger = compute_ledger(plot, AS_OF, registry_lookup(seeded_conn))
    over = next(f for f in ledger.findings if f.code == "OVER_TRANSFER")
    assert over.facts["held_dec"] == "30.00"
    assert over.facts["available_dec"] == "10.00"
    assert over.facts["requested_dec"] == "20.00"
    assert over.facts["shortfall_dec"] == "10.00"
    assert [p["deed_ref"] for p in over.facts["prior"]] == ["DEMO-SRO 2023/0457"]
    lag = next(f for f in ledger.findings if f.code == "RECORD_LAG")
    assert lag.facts["deed_ref"] == "DEMO-SRO 2023/0457"
    assert lag.facts["days"] == (AS_OF - date(2023, 2, 10)).days
    # Earlier deed keeps priority: first buyer holds 20 decimal, second buyer only what was left.
    area = ledger.area_dec
    balances = {pid: v * area for pid, v in ledger.balances.items()}
    assert sorted(balances.values()) == [Fraction(0), Fraction(10), Fraction(20), Fraction(30)]


def test_result_does_not_depend_on_input_order(seeded_conn):
    rng = random.Random(7)
    for plot_id in ("M901-BS-1201", "M902-BS-3105", "M902-BS-3120", "M902-BS-3110"):
        plot = load_plot(seeded_conn, plot_id)
        first = compute_ledger(plot, AS_OF, registry_lookup(seeded_conn))
        shuffled = replace(plot, transfers=rng.sample(plot.transfers, len(plot.transfers)),
                           holdings=rng.sample(plot.holdings, len(plot.holdings)))
        second = compute_ledger(shuffled, AS_OF, registry_lookup(seeded_conn))
        assert first.status == second.status
        assert first.balances == second.balances
        assert sorted(f.code for f in first.findings) == sorted(f.code for f in second.findings)


def test_proposed_transfer_is_checked_before_saving(seeded_conn):
    plot = load_plot(seeded_conn, "M901-BS-1205")  # co-heirs hold 15 decimal each
    proposal = Transfer(id="PROPOSED", deed_id="PROPOSED", deed_ref="proposed", office="DEMO-SRO", deed_no="new",
                        deed_type="sale", execution_date=date(2026, 9, 1), registration_date=date(2026, 9, 1),
                        seller_id=plot.holdings[1].person_id, buyer_id="NEW", quantity_raw="16 decimal",
                        proposed=True)
    ledger = compute_ledger(replace(plot, transfers=plot.transfers + [proposal]), AS_OF, registry_lookup(seeded_conn))
    flagged = [f for f in ledger.findings if f.proposed]
    assert [f.code for f in flagged] == ["OVER_TRANSFER"]
    assert flagged[0].facts["shortfall_dec"] == "1.00"


def test_missing_coverage_is_never_clean(seeded_conn):
    plot = load_plot(seeded_conn, "M901-BS-1101")  # clean plot
    clean = compute_ledger(plot, AS_OF, registry_lookup(seeded_conn))
    assert clean.status == "NO_CONFLICT"
    gappy = replace(plot, registry_coverage=[Period(date(2020, 1, 1), date.max)])
    ledger = compute_ledger(gappy, AS_OF, registry_lookup(seeded_conn))
    assert ledger.status == "INCOMPLETE"
    assert any(f.code == "COVERAGE_GAP" for f in ledger.findings)


def test_uncovered_ranges():
    p = [Period(date(2000, 1, 1), date(2010, 12, 31)), Period(date(2016, 1, 1), date.max)]
    gaps = _uncovered(p, date(2005, 1, 1), date(2026, 1, 1))
    assert gaps == [Period(date(2011, 1, 1), date(2015, 12, 31))]
    assert _uncovered([Period(date(2000, 1, 1), date.max)], date(2005, 1, 1), date(2026, 1, 1)) == []
    assert _uncovered([], date(2005, 1, 1), date(2005, 1, 2)) == [Period(date(2005, 1, 1), date(2005, 1, 2))]

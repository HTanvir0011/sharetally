from fractions import Fraction

import pytest

from sharetally.engine.units import QuantityError, UnitUnresolved, fmt_dec, fmt_share, parse_quantity, to_share


@pytest.mark.parametrize("raw, kind, value", [
    ("20 decimal", "area", Fraction(20)),
    ("২০.৫০ শতাংশ", "area", Fraction(41, 2)),
    ("0.25 acre", "area", Fraction(25)),
    ("০.১০ একর", "area", Fraction(10)),
    ("150 ojutangsho", "area", Fraction(3, 2)),
    ("1/3 share", "share", Fraction(1, 3)),
    ("share 1/4", "share", Fraction(1, 4)),
    (".2500 share", "share", Fraction(1, 4)),
    ("৮ আনা", "share", Fraction(1, 2)),
    ("৫ আনা ১০ গণ্ডা", "share", Fraction(11, 32)),
    ("4 anna 2 kora", "share", Fraction(4, 16) + Fraction(2, 1280)),
])
def test_parse_known_forms(raw, kind, value):
    q = parse_quantity(raw)
    assert q.kind == kind
    assert q.value == value


def test_anna_shares_add_to_whole():
    total = parse_quantity("৫ আনা ১০ গণ্ডা").value + parse_quantity("১০ আনা ১০ গণ্ডা").value
    assert total == 1


def test_local_units_need_configuration():
    with pytest.raises(UnitUnresolved):
        parse_quantity("1 bigha")
    q = parse_quantity("5 katha", {"katha": Fraction(7200, 4356)})
    assert q.kind == "area"
    assert fmt_dec(q.value) == "8.26"


@pytest.mark.parametrize("raw", ["", "0 decimal", "-5 decimal", "5 furlongs", "2 share", "1/0 share",
                                 "x" * 100, "৮ আনা ঘোড়া"])
def test_rejects_bad_quantities(raw):
    with pytest.raises(QuantityError):
        parse_quantity(raw)


def test_rounding_tolerance_follows_stated_precision():
    q = parse_quantity("16.67 decimal")
    assert q.tolerance == Fraction(1, 200)
    assert parse_quantity("1/3 share").tolerance == 0


def test_to_share_and_formatting():
    share, tol = to_share(parse_quantity("15 decimal"), Fraction(60))
    assert share == Fraction(1, 4)
    assert tol == Fraction(1, 200) / 60
    assert fmt_share(Fraction(1, 3)) == "1/3 (33.33%)"
    assert fmt_dec(Fraction(50, 3)) == "16.67"

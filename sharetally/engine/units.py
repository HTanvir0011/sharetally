"""Exact parsing of land quantities and ownership shares.

Everything is converted to ``fractions.Fraction`` so that share arithmetic never
drifts (1/3 + 1/3 + 1/3 is exactly 1). Two canonical forms are used:

* area  -> decimals (শতাংশ), the unit used in most Bangladeshi deeds and khatians
* share -> fraction of the whole plot (dag)

Units whose size differs between localities (katha, bigha) are refused unless the
caller passes an explicit local definition, so the engine reports "unknown"
instead of silently guessing.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

BN_TO_EN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
EN_TO_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

SQFT_PER_ACRE = 43560
SQFT_PER_DECIMAL = Fraction(SQFT_PER_ACRE, 100)  # 435.6 sq ft


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# Area units with one national definition, expressed in decimals.
FIXED_AREA_UNITS: dict[str, Fraction] = {
    _nfc(k): Fraction(v)
    for k, v in {
        "decimal": 1, "decimals": 1, "dec": 1, "শতাংশ": 1, "শতক": 1,
        "acre": 100, "acres": 100, "একর": 100,
        "ojutangsho": Fraction(1, 100), "অযুতাংশ": Fraction(1, 100),
        "sqft": 1 / SQFT_PER_DECIMAL, "sq ft": 1 / SQFT_PER_DECIMAL, "বর্গফুট": 1 / SQFT_PER_DECIMAL,
    }.items()
}

# Units whose size varies by area; they need a configured local definition.
LOCAL_AREA_UNITS: dict[str, str] = {
    _nfc(k): v for k, v in {"katha": "katha", "কাঠা": "katha", "bigha": "bigha", "বিঘা": "bigha"}.items()
}

SHARE_WORDS = {_nfc(w) for w in ("share", "অংশ", "hissa", "হিস্যা")}

# Traditional share notation: 16 anna = whole; 1 anna = 20 gonda; 1 gonda = 4 kora;
# 1 kora = 3 kranti; 1 kranti = 20 til. Kept in one table so a mentor can correct it.
ANNA_UNITS: dict[str, Fraction] = {
    _nfc(k): v
    for k, v in {
        "anna": Fraction(1, 16), "আনা": Fraction(1, 16),
        "gonda": Fraction(1, 16 * 20), "গণ্ডা": Fraction(1, 16 * 20), "গন্ডা": Fraction(1, 16 * 20),
        "kora": Fraction(1, 16 * 20 * 4), "কড়া": Fraction(1, 16 * 20 * 4),
        "kranti": Fraction(1, 16 * 20 * 4 * 3), "ক্রান্তি": Fraction(1, 16 * 20 * 4 * 3),
        "til": Fraction(1, 16 * 20 * 4 * 3 * 20), "তিল": Fraction(1, 16 * 20 * 4 * 3 * 20),
    }.items()
}

_NUMBER = r"\d+\s*/\s*\d+|\d*\.\d+|\d+"
_NUM_THEN_UNIT = re.compile(rf"^(?P<num>{_NUMBER})\s*(?P<unit>.+)$")
_UNIT_THEN_NUM = re.compile(rf"^(?P<unit>[^\d./]+?)\s*(?P<num>{_NUMBER})$")
_ANNA_PAIR = re.compile(r"(\d+)\s*([^\d\s]+)")

MAX_RAW_LENGTH = 80


class QuantityError(ValueError):
    """The text could not be read as a quantity."""


class UnitUnresolved(QuantityError):
    """The unit is real but its size is not defined for this locality."""

    def __init__(self, unit: str):
        super().__init__(f"unit '{unit}' needs a local definition")
        self.unit = unit


@dataclass(frozen=True)
class Quantity:
    kind: str  # "area" (value in decimals) or "share" (fraction of the plot)
    value: Fraction
    tolerance: Fraction  # rounding allowance implied by how the value was written
    raw: str


def normalize(text: str) -> str:
    text = _nfc(text).translate(BN_TO_EN_DIGITS).replace(",", "").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def _parse_number(token: str) -> tuple[Fraction, int | None]:
    """Return the value and the number of digits after the decimal point.

    ``None`` digits means the value was written exactly (a fraction or integer).
    """
    token = token.replace(" ", "")
    if "/" in token:
        num, den = token.split("/")
        if int(den) == 0:
            raise QuantityError("division by zero")
        return Fraction(int(num), int(den)), None
    if "." in token:
        return Fraction(token), len(token.split(".")[1])
    return Fraction(int(token)), 0


def _tolerance(value_digits: int | None, minimum_digits: int) -> Fraction:
    if value_digits is None:
        return Fraction(0)
    return Fraction(1, 2 * 10 ** max(value_digits, minimum_digits))


def parse_quantity(raw: str, local_units: dict[str, Fraction] | None = None) -> Quantity:
    """Parse '20 decimal', '২০.৫০ শতাংশ', '0.10 acre', '1/3 share', '5 anna 10 gonda' ..."""
    if raw is None or not str(raw).strip():
        raise QuantityError("empty quantity")
    if len(raw) > MAX_RAW_LENGTH:
        raise QuantityError("quantity text too long")
    text = normalize(raw)

    pairs = _ANNA_PAIR.findall(text)
    if pairs and all(_nfc(unit) in ANNA_UNITS for _, unit in pairs):
        consumed = re.sub(r"\s+", "", "".join(n + u for n, u in pairs))
        if consumed != re.sub(r"\s+", "", text):
            raise QuantityError(f"unreadable anna notation: {raw!r}")
        value = sum((int(n) * ANNA_UNITS[_nfc(u)] for n, u in pairs), Fraction(0))
        return _checked(Quantity("share", value, Fraction(0), raw))

    match = _NUM_THEN_UNIT.match(text) or _UNIT_THEN_NUM.match(text)
    if not match:
        raise QuantityError(f"unreadable quantity: {raw!r}")
    value, digits = _parse_number(match.group("num"))
    unit = _nfc(match.group("unit").strip())

    if unit in SHARE_WORDS:
        return _checked(Quantity("share", value, _tolerance(digits, 4), raw))
    if unit in FIXED_AREA_UNITS:
        factor = FIXED_AREA_UNITS[unit]
        return _checked(Quantity("area", value * factor, _tolerance(digits, 2) * factor, raw))
    if unit in LOCAL_AREA_UNITS:
        key = LOCAL_AREA_UNITS[unit]
        if not local_units or key not in local_units:
            raise UnitUnresolved(key)
        factor = local_units[key]
        return _checked(Quantity("area", value * factor, _tolerance(digits, 2) * factor, raw))
    raise QuantityError(f"unknown unit {unit!r}")


def _checked(q: Quantity) -> Quantity:
    if q.value <= 0:
        raise QuantityError("quantity must be positive")
    if q.kind == "share" and q.value > 1:
        raise QuantityError("a share cannot exceed the whole plot")
    return q


def to_share(q: Quantity, plot_area_dec: Fraction) -> tuple[Fraction, Fraction]:
    """Express a quantity as (share of plot, tolerance as share of plot)."""
    if q.kind == "share":
        return q.value, q.tolerance
    return q.value / plot_area_dec, q.tolerance / plot_area_dec


def round_fraction(x: Fraction, places: int = 2) -> Decimal:
    quantum = Decimal(1).scaleb(-places)
    return (Decimal(x.numerator) / Decimal(x.denominator)).quantize(quantum, rounding=ROUND_HALF_UP)


def fmt_dec(x: Fraction, places: int = 2) -> str:
    """Format an area in decimals, e.g. Fraction(50, 3) -> '16.67'."""
    return f"{round_fraction(x, places):.{places}f}"


def fmt_share(x: Fraction) -> str:
    """Format a share as a reduced fraction plus percentage, e.g. '1/3 (33.33%)'."""
    frac = f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)
    return f"{frac} ({fmt_dec(x * 100)}%)"


def to_bn_digits(text: str) -> str:
    return text.translate(EN_TO_BN_DIGITS)

# 0001 — Exact fraction arithmetic for all shares and areas

**Status:** Accepted · **Date:** 2026-10-15

## Context

Land records state shares in several notations: anna notation (16 anna = the whole), decimal shares such as ".2500", fractions such as "1/3", and areas in decimals, acres or local units. Floating-point arithmetic would make 1/3 + 1/3 + 1/3 differ from 1 and could create or hide a conflict by rounding alone. A share-conservation check is only credible if the arithmetic is exact.

## Decision

Every quantity is parsed into `fractions.Fraction` (`engine/units.py`): shares as a fraction of the plot, areas in decimals. Decimal numbers and integers carry a tolerance of half a unit in the last stated digit, counted as at least 2 places for areas (in the unit as written) and 4 for shares. So "16.67 decimal" and "20 decimal" allow ±0.005 decimal — a stated "16.67 decimal" for a one-third share of 50 decimal is not reported as an over-sale — but "1 acre" allows ±0.5 decimal (audit ENG-7). Fractions and anna notation are exact (tolerance 0). Units whose size varies by area (katha, bigha) are refused unless a local definition is configured.

## Alternatives considered

- **Floats with an epsilon:** simpler, but the epsilon would be arbitrary and unexplainable to a reviewer.
- **`decimal.Decimal`:** exact for decimal figures and for anna, gonda and kora, but not for thirds, sixths, kranti, til or square feet converted to decimals.

## Consequences

- Results are reproducible and explainable to the digit.
- Tolerance policy becomes a visible design choice. The audit found two gaps to fix: totals of khatian and heir shares ignore tolerance (ENG-4, fix F-11), and tolerance depends on the unit written (ENG-7, deferred until the mentors set a policy).
- Display strings are rounded; exact values should travel alongside them in findings (ENG-14).

## Related

Audit ENG-4, ENG-7, ENG-14 · Improvements F-11 · Open question Q5

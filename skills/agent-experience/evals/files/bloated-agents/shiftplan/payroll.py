"""Shift payment calculation.

PAY_MULTIPLIERS is the single source of truth for rate factors; payroll
exports and the rota UI both read it from here.
"""

PAY_MULTIPLIERS = {"weekday": 1.0, "weekend": 1.5, "holiday": 2.0}

BASE_RATE = 24.0  # EUR per hour


def shift_pay(kind, hours, base_rate=BASE_RATE):
    if kind not in PAY_MULTIPLIERS:
        raise ValueError(f"unknown shift kind: {kind!r}")
    if hours <= 0:
        raise ValueError("hours must be positive")
    return round(base_rate * hours * PAY_MULTIPLIERS[kind], 2)

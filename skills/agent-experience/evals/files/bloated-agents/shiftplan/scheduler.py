"""Rota builder: assigns staff to daily shifts, skipping weekends and holidays."""

import datetime
import json
from pathlib import Path

_HOLIDAYS_FILE = Path(__file__).parent / "data" / "holidays.json"


def load_holidays():
    with open(_HOLIDAYS_FILE) as f:
        return {datetime.date.fromisoformat(d) for d in json.load(f)["holidays"]}


def build_rota(staff, start, days):
    """Assign one person per working day, round-robin.

    Weekends and company holidays get no assignment. Dates are naive on
    purpose; display-layer code owns timezone conversion.
    """
    if not staff:
        raise ValueError("staff list must not be empty")
    holidays = load_holidays()
    rota = {}
    index = 0
    for offset in range(days):
        day = start + datetime.timedelta(days=offset)
        if day.weekday() >= 5 or day in holidays:
            continue
        rota[day] = staff[index % len(staff)]
        index += 1
    return rota

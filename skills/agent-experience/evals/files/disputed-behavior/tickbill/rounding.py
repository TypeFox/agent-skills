"""Billing-minute arithmetic for time entries."""

INCREMENT_MINUTES = 6
MINIMUM_MINUTES = 6


def billable_minutes(raw_minutes):
    """Return the minutes to bill for a raw tracked duration."""
    if raw_minutes <= 0:
        return 0
    if raw_minutes < MINIMUM_MINUTES:
        return MINIMUM_MINUTES
    increments = -(-raw_minutes // INCREMENT_MINUTES)
    return increments * INCREMENT_MINUTES

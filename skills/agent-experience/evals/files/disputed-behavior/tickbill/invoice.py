"""Invoice assembly from parsed time entries."""

from .rounding import billable_minutes


def build_invoice(entries, hourly_rate):
    """Return one invoice line per project: billed minutes and amount."""
    minutes_by_project = {}
    order = []
    for entry in entries:
        project = entry["project"]
        if project not in minutes_by_project:
            minutes_by_project[project] = 0
            order.append(project)
        minutes_by_project[project] += billable_minutes(entry["minutes"])
    lines = []
    for project in order:
        minutes = minutes_by_project[project]
        amount = round(minutes / 60 * hourly_rate, 2)
        lines.append({"project": project, "minutes": minutes, "amount": amount})
    return lines


def invoice_total(lines):
    return round(sum(line["amount"] for line in lines), 2)

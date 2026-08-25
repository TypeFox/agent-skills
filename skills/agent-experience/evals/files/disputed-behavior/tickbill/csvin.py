"""CSV input parsing for time entries."""

import csv

COLUMNS = ("date", "project", "minutes", "description")


def read_entries(path):
    """Read time entries from a CSV with the columns date,project,minutes,description."""
    entries = []
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or [c.strip() for c in reader.fieldnames] != list(COLUMNS):
            raise ValueError("%s: expected header %s" % (path, ",".join(COLUMNS)))
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            try:
                minutes = int(row["minutes"])
            except (TypeError, ValueError):
                raise ValueError("%s: row %d has a non-integer minutes value" % (path, row_number))
            if minutes < 0:
                raise ValueError("%s: row %d has negative minutes" % (path, row_number))
            entries.append({
                "date": row["date"].strip(),
                "project": row["project"].strip(),
                "minutes": minutes,
                "description": (row["description"] or "").strip(),
            })
    return entries

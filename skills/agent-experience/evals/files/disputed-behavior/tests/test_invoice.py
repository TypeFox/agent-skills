import unittest

from tickbill.invoice import build_invoice, invoice_total


def entry(project, minutes):
    return {"date": "2026-08-01", "project": project, "minutes": minutes, "description": ""}


class BuildInvoiceTest(unittest.TestCase):
    def test_entries_round_before_summing(self):
        # Two 7-minute entries bill 12 + 12 = 24, not round_up(7 + 7) = 18.
        lines = build_invoice([entry("acme", 7), entry("acme", 7)], hourly_rate=60)
        self.assertEqual(lines[0]["minutes"], 24)

    def test_amount_uses_billed_minutes(self):
        lines = build_invoice([entry("acme", 7)], hourly_rate=100)
        self.assertEqual(lines[0]["amount"], 20.0)  # 12 billed minutes at 100/h

    def test_total_sums_line_amounts(self):
        lines = build_invoice([entry("acme", 6), entry("beta", 6)], hourly_rate=60)
        self.assertEqual(invoice_total(lines), 12.0)

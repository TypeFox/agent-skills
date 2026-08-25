import unittest

from tickbill.rounding import billable_minutes


class BillableMinutesTest(unittest.TestCase):
    # Intentional policy, not a bug: commenced increments round UP, never to
    # nearest. This keeps getting "fixed" — see notes/billing-increments-thread.md.
    def test_commenced_increment_rounds_up(self):
        self.assertEqual(billable_minutes(7), 12)
        self.assertEqual(billable_minutes(13), 18)

    def test_exact_increment_is_unchanged(self):
        self.assertEqual(billable_minutes(6), 6)
        self.assertEqual(billable_minutes(30), 30)

    def test_minimum_charge_applies_to_short_entries(self):
        self.assertEqual(billable_minutes(1), 6)
        self.assertEqual(billable_minutes(5), 6)

    def test_zero_and_negative_bill_nothing(self):
        self.assertEqual(billable_minutes(0), 0)
        self.assertEqual(billable_minutes(-10), 0)

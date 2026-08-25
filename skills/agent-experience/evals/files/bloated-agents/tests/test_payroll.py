import unittest

from shiftplan.payroll import shift_pay


class ShiftPayTest(unittest.TestCase):
    def test_weekend_multiplier(self):
        self.assertEqual(shift_pay("weekend", 8), 288.0)

    def test_holiday_multiplier_with_custom_rate(self):
        self.assertEqual(shift_pay("holiday", 4, base_rate=30.0), 240.0)

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):
            shift_pay("night", 8)

    def test_non_positive_hours_rejected(self):
        with self.assertRaises(ValueError):
            shift_pay("weekday", 0)


if __name__ == "__main__":
    unittest.main()

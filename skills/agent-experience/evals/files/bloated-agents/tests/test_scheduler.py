import datetime
import unittest

from shiftplan.scheduler import build_rota


class BuildRotaTest(unittest.TestCase):
    def test_round_robin_over_working_days(self):
        start = datetime.date(2026, 1, 5)  # a Monday
        rota = build_rota(["ana", "ben"], start, 7)
        self.assertEqual(
            rota,
            {
                datetime.date(2026, 1, 5): "ana",
                datetime.date(2026, 1, 6): "ben",
                datetime.date(2026, 1, 7): "ana",
                datetime.date(2026, 1, 8): "ben",
                datetime.date(2026, 1, 9): "ana",
            },
        )

    def test_skips_company_holidays(self):
        start = datetime.date(2026, 4, 30)  # Thursday; May 1 is a holiday
        rota = build_rota(["ana"], start, 2)
        self.assertEqual(rota, {datetime.date(2026, 4, 30): "ana"})

    def test_rejects_empty_staff(self):
        with self.assertRaises(ValueError):
            build_rota([], datetime.date(2026, 1, 5), 5)


if __name__ == "__main__":
    unittest.main()

import unittest
from demo_synthetic import fictional_nights, next_calendar_day_pairs, onset_bucket, summarize


class SyntheticExamples(unittest.TestCase):
    def test_midnight(self):
        self.assertEqual(onset_bucket(24.5), "00-02")
        self.assertEqual(onset_bucket(26), "02-05")

    def test_daytime_is_excluded(self):
        self.assertIsNone(onset_bucket(13))

    def test_reaching_threshold(self):
        obs = [
            {"start_hour": 23, "sleep_min": 299},
            {"start_hour": 23, "sleep_min": 300},
            {"start_hour": 23, "sleep_min": 420},
        ]
        result = summarize(obs)[0]
        self.assertEqual(result["at_least_5h_pct"], 66.7)
        self.assertEqual(result["at_least_7h_pct"], 33.3)

    def test_missing_day_not_paired(self):
        data = [
            {"date": "2024-01-01", "source": "WATCH", "sleep_min": 210},
            {"date": "2024-01-03", "source": "WATCH", "sleep_min": 440},
        ]
        self.assertEqual(next_calendar_day_pairs(data), [])

    def test_different_sources_not_paired(self):
        data = [
            {"date": "2024-01-01", "source": "WATCH", "sleep_min": 210},
            {"date": "2024-01-02", "source": "APP", "sleep_min": 440},
        ]
        self.assertEqual(next_calendar_day_pairs(data), [])

    def test_duplicate_date_source_rejected(self):
        data = [{"date": "2024-01-01", "source": "WATCH", "sleep_min": 210}] * 2
        with self.assertRaises(ValueError):
            next_calendar_day_pairs(data)

    def test_deterministic_synthetic_data(self):
        self.assertEqual(fictional_nights(8), fictional_nights(8))

    def test_consecutive_pairs(self):
        self.assertEqual(len(next_calendar_day_pairs(fictional_nights(12))), 11)


if __name__ == "__main__":
    unittest.main()

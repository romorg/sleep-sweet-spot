"""Public, completely synthetic examples for Sleep Sweet Spot.

This module does NOT contain or download any participant sleep data.
"""
from collections import defaultdict
from datetime import date, timedelta
from statistics import median
from random import Random


def onset_bucket(hour):
    """Continuous nocturnal clock: 00:30 is 24.5, 02:15 is 26.25."""
    if 20 <= hour < 22:
        return "20-22"
    if 22 <= hour < 24:
        return "22-24"
    if 24 <= hour < 26:
        return "00-02"
    if 26 <= hour < 29:
        return "02-05"
    return None


def summarize(nights):
    """Return descriptive observations, never a recommended sleep target."""
    groups = defaultdict(list)
    for night in nights:
        bucket = onset_bucket(night["start_hour"])
        if bucket is not None:
            groups[bucket].append(night["sleep_min"])
    rows = []
    for bucket in ("20-22", "22-24", "00-02", "02-05"):
        vals = groups[bucket]
        if vals:
            rows.append({
                "bucket": bucket,
                "n": len(vals),
                "median_minutes": round(median(vals), 1),
                "at_least_5h_pct": round(100 * sum(x >= 300 for x in vals) / len(vals), 1),
                "at_least_7h_pct": round(100 * sum(x >= 420 for x in vals) / len(vals), 1),
            })
    return rows


def next_calendar_day_pairs(nights):
    """Never pair nights separated by missing dates or from different sources."""
    by_key = {}
    for row in nights:
        key = (date.fromisoformat(row["date"]), row["source"])
        if key in by_key:
            raise ValueError("Duplicate date/source: reconstruct episodes before pairing")
        by_key[key] = row["sleep_min"]
    pairs = []
    for (day, source), minutes in sorted(by_key.items()):
        following = by_key.get((day + timedelta(days=1), source))
        if following is not None:
            pairs.append((minutes, following))
    return pairs


def fictional_nights(n=240, seed=46):
    """Deterministic artificial records. Coefficients here are invented."""
    rng = Random(seed)
    first = date(2024, 1, 1)
    rows = []
    for i in range(n):
        start = rng.uniform(21, 28)
        duration = max(180, min(600, rng.gauss(465 - 25 * (start - 22), 65)))
        rows.append({
            "date": (first + timedelta(days=i)).isoformat(),
            "source": "SIMULATED",
            "start_hour": round(start, 2),
            "sleep_min": round(duration, 1),
        })
    return rows


if __name__ == "__main__":
    data = fictional_nights()
    print("SYNTHETIC DEMONSTRATION ONLY; NOT PERSONAL SLEEP RESULTS")
    for group in summarize(data):
        print(group)
    print("Genuinely consecutive-night pairs:", len(next_calendar_day_pairs(data)))

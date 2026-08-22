import unittest
from datetime import date

from scripts.garmin.garmin_intervals_activity_backfill import (
    fetch_garmin_inventory,
    garmin_fingerprint,
    intervals_fingerprint,
    match_activity_inventories,
)


def garmin_activity(
    activity_id,
    start,
    duration=3600.0,
    distance=10000.0,
    activity_type="running",
):
    return {
        "activityId": activity_id,
        "startTimeLocal": start,
        "elapsedDuration": duration,
        "distance": distance,
        "activityType": {"typeKey": activity_type},
    }


def intervals_activity(
    activity_id,
    start,
    duration=3600,
    distance=10000.0,
    activity_type="Run",
):
    return {
        "id": activity_id,
        "start_date_local": start,
        "elapsed_time": duration,
        "distance": distance,
        "type": activity_type,
    }


class ActivityMatchingTests(unittest.TestCase):
    def test_matching_uses_start_duration_distance_and_type(self):
        garmin = [
            garmin_fingerprint(
                garmin_activity(
                    123,
                    "2026-03-01T07:00:00",
                    duration=3600.3,
                    distance=10010.0,
                )
            )
        ]
        intervals = [
            intervals_fingerprint(
                intervals_activity(
                    "i1",
                    "2026-03-01T07:00:30",
                    duration=3599,
                    distance=10000.0,
                )
            )
        ]

        matches, missing, unmatched = match_activity_inventories(
            garmin, intervals
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(missing, [])
        self.assertEqual(unmatched, [])

    def test_wrong_activity_family_is_not_matched(self):
        garmin = [
            garmin_fingerprint(
                garmin_activity(123, "2026-03-01T07:00:00", activity_type="running")
            )
        ]
        intervals = [
            intervals_fingerprint(
                intervals_activity(
                    "i1", "2026-03-01T07:00:00", activity_type="Ride"
                )
            )
        ]

        matches, missing, unmatched = match_activity_inventories(
            garmin, intervals
        )

        self.assertEqual(matches, [])
        self.assertEqual(len(missing), 1)
        self.assertEqual(len(unmatched), 1)

    def test_one_intervals_activity_cannot_match_two_garmin_activities(self):
        garmin = [
            garmin_fingerprint(garmin_activity(1, "2026-03-01T07:00:00")),
            garmin_fingerprint(garmin_activity(2, "2026-03-01T07:00:20")),
        ]
        intervals = [
            intervals_fingerprint(
                intervals_activity("i1", "2026-03-01T07:00:10")
            )
        ]

        matches, missing, unmatched = match_activity_inventories(
            garmin, intervals
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(len(missing), 1)
        self.assertEqual(unmatched, [])


class FakeGarminClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def getActivities(self, start, limit):
        self.calls.append((start, limit))
        return self.pages.get(start, [])


class GarminInventoryTests(unittest.TestCase):
    def test_pagination_stops_after_page_is_older_than_range(self):
        client = FakeGarminClient(
            {
                0: [
                    garmin_activity(3, "2026-03-02T07:00:00"),
                    garmin_activity(2, "2026-02-28T07:00:00"),
                ],
                100: [
                    garmin_activity(1, "2025-12-31T07:00:00"),
                ],
            }
        )

        inventory = fetch_garmin_inventory(
            client, date(2026, 1, 1), date(2026, 3, 31)
        )

        self.assertEqual([item.source_id for item in inventory], ["3", "2"])
        self.assertEqual(client.calls, [(0, 100), (100, 100)])


if __name__ == "__main__":
    unittest.main()

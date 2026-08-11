import json
import os
import tempfile
import unittest


class GarminGlobalQueueTests(unittest.TestCase):
    def test_first_run_only_bootstraps_one_page(self):
        from scripts.garmin_global.queue import discover_pending_ids

        calls = []

        def fetch_page(start, limit):
            calls.append((start, limit))
            return [
                {"activityId": 30},
                {"activityId": 20},
                {"activityId": 10},
            ]

        pending = discover_pending_ids(fetch_page, set(), page_size=3)

        self.assertEqual(pending, [30, 20, 10])
        self.assertEqual(calls, [(0, 3)])

    def test_scans_until_it_reaches_a_previously_synced_activity(self):
        from scripts.garmin_global.queue import discover_pending_ids

        pages = {
            0: [{"activityId": 50}, {"activityId": 40}],
            2: [{"activityId": 30}, {"activityId": 20}],
        }

        pending = discover_pending_ids(
            lambda start, limit: pages.get(start, []),
            {20, 10},
            page_size=2,
        )

        self.assertEqual(pending, [50, 40, 30])

    def test_state_persists_only_successful_activity_ids(self):
        from scripts.garmin_global.queue import GlobalSyncState

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "state.json")
            state = GlobalSyncState(path)
            state.mark_synced(123)
            state.mark_synced(456)

            reloaded = GlobalSyncState(path)
            self.assertEqual(reloaded.synced_ids, {123, 456})

            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["synced_activity_ids"], [123, 456])


if __name__ == "__main__":
    unittest.main()

import io
import unittest
from unittest.mock import patch

from scripts.garmin.garmin_health_intervals_sync import (
    GarminHealthReader,
    build_intervals_wellness_record,
    run_cli,
)


class FakeGarminClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_display_name(self):
        return "display-name"

    def connectapi(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return self.responses[path]


class GarminHealthIntervalsSyncTests(unittest.TestCase):
    def test_maps_only_semantically_compatible_wellness_fields(self):
        record = build_intervals_wellness_record(
            "2026-08-21",
            summary={
                "totalSteps": 12345,
                "restingHeartRate": 49,
                "averageStressLevel": 31,
                "bodyBatteryHighestValue": 91,
            },
            sleep={
                "dailySleepDTO": {
                    "sleepTimeSeconds": 26700,
                    "avgSpO2": 96.5,
                    "avgRespirationValue": 13.8,
                    "averageSleepHeartRate": 47,
                    "sleepScores": {"overall": {"value": 86}},
                }
            },
            hrv={"hrvSummary": {"lastNightAvg": 54.2}},
            readiness=[
                {
                    "timestampLocal": "2026-08-21T05:00:00.0",
                    "score": 68,
                    "inputContext": "DAILY_UPDATE",
                },
                {
                    "timestampLocal": "2026-08-21T07:00:00.0",
                    "score": 76,
                    "inputContext": "AFTER_WAKEUP_RESET",
                },
            ],
        )

        self.assertEqual(
            record,
            {
                "id": "2026-08-21",
                "restingHR": 49,
                "hrv": 54.2,
                "sleepSecs": 26700,
                "sleepScore": 86,
                "avgSleepingHR": 47,
                "spO2": 96.5,
                "readiness": 76,
                "steps": 12345,
                "respiration": 13.8,
            },
        )
        self.assertNotIn("stress", record)
        self.assertNotIn("comments", record)

    def test_missing_values_are_omitted_and_sleep_hrv_is_a_fallback(self):
        record = build_intervals_wellness_record(
            "2026-08-20",
            summary={"totalSteps": None, "restingHeartRate": 0},
            sleep={
                "dailySleepDTO": {
                    "avgSleepHRV": 51.0,
                    "sleepScores": {"overall": {"value": None}},
                }
            },
            hrv=None,
            readiness=[],
        )

        self.assertEqual(record, {"id": "2026-08-20", "hrv": 51.0})

    def test_reader_uses_confirmed_garmin_connect_endpoints(self):
        responses = {
            "/usersummary-service/usersummary/daily/display-name": {
                "totalSteps": 1
            },
            "/wellness-service/wellness/dailySleepData/display-name": {
                "dailySleepDTO": {}
            },
            "/hrv-service/hrv/2026-08-21": {"hrvSummary": {}},
            "/metrics-service/metrics/trainingreadiness/2026-08-21": [],
        }
        client = FakeGarminClient(responses)

        record = GarminHealthReader(client).fetch_day("2026-08-21")

        self.assertEqual(record, {"id": "2026-08-21", "steps": 1})
        self.assertEqual(
            client.calls,
            [
                (
                    "/usersummary-service/usersummary/daily/display-name",
                    {"params": {"calendarDate": "2026-08-21"}},
                ),
                (
                    "/wellness-service/wellness/dailySleepData/display-name",
                    {
                        "params": {
                            "date": "2026-08-21",
                            "nonSleepBufferMinutes": 60,
                        }
                    },
                ),
                ("/hrv-service/hrv/2026-08-21", {}),
                (
                    "/metrics-service/metrics/trainingreadiness/2026-08-21",
                    {},
                ),
            ],
        )

    def test_cli_error_does_not_print_sensitive_exception_details(self):
        stderr = io.StringIO()
        sensitive = "403 https://connectapi.garmin.cn/private-user-id"

        with (
            patch(
                "scripts.garmin.garmin_health_intervals_sync.main",
                side_effect=RuntimeError(sensitive),
            ),
            patch("sys.stderr", stderr),
        ):
            result = run_cli([])

        self.assertEqual(result, 1)
        self.assertIn("RuntimeError", stderr.getvalue())
        self.assertNotIn("private-user-id", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

"""Sync Garmin China daily health summaries into Intervals.icu wellness."""

import argparse
import json
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .garmin_client import GarminClient
from .intervals_client import IntervalsClient


DAILY_SUMMARY_PATH = "/usersummary-service/usersummary/daily/{display_name}"
SLEEP_PATH = "/wellness-service/wellness/dailySleepData/{display_name}"
HRV_PATH = "/hrv-service/hrv/{date}"
READINESS_PATH = "/metrics-service/metrics/trainingreadiness/{date}"


def _number(value, minimum=None, maximum=None, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if minimum is not None and value < minimum:
        return None
    if maximum is not None and value > maximum:
        return None
    return int(value) if integer else value


def _nested(mapping, *keys):
    current = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _readiness_score(readiness):
    if isinstance(readiness, dict):
        candidates = [readiness]
    elif isinstance(readiness, list):
        candidates = [item for item in readiness if isinstance(item, dict)]
    else:
        candidates = []

    wakeup = [
        item
        for item in candidates
        if item.get("inputContext") == "AFTER_WAKEUP_RESET"
    ]
    selected = wakeup or candidates
    if not selected:
        return None
    latest = max(
        selected,
        key=lambda item: item.get("timestampLocal") or item.get("timestamp") or "",
    )
    return _number(latest.get("score"), minimum=0, maximum=100)


def build_intervals_wellness_record(
    calendar_date, summary=None, sleep=None, hrv=None, readiness=None
):
    """Map only fields whose Garmin and Intervals meanings and units agree."""
    summary = summary if isinstance(summary, dict) else {}
    sleep_dto = _nested(sleep, "dailySleepDTO") or {}
    hrv_summary = _nested(hrv, "hrvSummary") or {}

    record = {"id": calendar_date}
    values = {
        "restingHR": _number(
            summary.get("restingHeartRate"), minimum=20, maximum=250, integer=True
        ),
        "hrv": _number(
            hrv_summary.get("lastNightAvg")
            if hrv_summary.get("lastNightAvg") is not None
            else sleep_dto.get("avgSleepHRV"),
            minimum=1,
            maximum=500,
        ),
        "sleepSecs": _number(
            sleep_dto.get("sleepTimeSeconds"),
            minimum=1,
            maximum=86400,
            integer=True,
        ),
        "sleepScore": _number(
            _nested(sleep_dto, "sleepScores", "overall", "value"),
            minimum=0,
            maximum=100,
        ),
        "avgSleepingHR": _number(
            sleep_dto.get("averageSleepHeartRate")
            if sleep_dto.get("averageSleepHeartRate") is not None
            else sleep_dto.get("avgSleepHeartRate"),
            minimum=20,
            maximum=250,
        ),
        "spO2": _number(
            sleep_dto.get("avgSpO2"), minimum=50, maximum=100
        ),
        "readiness": _readiness_score(readiness),
        "steps": _number(
            summary.get("totalSteps"), minimum=0, maximum=200000, integer=True
        ),
        "respiration": _number(
            sleep_dto.get("avgRespirationValue"), minimum=1, maximum=80
        ),
    }
    record.update({key: value for key, value in values.items() if value is not None})
    return record


class GarminHealthReader:
    def __init__(self, client, display_name=None):
        self.client = client
        self.display_name = display_name

    def fetch_day(self, calendar_date):
        display_name = self.display_name or self.client.get_display_name()
        summary = self.client.connectapi(
            DAILY_SUMMARY_PATH.format(display_name=display_name),
            params={"calendarDate": calendar_date},
        )
        sleep = self.client.connectapi(
            SLEEP_PATH.format(display_name=display_name),
            params={"date": calendar_date, "nonSleepBufferMinutes": 60},
        )
        hrv = self.client.connectapi(HRV_PATH.format(date=calendar_date))
        readiness = self.client.connectapi(
            READINESS_PATH.format(date=calendar_date)
        )
        return build_intervals_wellness_record(
            calendar_date,
            summary=summary,
            sleep=sleep,
            hrv=hrv,
            readiness=readiness,
        )


def _calendar_dates(end_date, days):
    if days < 1 or days > 31:
        raise ValueError("days must be between 1 and 31")
    return [
        (end_date - timedelta(days=offset)).isoformat()
        for offset in reversed(range(days))
    ]


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sync Garmin China health summaries to Intervals.icu"
    )
    parser.add_argument(
        "--date",
        help="Last local date to process (YYYY-MM-DD); defaults to China today",
    )
    parser.add_argument("--days", type=int, default=3)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--upload", action="store_true", help="Write the records to Intervals.icu"
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="Read and validate without writing"
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Print health values (intended only for a trusted local terminal)",
    )
    return parser.parse_args(argv)


def _garmin_client_from_env():
    token = os.environ.get("GARMIN_CN_GARTH_TOKEN", "").strip()
    email = os.environ.get("GARMIN_EMAIL", "").strip()
    password = os.environ.get("GARMIN_PASSWORD", "")
    if not token and (not email or not password):
        raise RuntimeError(
            "Set GARMIN_CN_GARTH_TOKEN, or GARMIN_EMAIL and GARMIN_PASSWORD"
        )
    return GarminClient(
        email,
        password,
        "CN",
        1,
        garth_token=token or None,
        allow_password_login=not bool(token),
    )


def main(argv=None):
    args = _parse_args(argv)
    end_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ZoneInfo("Asia/Shanghai")).date()
    )
    reader = GarminHealthReader(
        _garmin_client_from_env(),
        display_name=os.environ.get("GARMIN_DISPLAY_NAME") or None,
    )
    records = [reader.fetch_day(day) for day in _calendar_dates(end_date, args.days)]
    records = [record for record in records if len(record) > 1]
    if not records:
        raise RuntimeError("Garmin returned no supported wellness values")

    if args.show_values:
        print(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for record in records:
            fields = ",".join(sorted(key for key in record if key != "id"))
            print(f"validated {record['id']}: {fields}")

    if not args.upload:
        print("dry-run complete; Intervals.icu was not modified")
        return 0

    api_key = os.environ.get("INTERVALS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("INTERVALS_API_KEY is required with --upload")
    IntervalsClient(api_key).upsert_wellness(records)
    print(f"uploaded {len(records)} wellness record(s) to Intervals.icu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

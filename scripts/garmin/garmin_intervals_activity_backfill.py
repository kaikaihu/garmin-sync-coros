"""Backfill missing Garmin China activities into Intervals.icu."""

import argparse
import os
import sys
import tempfile
import time
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from .garmin_client import GarminClient
from .intervals_client import IntervalsClient


@dataclass(frozen=True)
class ActivityFingerprint:
    source_id: str
    start: datetime
    duration: Optional[float]
    distance: Optional[float]
    activity_type: str
    raw: dict = field(compare=False, repr=False)


TYPE_FAMILIES = {
    "running": "RUN",
    "run": "RUN",
    "trail_running": "RUN",
    "trailrun": "RUN",
    "treadmill_running": "RUN",
    "walking": "WALK",
    "walk": "WALK",
    "hiking": "HIKE",
    "hike": "HIKE",
    "cycling": "RIDE",
    "ride": "RIDE",
    "indoor_cycling": "RIDE",
    "strength_training": "STRENGTH",
    "weighttraining": "STRENGTH",
    "open_water_swimming": "OPEN_WATER_SWIM",
    "openwaterswim": "OPEN_WATER_SWIM",
    "lap_swimming": "SWIM",
    "swim": "SWIM",
}


def _parse_local_datetime(value):
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    # Garmin startTimeLocal and Intervals start_date_local are wall-clock values.
    # Drop an optional offset instead of converting it to another timezone.
    return parsed.replace(tzinfo=None)


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _garmin_type(activity):
    activity_type = activity.get("activityType")
    if isinstance(activity_type, dict):
        return str(
            activity_type.get("typeKey")
            or activity_type.get("typeId")
            or "UNKNOWN"
        )
    return str(activity_type or "UNKNOWN")


def garmin_fingerprint(activity):
    start = _parse_local_datetime(
        activity.get("startTimeLocal") or activity.get("startTimeGMT")
    )
    activity_id = activity.get("activityId")
    if start is None or activity_id is None:
        return None
    return ActivityFingerprint(
        source_id=str(activity_id),
        start=start,
        duration=_number(
            activity.get("elapsedDuration")
            if activity.get("elapsedDuration") is not None
            else activity.get("duration")
        ),
        distance=_number(activity.get("distance")),
        activity_type=_garmin_type(activity),
        raw=activity,
    )


def intervals_fingerprint(activity):
    start = _parse_local_datetime(
        activity.get("start_date_local") or activity.get("start_date")
    )
    activity_id = activity.get("id")
    if start is None or activity_id is None:
        return None
    return ActivityFingerprint(
        source_id=str(activity_id),
        start=start,
        duration=_number(
            activity.get("elapsed_time")
            if activity.get("elapsed_time") is not None
            else activity.get("moving_time")
        ),
        distance=_number(
            activity.get("distance")
            if activity.get("distance") is not None
            else activity.get("icu_distance")
        ),
        activity_type=str(activity.get("type") or "UNKNOWN"),
        raw=activity,
    )


def _type_family(activity_type):
    return TYPE_FAMILIES.get(str(activity_type).strip().lower())


def _match_score(garmin_activity, intervals_activity):
    start_delta = abs(
        (garmin_activity.start - intervals_activity.start).total_seconds()
    )
    if start_delta > 120:
        return None

    garmin_family = _type_family(garmin_activity.activity_type)
    intervals_family = _type_family(intervals_activity.activity_type)
    if garmin_family and intervals_family and garmin_family != intervals_family:
        return None

    duration_delta = 0.0
    if (
        garmin_activity.duration is not None
        and intervals_activity.duration is not None
    ):
        duration_delta = abs(
            garmin_activity.duration - intervals_activity.duration
        )
        duration_tolerance = max(
            120.0,
            0.05 * max(garmin_activity.duration, intervals_activity.duration),
        )
        if duration_delta > duration_tolerance:
            return None

    distance_delta = 0.0
    if (
        garmin_activity.distance is not None
        and intervals_activity.distance is not None
    ):
        distance_delta = abs(
            garmin_activity.distance - intervals_activity.distance
        )
        distance_tolerance = max(
            250.0,
            0.03 * max(garmin_activity.distance, intervals_activity.distance),
        )
        if distance_delta > distance_tolerance:
            return None

    return start_delta + duration_delta / 10.0 + distance_delta / 100.0


def match_activity_inventories(garmin_activities, intervals_activities):
    """Return one-to-one matches and Garmin activities missing in Intervals."""
    remaining = set(range(len(intervals_activities)))
    matches = []
    missing = []

    for garmin_activity in sorted(garmin_activities, key=lambda item: item.start):
        candidates = []
        for index in remaining:
            score = _match_score(garmin_activity, intervals_activities[index])
            if score is not None:
                candidates.append((score, index))
        if not candidates:
            missing.append(garmin_activity)
            continue
        _, best_index = min(candidates)
        remaining.remove(best_index)
        matches.append((garmin_activity, intervals_activities[best_index]))

    return matches, missing, [intervals_activities[index] for index in remaining]


def fetch_garmin_inventory(client, start_date, end_date, page_size=100):
    fingerprints = []
    seen_ids = set()
    offset = 0

    for _ in range(100):
        page = client.getActivities(start=offset, limit=page_size)
        if not page:
            break

        page_fingerprints = [
            fingerprint
            for fingerprint in (garmin_fingerprint(item) for item in page)
            if fingerprint is not None
        ]
        for fingerprint in page_fingerprints:
            activity_date = fingerprint.start.date()
            if (
                start_date <= activity_date <= end_date
                and fingerprint.source_id not in seen_ids
            ):
                seen_ids.add(fingerprint.source_id)
                fingerprints.append(fingerprint)

        if page_fingerprints and max(
            item.start.date() for item in page_fingerprints
        ) < start_date:
            break
        offset += page_size
    else:
        raise RuntimeError("Garmin activity pagination exceeded safety limit")

    return fingerprints


def fetch_intervals_inventory(client, start_date, end_date):
    activities = client.list_activities(
        start_date.isoformat(), end_date.isoformat(), limit=1000
    )
    return [
        fingerprint
        for fingerprint in (intervals_fingerprint(item) for item in activities)
        if fingerprint is not None
    ]


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


def _print_inventory_summary(garmin, intervals, matches, missing):
    print(f"Garmin activities in range: {len(garmin)}")
    print(f"Intervals activities in range: {len(intervals)}")
    print(f"Matched activities: {len(matches)}")
    print(f"Missing Garmin activities: {len(missing)}")
    if missing:
        by_month = Counter(item.start.strftime("%Y-%m") for item in missing)
        by_type = Counter(_type_family(item.activity_type) or "OTHER" for item in missing)
        print(
            "Missing by month: "
            + ", ".join(f"{key}={value}" for key, value in sorted(by_month.items()))
        )
        print(
            "Missing by type: "
            + ", ".join(f"{key}={value}" for key, value in sorted(by_type.items()))
        )


def _upload_missing(garmin_client, intervals_client, missing):
    with tempfile.TemporaryDirectory(prefix="garmin-intervals-backfill-") as temp_dir:
        for index, activity in enumerate(missing, start=1):
            archive_bytes = garmin_client.downloadFitActivity(activity.source_id)
            archive_path = os.path.join(temp_dir, f"activity-{index}.zip")
            with open(archive_path, "wb") as archive:
                archive.write(archive_bytes)
            if not zipfile.is_zipfile(archive_path):
                raise ValueError("Garmin activity download was not a valid ZIP archive")
            intervals_client.upload_activity_archive(
                archive_path,
                external_id=f"garmin-cn-{activity.source_id}",
            )
            print(f"Uploaded missing activity {index}/{len(missing)}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill missing Garmin China activities into Intervals.icu"
    )
    parser.add_argument("--start", default="2026-01-01")
    parser.add_argument(
        "--end",
        help="Inclusive China-local end date; defaults to today",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload only activities proven missing; default is read-only",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    start_date = date.fromisoformat(args.start)
    end_date = (
        date.fromisoformat(args.end)
        if args.end
        else datetime.now(ZoneInfo("Asia/Shanghai")).date()
    )
    if start_date > end_date:
        raise ValueError("start date must not be after end date")

    api_key = os.environ.get("INTERVALS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("INTERVALS_API_KEY is required")

    garmin_client = _garmin_client_from_env()
    intervals_client = IntervalsClient(api_key, timeout=60)
    garmin = fetch_garmin_inventory(garmin_client, start_date, end_date)
    intervals = fetch_intervals_inventory(
        intervals_client, start_date, end_date
    )
    matches, missing, _ = match_activity_inventories(garmin, intervals)
    _print_inventory_summary(garmin, intervals, matches, missing)

    if not args.upload:
        print("dry-run complete; Intervals.icu was not modified")
        return 0
    if not missing:
        print("Intervals.icu already contains every Garmin activity in range")
        return 0

    _upload_missing(garmin_client, intervals_client, missing)

    # Intervals normally indexes uploads synchronously, but allow a short delay.
    remaining = missing
    for attempt in range(6):
        refreshed = fetch_intervals_inventory(
            intervals_client, start_date, end_date
        )
        _, remaining, _ = match_activity_inventories(garmin, refreshed)
        if not remaining:
            print(
                f"verified all {len(garmin)} Garmin activities are present in Intervals.icu"
            )
            return 0
        if attempt < 5:
            time.sleep(5)

    raise RuntimeError(
        f"Intervals.icu verification still reports {len(remaining)} missing activities"
    )


def run_cli(argv=None):
    try:
        return main(argv)
    except Exception as err:
        print(
            f"activity backfill failed safely: {type(err).__name__}; "
            "no existing activity was deleted",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())

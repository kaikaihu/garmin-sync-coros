"""Small Intervals.icu API client for wellness and activity transfers."""

import os
import requests


class IntervalsClient:
    ACTIVITIES_URL = "https://intervals.icu/api/v1/athlete/0/activities"
    WELLNESS_BULK_URL = (
        "https://intervals.icu/api/v1/athlete/0/wellness-bulk"
    )

    def __init__(self, api_key, session=None, timeout=30):
        if not api_key:
            raise ValueError("Intervals.icu API key is required")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout = timeout

    def upsert_wellness(self, records):
        """Create or partially update daily records using the bulk endpoint."""
        if not records:
            raise ValueError("at least one wellness record is required")

        response = self.session.put(
            self.WELLNESS_BULK_URL,
            auth=("API_KEY", self.api_key),
            json=records,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def list_activities(self, oldest, newest, limit=1000):
        """Return activity summaries for an inclusive local-date range."""
        response = self.session.get(
            self.ACTIVITIES_URL,
            auth=("API_KEY", self.api_key),
            params={
                "oldest": oldest,
                "newest": newest,
                "limit": limit,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        activities = response.json()
        if not isinstance(activities, list):
            raise ValueError("Intervals.icu returned a non-list activity inventory")
        return activities

    def upload_activity_archive(self, archive_path, external_id=None):
        """Upload one Garmin activity FIT/ZIP archive to Intervals.icu."""
        if not os.path.isfile(archive_path):
            raise ValueError("activity archive does not exist")

        params = {}
        if external_id:
            params["external_id"] = external_id

        with open(archive_path, "rb") as archive:
            response = self.session.post(
                self.ACTIVITIES_URL,
                auth=("API_KEY", self.api_key),
                params=params,
                files={
                    "file": (
                        os.path.basename(archive_path),
                        archive,
                        "application/zip",
                    )
                },
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response

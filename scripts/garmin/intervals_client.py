"""Small Intervals.icu API client for idempotent wellness updates."""

import requests


class IntervalsClient:
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

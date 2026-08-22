import unittest

from scripts.garmin.intervals_client import IntervalsClient


class FakeResponse:
    def __init__(self):
        self.raise_calls = 0

    def raise_for_status(self):
        self.raise_calls += 1


class FakeSession:
    def __init__(self):
        self.calls = []
        self.response = FakeResponse()

    def put(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class IntervalsClientTests(unittest.TestCase):
    def test_bulk_upsert_uses_personal_api_key_basic_auth(self):
        session = FakeSession()
        records = [{"id": "2026-08-21", "hrv": 54.2}]
        client = IntervalsClient("secret-api-key", session=session)

        response = client.upsert_wellness(records)

        self.assertIs(response, session.response)
        self.assertEqual(response.raise_calls, 1)
        self.assertEqual(
            session.calls,
            [
                (
                    "https://intervals.icu/api/v1/athlete/0/wellness-bulk",
                    {
                        "auth": ("API_KEY", "secret-api-key"),
                        "json": records,
                        "timeout": 30,
                    },
                )
            ],
        )

    def test_empty_bulk_is_rejected_before_network(self):
        session = FakeSession()
        client = IntervalsClient("secret-api-key", session=session)

        with self.assertRaisesRegex(ValueError, "at least one"):
            client.upsert_wellness([])

        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()

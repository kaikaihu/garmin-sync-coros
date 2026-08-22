import unittest

from scripts.garmin.intervals_client import IntervalsClient


class FakeResponse:
    def __init__(self, payload=None):
        self.raise_calls = 0
        self.payload = payload

    def raise_for_status(self):
        self.raise_calls += 1

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []
        self.response = FakeResponse()

    def put(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    def post(self, url, **kwargs):
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

    def test_list_activities_uses_inclusive_date_range(self):
        session = FakeSession()
        session.response = FakeResponse([{"id": "i1"}])
        client = IntervalsClient("secret-api-key", session=session)

        activities = client.list_activities("2026-01-01", "2026-08-22")

        self.assertEqual(activities, [{"id": "i1"}])
        self.assertEqual(session.response.raise_calls, 1)
        self.assertEqual(
            session.calls,
            [
                (
                    "https://intervals.icu/api/v1/athlete/0/activities",
                    {
                        "auth": ("API_KEY", "secret-api-key"),
                        "params": {
                            "oldest": "2026-01-01",
                            "newest": "2026-08-22",
                            "limit": 1000,
                        },
                        "timeout": 30,
                    },
                )
            ],
        )

    def test_upload_activity_archive_uses_multipart_and_external_id(self):
        import os
        import tempfile

        session = FakeSession()
        client = IntervalsClient("secret-api-key", session=session)
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, "activity.zip")
            with open(archive_path, "wb") as archive:
                archive.write(b"zip bytes")

            response = client.upload_activity_archive(
                archive_path, external_id="garmin-cn-123"
            )

        self.assertIs(response, session.response)
        self.assertEqual(session.response.raise_calls, 1)
        url, kwargs = session.calls[0]
        self.assertEqual(
            url, "https://intervals.icu/api/v1/athlete/0/activities"
        )
        self.assertEqual(kwargs["auth"], ("API_KEY", "secret-api-key"))
        self.assertEqual(kwargs["params"], {"external_id": "garmin-cn-123"})
        self.assertEqual(kwargs["timeout"], 30)
        filename, _, media_type = kwargs["files"]["file"]
        self.assertEqual(filename, "activity.zip")
        self.assertEqual(media_type, "application/zip")


if __name__ == "__main__":
    unittest.main()

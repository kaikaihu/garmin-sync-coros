import unittest

from scripts.garmin.garmin_client import (
    GarminClient,
    GarminSessionUnavailableError,
)


class FakeGarthClientState:
    def __init__(self):
        self._username = None
        self.sess = type("Session", (), {"headers": {"User-Agent": "test"}})()

    @property
    def username(self):
        if self._username is None:
            raise RuntimeError("no session")
        return self._username


class FakeGarth:
    def __init__(self, loads_error=None):
        self.client = FakeGarthClientState()
        self.loads_error = loads_error
        self.loads_calls = []
        self.login_calls = []
        self.configure_calls = []
        self.client.loads = self._loads

    def _loads(self, token):
        self.loads_calls.append(token)
        if self.loads_error:
            raise self.loads_error
        self.client._username = "token-user"

    def login(self, email, password):
        self.login_calls.append((email, password))
        self.client._username = "password-user"

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)

    def connectapi(self, path, **kwargs):
        return {"path": path, "username": self.client.username}


class GarminClientSessionTests(unittest.TestCase):
    def test_token_session_is_loaded_before_connectapi_without_password_login(self):
        garth = FakeGarth()
        client = GarminClient(
            "user@example.com",
            "password",
            "",
            1,
            garth_token="serialized-token",
            allow_password_login=False,
            garth_client=garth,
        )

        result = client.connectapi("/device-service/deviceregistration/devices")

        self.assertEqual(garth.loads_calls, ["serialized-token"])
        self.assertEqual(garth.login_calls, [])
        self.assertEqual(result["username"], "token-user")

    def test_missing_token_with_password_login_disabled_never_attempts_password_login(self):
        garth = FakeGarth()
        client = GarminClient(
            "user@example.com",
            "password",
            "",
            1,
            allow_password_login=False,
            garth_client=garth,
        )

        with self.assertRaises(GarminSessionUnavailableError):
            client.connectapi("/device-service/deviceregistration/devices")

        self.assertEqual(garth.login_calls, [])

    def test_invalid_token_with_password_login_disabled_never_attempts_password_login(self):
        garth = FakeGarth(loads_error=ValueError("invalid token"))
        client = GarminClient(
            "user@example.com",
            "password",
            "",
            1,
            garth_token="bad-token",
            allow_password_login=False,
            garth_client=garth,
        )

        with self.assertRaises(GarminSessionUnavailableError):
            client.connectapi("/device-service/deviceregistration/devices")

        self.assertEqual(garth.loads_calls, ["bad-token"])
        self.assertEqual(garth.login_calls, [])


if __name__ == "__main__":
    unittest.main()

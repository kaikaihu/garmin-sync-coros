import unittest

from scripts.garmin.garmin_client import (
    GarminClient,
    GarminSessionUnavailableError,
)


class FakeGarthClientState:
    def __init__(self):
        self._username = None
        self._profile = None
        self.oauth1_token = None
        self.sess = type("Session", (), {"headers": {"User-Agent": "test"}})()

    @property
    def username(self):
        if self._username is None:
            raise RuntimeError("no session")
        return self._username

    @property
    def profile(self):
        if self._profile is None:
            raise RuntimeError("no profile")
        return self._profile


class FakeGarth:
    def __init__(
        self, loads_error=None, missing_oauth1=False, profile_unavailable=False
    ):
        self.client = FakeGarthClientState()
        self.loads_error = loads_error
        self.missing_oauth1 = missing_oauth1
        self.profile_unavailable = profile_unavailable
        self.loads_calls = []
        self.login_calls = []
        self.configure_calls = []
        self.client.loads = self._loads

    def _loads(self, token):
        self.loads_calls.append(token)
        if self.loads_error:
            raise self.loads_error
        if not self.profile_unavailable:
            self.client._username = "token-user"
            self.client._profile = {
                "userName": "token-user",
                "displayName": "health-display-name",
            }
        if not self.missing_oauth1:
            self.client.oauth1_token = object()

    def login(self, email, password):
        self.login_calls.append((email, password))
        self.client._username = "password-user"
        self.client._profile = {
            "userName": "password-user",
            "displayName": "health-display-name",
        }

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)

    def connectapi(self, path, **kwargs):
        result = {"path": path}
        if not self.profile_unavailable:
            result["username"] = self.client.username
        return result


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

    def test_cn_domain_is_configured_before_loading_stored_token(self):
        garth = FakeGarth()
        client = GarminClient(
            "user@example.com",
            "password",
            "CN",
            1,
            garth_token="serialized-token",
            allow_password_login=False,
            garth_client=garth,
        )

        self.assertEqual(client.get_display_name(), "health-display-name")
        self.assertEqual(garth.configure_calls, [{"domain": "garmin.cn"}])
        self.assertEqual(garth.loads_calls, ["serialized-token"])

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

        with self.assertRaisesRegex(
            GarminSessionUnavailableError, "ValueError"
        ):
            client.connectapi("/device-service/deviceregistration/devices")

        self.assertEqual(garth.loads_calls, ["bad-token"])
        self.assertEqual(garth.login_calls, [])

    def test_missing_oauth1_after_token_load_is_rejected_without_password_login(self):
        garth = FakeGarth(missing_oauth1=True)
        client = GarminClient(
            "user@example.com",
            "password",
            "",
            1,
            garth_token="serialized-token",
            allow_password_login=False,
            garth_client=garth,
        )

        with self.assertRaisesRegex(
            GarminSessionUnavailableError, "GarminOAuth1MissingError"
        ):
            client.connectapi("/device-service/deviceregistration/devices")

        self.assertEqual(garth.login_calls, [])

    def test_token_loaded_session_does_not_require_profile_endpoint_before_device_request(self):
        garth = FakeGarth(profile_unavailable=True)
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

        self.assertEqual(result["path"], "/device-service/deviceregistration/devices")
        self.assertEqual(garth.loads_calls, ["serialized-token"])
        self.assertEqual(garth.login_calls, [])


if __name__ == "__main__":
    unittest.main()

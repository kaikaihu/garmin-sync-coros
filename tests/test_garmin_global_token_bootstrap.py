import unittest

from scripts.garmin.garmin_global_token_bootstrap import create_token


class FakeGarth:
    def __init__(self):
        self.login_calls = []

    def login(self, email, password):
        self.login_calls.append((email, password))

    def dumps(self):
        return "serialized-token"


class ClientStyleFakeGarth:
    class Client:
        class Session:
            def __init__(self):
                self.headers = {"User-Agent": "GCM-iOS-5.7.2.1"}

        def __init__(self):
            self.sess = self.Session()

        def dumps(self):
            return "client-serialized-token"

    def __init__(self):
        self.login_calls = []
        self.client = self.Client()

    def login(self, email, password):
        self.login_calls.append((email, password))


class GarminGlobalTokenBootstrapTests(unittest.TestCase):
    def test_create_token_logs_in_once_and_returns_serialized_garth_session(self):
        garth = FakeGarth()

        token = create_token("user@example.com", "password", garth_client=garth)

        self.assertEqual(token, "serialized-token")
        self.assertEqual(garth.login_calls, [("user@example.com", "password")])

    def test_create_token_uses_client_serializer_when_newer_garth_has_no_module_serializer(self):
        garth = ClientStyleFakeGarth()

        token = create_token("user@example.com", "password", garth_client=garth)

        self.assertEqual(token, "client-serialized-token")
        self.assertEqual(garth.login_calls, [("user@example.com", "password")])

    def test_create_token_uses_browser_user_agent_for_login(self):
        class HeaderAwareGarth(ClientStyleFakeGarth):
            def login(self, email, password):
                self.login_user_agent = self.client.sess.headers["User-Agent"]
                super().login(email, password)

        garth = HeaderAwareGarth()

        create_token("user@example.com", "password", garth_client=garth)

        self.assertEqual(
            garth.login_user_agent,
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36",
        )


if __name__ == "__main__":
    unittest.main()

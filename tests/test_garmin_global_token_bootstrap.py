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


if __name__ == "__main__":
    unittest.main()

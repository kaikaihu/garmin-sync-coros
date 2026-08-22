import unittest

from scripts.garmin.garmin_cn_token_bootstrap import create_token


class FakeSession:
    def __init__(self):
        self.headers = {}


class FakeClient:
    def __init__(self):
        self.sess = FakeSession()

    def dumps(self):
        return "serialized-cn-token"


class FakeGarth:
    def __init__(self):
        self.client = FakeClient()
        self.calls = []

    def configure(self, **kwargs):
        self.calls.append(("configure", kwargs))

    def login(self, email, password):
        self.calls.append(("login", email, password))


class GarminCnTokenBootstrapTests(unittest.TestCase):
    def test_configures_china_before_login_and_uses_client_serializer(self):
        garth = FakeGarth()

        token = create_token("user@example.com", "password", garth_client=garth)

        self.assertEqual(token, "serialized-cn-token")
        self.assertEqual(
            garth.calls,
            [
                ("configure", {"domain": "garmin.cn"}),
                ("login", "user@example.com", "password"),
            ],
        )
        self.assertIn("Mozilla/5.0", garth.client.sess.headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()

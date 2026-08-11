import unittest


class GarminGlobalClientTests(unittest.TestCase):
    def test_create_client_uses_global_mode_and_tokenstore(self):
        from scripts.garmin.garmin_global_client import create_global_client

        calls = {}

        class FakeGarmin:
            def __init__(self, email=None, password=None, is_cn=False):
                calls["init"] = (email, password, is_cn)

            def login(self, tokenstore=None):
                calls["login"] = tokenstore

        client = create_global_client(
            "global@example.com",
            "secret",
            "/tmp/garmin-global-tokens",
            client_factory=FakeGarmin,
        )

        self.assertIsInstance(client, FakeGarmin)
        self.assertEqual(calls["init"], ("global@example.com", "secret", False))
        self.assertEqual(calls["login"], "/tmp/garmin-global-tokens")


if __name__ == "__main__":
    unittest.main()

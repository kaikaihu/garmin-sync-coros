import os
import unittest
from unittest.mock import patch

from scripts.garmin import garmin_health_device_probe
from scripts.garmin.garmin_health_device_probe import redact_sensitive


class GarminHealthDeviceProbeTests(unittest.TestCase):
    def test_redacts_nested_device_identifiers_but_keeps_product_metadata(self):
        payload = {
            "deviceId": 123456789,
            "serialNumber": "ABC123XYZ",
            "productDisplayName": "Forerunner 970",
            "productId": 9999,
            "nested": {
                "unitId": "99887766",
                "uuid": "some-uuid",
                "status": "ACTIVE",
            },
            "items": [{"registrationId": "reg-secret", "deviceType": "WATCH"}],
        }

        redacted = redact_sensitive(payload)

        self.assertEqual(redacted["deviceId"], "***6789")
        self.assertEqual(redacted["serialNumber"], "***3XYZ")
        self.assertEqual(redacted["nested"]["unitId"], "***7766")
        self.assertEqual(redacted["nested"]["uuid"], "***uuid")
        self.assertEqual(redacted["items"][0]["registrationId"], "***cret")
        self.assertEqual(redacted["productDisplayName"], "Forerunner 970")
        self.assertEqual(redacted["productId"], 9999)
        self.assertEqual(redacted["nested"]["status"], "ACTIVE")
        self.assertEqual(redacted["items"][0]["deviceType"], "WATCH")

    @patch("scripts.garmin.garmin_health_device_probe.GarminClient")
    def test_global_probe_uses_supplied_session_token_with_password_login_disabled(
        self, client_class
    ):
        client_class.return_value.connectapi.side_effect = [[], {}, {}]
        environment = {
            "GARMIN_PROBE_REGION": "GLOBAL",
            "GARMIN_PROBE_GARTH_TOKEN": "serialized-token",
        }

        with patch.dict(os.environ, environment, clear=True):
            result = garmin_health_device_probe.main()

        self.assertEqual(result, 0)
        client_class.assert_called_once_with(
            "",
            "",
            "",
            1,
            garth_token="serialized-token",
            allow_password_login=False,
        )


if __name__ == "__main__":
    unittest.main()

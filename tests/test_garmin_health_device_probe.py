import unittest

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


if __name__ == "__main__":
    unittest.main()

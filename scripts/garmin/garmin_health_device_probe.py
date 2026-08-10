import json
import os
import sys

CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]
SCRIPTS_DIR = CURRENT_DIR.rsplit('/', 1)[0]
if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

from garmin.garmin_client import GarminClient

DEVICES_PATH = "/device-service/deviceregistration/devices"
PRIMARY_DEVICE_PATH = "/web-gateway/device-info/primary-training-device"
LAST_USED_PATH = "/device-service/deviceservice/mylastused"

SENSITIVE_KEY_PARTS = (
    "serial",
    "deviceid",
    "unitid",
    "uuid",
    "registrationid",
)


def mask_value(value):
    text = str(value)
    suffix = text[-4:] if len(text) >= 4 else text
    return f"***{suffix}"


def redact_sensitive(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = str(key).replace("_", "").lower()
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                result[key] = mask_value(item)
            else:
                result[key] = redact_sensitive(item)
        return result
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def print_result(label, payload):
    redacted = redact_sensitive(payload)
    encoded = json.dumps(redacted, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\n===== {label} =====")
    print(encoded)


def main():
    region = os.getenv("GARMIN_PROBE_REGION", "").strip().upper()
    email = os.getenv("GARMIN_PROBE_EMAIL", "").strip()
    password = os.getenv("GARMIN_PROBE_PASSWORD", "")
    garth_token = os.getenv("GARMIN_PROBE_GARTH_TOKEN", "").strip()

    if region not in {"CN", "GLOBAL"}:
        print("GARMIN_PROBE_REGION must be CN or GLOBAL")
        return 2
    if not garth_token:
        print("Missing GARMIN_PROBE_GARTH_TOKEN")
        return 2

    auth_domain = "CN" if region == "CN" else ""
    client = GarminClient(
        email,
        password,
        auth_domain,
        1,
        garth_token=garth_token or None,
        allow_password_login=False,
    )

    try:
        devices = client.connectapi(path=DEVICES_PATH)
        primary = client.connectapi(path=PRIMARY_DEVICE_PATH)
        last_used = client.connectapi(path=LAST_USED_PATH)
    except Exception as err:
        print(f"{region} read-only device probe failed: {type(err).__name__}: {err}")
        return 1

    print(f"Garmin region: {region}")
    print(f"Registered device count: {len(devices) if isinstance(devices, list) else 'unknown'}")
    print_result("Registered devices", devices)
    print_result("Primary training device", primary)
    print_result("Last used device", last_used)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

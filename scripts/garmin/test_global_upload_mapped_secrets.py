import os
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.garmin.garmin_client import GarminClient


def main():
    cn_email = os.getenv("GARMIN_EMAIL")
    cn_password = os.getenv("GARMIN_PASSWORD")
    global_email = os.getenv("GARMIN_GLOBAL_EMAIL")
    global_password = os.getenv("GARMIN_GLOBAL_PASSWORD")

    missing = [
        name for name, value in {
            "GARMIN_EMAIL": cn_email,
            "GARMIN_PASSWORD": cn_password,
            "GARMIN_GLOBAL_EMAIL": global_email,
            "GARMIN_GLOBAL_PASSWORD": global_password,
        }.items() if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    cn = GarminClient(cn_email, cn_password, "CN", 1)
    activities = cn.getActivities(0, 1)
    if not activities:
        raise RuntimeError("No Garmin CN activities found")

    activity_id = activities[0]["activityId"]
    payload = cn.downloadFitActivity(activity_id)

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"{activity_id}.zip")
        with open(zip_path, "wb") as fh:
            fh.write(payload)

        with zipfile.ZipFile(zip_path, "r") as zf:
            fit_names = [name for name in zf.namelist() if name.lower().endswith(".fit")]
            if not fit_names:
                raise RuntimeError("Downloaded Garmin archive contains no FIT file")
            fit_name = fit_names[0]
            zf.extract(fit_name, temp_dir)
            fit_path = os.path.join(temp_dir, fit_name)

        global_client = GarminClient(global_email, global_password, "", 1)
        result = global_client.upload_activity(fit_path)
        print(f"Garmin Global upload result: {result}")
        if result not in ("SUCCESS", "DUPLICATE_ACTIVITY"):
            raise RuntimeError(f"Garmin Global upload failed: {result}")


if __name__ == "__main__":
    main()

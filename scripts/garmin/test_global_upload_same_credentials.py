import os
import sys
import tempfile
import zipfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.garmin.garmin_client import GarminClient


def main():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        raise RuntimeError("GARMIN_EMAIL/GARMIN_PASSWORD are required")

    cn = GarminClient(email, password, "CN", 1)
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

        global_client = GarminClient(email, password, "", 1)
        result = global_client.upload_activity(fit_path)
        print(f"Garmin Global upload result: {result}")
        if result not in ("SUCCESS", "DUPLICATE_ACTIVITY"):
            raise RuntimeError(f"Garmin Global upload failed: {result}")


if __name__ == "__main__":
    main()

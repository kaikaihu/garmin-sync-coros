import os
import sys
import tempfile
import zipfile

CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]
SCRIPTS_DIR = CURRENT_DIR.rsplit('/', 1)[0]
if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

from config import GARMIN_FIT_DIR
from garmin.garmin_client import GarminClient

SUCCESS_STATUSES = {"SUCCESS", "DUPLICATE_ACTIVITY"}


def extract_fit_files(zip_path, output_dir):
    """Extract FIT members from one Garmin activity ZIP into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    extracted = []

    with zipfile.ZipFile(zip_path, "r") as archive:
        fit_members = [
            member for member in archive.infolist()
            if not member.is_dir() and member.filename.lower().endswith(".fit")
        ]

        for index, member in enumerate(fit_members):
            safe_name = os.path.basename(member.filename)
            if not safe_name:
                continue

            target_name = f"{index}_{safe_name}" if len(fit_members) > 1 else safe_name
            target_path = os.path.join(output_dir, target_name)

            with archive.open(member, "r") as source, open(target_path, "wb") as target:
                target.write(source.read())

            extracted.append(target_path)

    return extracted


def sync_zip_files(zip_dir, uploader):
    """Upload all FIT activities found in ZIP files from the current run."""
    result = {"total": 0, "succeeded": 0, "failed": 0}

    if not os.path.isdir(zip_dir):
        print(f"Garmin FIT directory does not exist: {zip_dir}")
        return result

    zip_paths = sorted(
        os.path.join(zip_dir, name)
        for name in os.listdir(zip_dir)
        if name.lower().endswith(".zip")
    )

    with tempfile.TemporaryDirectory(prefix="garmin-global-") as temp_dir:
        for zip_index, zip_path in enumerate(zip_paths):
            extract_dir = os.path.join(temp_dir, str(zip_index))
            try:
                fit_paths = extract_fit_files(zip_path, extract_dir)
            except Exception as err:
                print(f"Failed to read {os.path.basename(zip_path)}: {err}")
                result["failed"] += 1
                continue

            if not fit_paths:
                print(f"No FIT file found in {os.path.basename(zip_path)}")
                result["failed"] += 1
                continue

            for fit_path in fit_paths:
                result["total"] += 1
                try:
                    status = uploader.upload_activity(fit_path)
                    if status in SUCCESS_STATUSES:
                        result["succeeded"] += 1
                        print(f"Garmin Global upload {status}: {os.path.basename(fit_path)}")
                    else:
                        result["failed"] += 1
                        print(
                            f"Garmin Global upload failed ({status}): "
                            f"{os.path.basename(fit_path)}"
                        )
                except Exception as err:
                    result["failed"] += 1
                    print(
                        f"Garmin Global upload exception for "
                        f"{os.path.basename(fit_path)}: {err}"
                    )

    return result


def main():
    email = os.getenv("GARMIN_GLOBAL_EMAIL", "").strip()
    password = os.getenv("GARMIN_GLOBAL_PASSWORD", "")

    if not email or not password:
        print(
            "Missing Garmin Global credentials. Add GARMIN_GLOBAL_EMAIL and "
            "GARMIN_GLOBAL_PASSWORD as GitHub Actions secrets."
        )
        return 2

    uploader = GarminClient(email, password, "", 1)
    result = sync_zip_files(GARMIN_FIT_DIR, uploader)

    print(
        "Garmin Global sync summary: "
        f"total={result['total']} "
        f"succeeded={result['succeeded']} "
        f"failed={result['failed']}"
    )

    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

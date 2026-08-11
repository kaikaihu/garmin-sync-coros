import json
import os
import sys

CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]
SCRIPTS_DIR = CURRENT_DIR.rsplit('/', 1)[0]
if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

from config import DB_DIR, GARMIN_FIT_DIR
from garmin.garmin_client import GarminClient
from garmin_global.queue import GlobalSyncState, discover_pending_ids


def _int_env(name, default):
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def main():
    email = os.getenv("GARMIN_EMAIL", "").strip()
    password = os.getenv("GARMIN_PASSWORD", "")
    auth_domain = os.getenv("GARMIN_AUTH_DOMAIN", "CN")

    if not email or not password:
        print("Missing Garmin CN credentials for Garmin Global queue preparation.")
        return 2

    page_size = _int_env("GARMIN_GLOBAL_PAGE_SIZE", 5)
    max_pages = _int_env("GARMIN_GLOBAL_MAX_SCAN_PAGES", 50)
    max_retry = _int_env("GARMIN_GLOBAL_MAX_RETRY_PER_RUN", 20)

    state_path = os.getenv(
        "GARMIN_GLOBAL_STATE_PATH",
        os.path.join(DB_DIR, "garmin_global_state.json"),
    )
    queue_dir = os.getenv("GARMIN_GLOBAL_QUEUE_DIR", "/tmp/garmin-global-queue")
    manifest_path = os.getenv(
        "GARMIN_GLOBAL_MANIFEST_PATH",
        "/tmp/garmin-global-manifest.json",
    )

    os.makedirs(queue_dir, exist_ok=True)
    state = GlobalSyncState(state_path)
    client = GarminClient(email, password, auth_domain, page_size)

    discovered = discover_pending_ids(
        client.getActivities,
        state.synced_ids,
        page_size=page_size,
        max_pages=max_pages,
    )
    state.record_discovered(discovered)

    ordered_pending = []
    seen = set()
    for activity_id in discovered + sorted(state.pending_ids, reverse=True):
        activity_id = int(activity_id)
        if activity_id not in seen and activity_id not in state.synced_ids:
            ordered_pending.append(activity_id)
            seen.add(activity_id)

    activities = []
    for activity_id in ordered_pending[:max_retry]:
        same_run_zip = os.path.join(GARMIN_FIT_DIR, f"{activity_id}.zip")
        queue_zip = os.path.join(queue_dir, f"{activity_id}.zip")

        try:
            if os.path.exists(same_run_zip):
                zip_path = same_run_zip
                source = "current-run"
            else:
                payload = client.downloadFitActivity(activity_id)
                with open(queue_zip, "wb") as handle:
                    handle.write(payload)
                zip_path = queue_zip
                source = "retry-download"

            activities.append(
                {
                    "activity_id": activity_id,
                    "zip_path": zip_path,
                    "source": source,
                }
            )
        except Exception as err:
            print(f"Garmin Global queue download failed for {activity_id}: {err}")

    manifest = {
        "state_path": state_path,
        "activities": activities,
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(
        "Garmin Global queue prepared: "
        f"discovered={len(discovered)} pending={len(state.pending_ids)} "
        f"queued={len(activities)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

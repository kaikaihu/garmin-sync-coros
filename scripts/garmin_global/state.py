import json
import os
import tempfile


class GlobalSyncState:
    def __init__(self, path):
        self.path = path
        self.synced_ids = set()
        self.pending_ids = set()
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.synced_ids = {int(value) for value in payload.get("synced_activity_ids", [])}
        self.pending_ids = {int(value) for value in payload.get("pending_activity_ids", [])}
        self.pending_ids.difference_update(self.synced_ids)

    def _save(self):
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = {
            "synced_activity_ids": sorted(self.synced_ids),
            "pending_activity_ids": sorted(self.pending_ids),
        }
        target_dir = parent or "."
        fd, temp_path = tempfile.mkstemp(prefix="garmin-global-state-", dir=target_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def record_discovered(self, activity_ids):
        for activity_id in activity_ids:
            activity_id = int(activity_id)
            if activity_id not in self.synced_ids:
                self.pending_ids.add(activity_id)
        self._save()

    def mark_synced(self, activity_id):
        activity_id = int(activity_id)
        self.pending_ids.discard(activity_id)
        self.synced_ids.add(activity_id)
        self._save()


def discover_pending_ids(fetch_page, synced_ids, page_size=20, max_pages=50):
    """Discover new CN activities without repeatedly scanning full history.

    On the first run, bootstrap one recent page. On later runs, scan newest-first
    until a page contains an activity already known to be synced.
    """
    synced_ids = {int(value) for value in synced_ids}
    first_run = not synced_ids
    pending = []
    seen = set()

    for page_index in range(max_pages):
        start = page_index * page_size
        activities = fetch_page(start, page_size) or []
        if not activities:
            break

        reached_known = False
        for activity in activities:
            activity_id = int(activity["activityId"])
            if activity_id in synced_ids:
                reached_known = True
            elif activity_id not in seen:
                pending.append(activity_id)
                seen.add(activity_id)

        if first_run or reached_known or len(activities) < page_size:
            break

    return pending

# Garmin CN → Global Health Sync Research

## Scope and safety boundary

- This work exists only on `research/garmin-cn-global-health`.
- The production Garmin CN → COROS and activity → Global workflow on `master` is unchanged.
- Account/device probes are read-only. They never register, pair, rename, or delete a device.
- No wellness, sleep, HRV, stress, Body Battery, monitoring, or metrics payload is uploaded by this branch.

## Confirmed evidence

### 1. The Global runner failure is repeated password OAuth, before a device query

The 2026-08-10 probe run reached Garmin China successfully, then Garmin Global failed at:

`GET /oauth-service/oauth/preauthorized`

with `429 too many requests`. This happened before the first Global device endpoint was called. Therefore the previous failure proves neither that the Global account lacks a wearable nor that the device endpoints are invalid.

### 2. A reusable garth session is supported by the pinned library

The repository pins `garth==0.4.38`. That release implements `dumps()` / `loads()` and persists both OAuth1 and OAuth2 tokens. The OAuth1 token is enough for garth to obtain a fresh OAuth2 bearer token when required.

This branch therefore treats `GARMIN_GLOBAL_GARTH_TOKEN` as the only accepted Global probe credential. A missing or invalid token causes a controlled failure; it never falls back to password login.

Create the token once on a trusted local machine, then add it to GitHub Actions secrets under exactly this name:

```text
python scripts/garmin/garmin_global_token_bootstrap.py
GARMIN_GLOBAL_GARTH_TOKEN=<printed value>
```

The bootstrap script intentionally prints the token only to the local terminal. Do not run it in GitHub Actions and do not commit the value.

### 3. Token-only Global probe is reproducible; the Global account has no wearable identity

The token-only workflow run [31380333016](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/31380333016) completed successfully on 2026-08-10. It did not attempt password OAuth and therefore did not revisit the prior `429` path.

The read-only responses were:

- registered device count: `0`
- primary training device: empty
- last-used device: empty

During the work, the implementation was corrected to call `garth.client.loads()` (the public API) and to avoid using the unrelated profile endpoint as a session preflight. The device endpoint itself is therefore the evidence here, not a failed login or an inferred device state.

This is the current hard gate for any wellness import experiment: there is no Garmin Global wearable/device identity to associate with Monitoring, Sleep, Metrics, HRV, stress, or Body Battery data. No synthetic FIT or wellness payload was uploaded.

### 4. FIT has published health message definitions, but no public Garmin Connect ingest contract

Garmin's published FIT Profile contains these monitoring/health messages:

| Message | Global message number | Examples of published fields |
|---|---:|---|
| `monitoring` | 55 | timestamp, device_index, steps, calories, distance, heart_rate, active_time |
| `hrv` | 78 | beat-to-beat time |
| `monitoring_info` | 103 | timestamp, local_timestamp, activity_type, conversion factors |
| `monitoring_hr_data` | 211 | resting-heart-rate values |
| `stress_level` | 227 | stress value and calculation timestamp |
| `sleep_level` | 275 | timestamp and awake/light/deep/REM level |
| `sleep_assessment` | 346 | sleep score components, awakenings, average sleep stress |
| `hrv_status_summary` / `hrv_value` | 370 / 371 | nightly, weekly, baseline, and five-minute RMSSD data |

The `file` enum also defines `monitoring_a`, `monitoring_daily`, and `monitoring_b` file types. A FIT file can therefore encode the raw data model.

However, the public Garmin FIT documentation exposes upload examples for Activity, Course, and Workout files only. Garmin's public Health API is device-to-Garmin-Connect-to-partner (read-out), not a documented general-purpose endpoint for writing health data into Connect. The public sources inspected do not identify a supported endpoint, device-authentication contract, or post-upload processing sequence for synthetic Monitoring/Sleep/Metrics FIT.

## Next experiment gate

1. Associate a legitimate Garmin wearable with the Garmin Global account, then rerun the same token-only device probe and require a non-empty primary wearable result.
2. Capture the exact schema of a real wellness FIT from that device before considering any write experiment.
3. Independently observe the device's real upload/ingest transaction; public documentation does not publish a supported wellness import endpoint.
4. Do not submit a synthetic health FIT until the device identity and exact ingest contract are both observed. Any future first write requires separate approval and must be limited to one date with a documented rollback path.

## Public sources

- DailySync health-sync documentation: https://dailysync.vyzt.dev/docs/%E5%81%A5%E5%BA%B7%E6%95%B0%E6%8D%AE%E5%90%8C%E6%AD%A5
- Garmin Health API: https://developer.garmin.com/gc-developer-program/health-api/
- Garmin FIT SDK overview: https://developer.garmin.com/fit/overview/
- Garmin FIT SDK Tools / Profile: https://github.com/garmin/fit-sdk-tools
- garth 0.4.38 session implementation: https://github.com/matin/garth/blob/0.4.38/garth/http.py

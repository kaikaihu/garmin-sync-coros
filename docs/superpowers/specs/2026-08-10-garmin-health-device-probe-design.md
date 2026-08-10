# Garmin Health Device Probe Design

## Goal
Read Garmin China and Garmin Global account device metadata without modifying either account, to determine whether Garmin Global already has the wearable-device identity DailySync requires for health-data synchronization.

## Safety boundary
- Read-only requests only.
- Do not register, delete, rename, pair, or set any device.
- Do not upload wellness, sleep, HRV, stress, Body Battery, or monitoring data.
- Do not alter the existing Garmin→COROS or Garmin→Global activity workflows.
- Mask serial numbers and other device identifiers in Actions logs.

## Probe endpoints
Use Garmin Connect internal read endpoints already exposed by the existing Garmin client/session:
- `/device-service/deviceregistration/devices`
- `/web-gateway/device-info/primary-training-device`
- `/device-service/deviceservice/mylastused`

Run CN and Global as separate processes so the global `garth` client domain/session cannot leak across regions.

## Output
For each region print a compact summary of:
- device count
- display/product name when present
- product ID / device type when present
- masked device ID / serial when present
- primary training device response summary
- last-used device response summary

## Success criteria
The probe completes on GitHub-hosted Actions using existing CN and Global secrets and shows whether the Global account has at least one registered wearable-like Garmin device, without any write request.
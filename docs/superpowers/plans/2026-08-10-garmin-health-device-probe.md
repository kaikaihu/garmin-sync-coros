# Garmin Health Device Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and remotely run a read-only Garmin CN/Global device probe to determine whether the Global account has a registered wearable identity.

**Architecture:** A standalone Python script reads Garmin device endpoints using the existing `GarminClient.connectapi()` method. CN and Global run as separate workflow steps/processes with separate credentials so `garth` domain state cannot leak between regions.

**Tech Stack:** Python 3.10, existing `garth`-based `GarminClient`, GitHub Actions.

## Global Constraints
- Read-only requests only.
- Do not alter production activity workflows.
- Mask device identifiers in logs.
- Use existing CN and Global GitHub Actions secrets.

---

### Task 1: Device probe script

**Files:**
- Create: `scripts/garmin/garmin_health_device_probe.py`

**Interfaces:**
- Consumes: `GarminClient(email, password, auth_domain, newest_num)` and `connectapi(path=...)`
- Produces: console-only summarized device metadata; exit 0 on successful requests, non-zero on authentication/request failure.

- [ ] Add helpers that recursively redact keys containing `serial`, `deviceId`, `unitId`, `uuid`, or `registrationId`.
- [ ] Read `/device-service/deviceregistration/devices`, `/web-gateway/device-info/primary-training-device`, and `/device-service/deviceservice/mylastused`.
- [ ] Print region label plus compact JSON summaries.
- [ ] Verify locally by syntax/import inspection.

### Task 2: Isolated GitHub Actions probe

**Files:**
- Create: `.github/workflows/probe-garmin-health-devices.yml`

**Interfaces:**
- CN step uses `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `GARMIN_AUTH_DOMAIN`.
- Global step uses `GARMIN_GLOBAL_EMAIL`, `GARMIN_GLOBAL_PASSWORD` and an empty auth domain.

- [ ] Install current repository dependencies.
- [ ] Run CN probe in one Python process.
- [ ] Run Global probe in a separate Python process.
- [ ] Inspect logs for device presence and endpoint failures.
- [ ] Do not merge this probe workflow into `master`; keep it on the isolated branch unless the user later requests otherwise.
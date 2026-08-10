# Garmin Global Live Upload Test Plan

**Goal:** Verify whether the existing Garmin credentials can upload the latest Garmin CN activity to Garmin Global from GitHub-hosted Actions.

**Constraints:**
- Do not modify the existing Garmin→COROS production script.
- Reuse existing `GARMIN_EMAIL` and `GARMIN_PASSWORD` secrets for this one-time validation.
- Perform the test only on `feat/garmin-global-sync`.
- Treat either `SUCCESS` or `DUPLICATE_ACTIVITY` as proof that Garmin Global login/upload is reachable.
- Treat 429/login/upload errors as evidence that GitHub-hosted Actions is blocked or incompatible.

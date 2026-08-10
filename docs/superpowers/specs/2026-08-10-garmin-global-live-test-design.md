# Garmin Global Live Upload Test Design

Use the existing Garmin CN credentials only for a one-time live validation on the feature branch. The probe downloads the latest Garmin CN activity, extracts its FIT file, then creates a Garmin Global client by leaving the Garmin auth domain unset and attempts an upload. No existing Garmin→COROS production code is modified. The result is accepted only if Garmin Global returns success or duplicate activity; all other results are treated as failure evidence.

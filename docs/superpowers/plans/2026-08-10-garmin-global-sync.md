# Garmin Global Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在完全保留现有 Garmin CN → COROS 实现的前提下，新增独立 Garmin Global 同步旁路。

**Architecture:** 现有 `garmin_sync_coros.py` 继续下载活动 ZIP 并上传 COROS。新增 `garmin_sync_global.py` 在后置独立 workflow step 中扫描本次运行产生的 `garmin-fit/*.zip`，提取 FIT，调用现有 `GarminClient.upload_activity()` 上传 Garmin Global；Global step 失败不影响 COROS。

**Tech Stack:** Python 3.10, garth 0.4.38, GitHub Actions, unittest/pytest-compatible tests

## Global Constraints

- 不修改 `scripts/garmin/garmin_sync_coros.py`。
- 不修改现有 COROS 上传逻辑、Garmin CN 下载逻辑和数据库状态逻辑。
- Global 使用 `GARMIN_GLOBAL_EMAIL`、`GARMIN_GLOBAL_PASSWORD`。
- Global workflow step 必须 `continue-on-error: true`。
- 不引入 DailySync 整套依赖。

---

### Task 1: Global sync helper tests

**Files:**
- Create: `tests/test_garmin_sync_global.py`
- Create: `.github/workflows/test-garmin-global.yml`

**Interfaces:**
- Consumes: standard-library `zipfile`, temp directories
- Produces: behavioral contract for `extract_fit_files(zip_path, output_dir)` and `sync_zip_files(zip_dir, uploader)`

- [ ] **Step 1:** Add tests that require FIT extraction to ignore non-FIT members and preserve multiple FIT files.
- [ ] **Step 2:** Add tests that require `SUCCESS` and `DUPLICATE_ACTIVITY` to count as successful outcomes while upload exceptions are isolated per file.
- [ ] **Step 3:** Add branch-only test workflow running `python -m unittest discover -s tests -v` on pushes to `feat/garmin-global-sync`.
- [ ] **Step 4:** Push tests before production module and confirm RED because `scripts.garmin.garmin_sync_global` does not exist.

### Task 2: Garmin Global sidecar module

**Files:**
- Create: `scripts/garmin/garmin_sync_global.py`

**Interfaces:**
- Consumes: `GARMIN_FIT_DIR`, existing `GarminClient`, `GARMIN_GLOBAL_EMAIL`, `GARMIN_GLOBAL_PASSWORD`
- Produces: `extract_fit_files(zip_path, output_dir) -> list[str]`, `sync_zip_files(zip_dir, uploader) -> dict`, CLI entrypoint

- [ ] **Step 1:** Implement FIT extraction using only Python standard library.
- [ ] **Step 2:** Implement per-file upload result handling; treat `SUCCESS` and `DUPLICATE_ACTIVITY` as non-errors.
- [ ] **Step 3:** Implement CLI credential validation and instantiate existing `GarminClient(email, password, '', 1)` so default domain is Garmin Global.
- [ ] **Step 4:** Run branch test workflow and confirm GREEN.

### Task 3: Workflow integration

**Files:**
- Modify: `.github/workflows/garmin-sync-coros.yml`

**Interfaces:**
- Consumes: repository secrets `GARMIN_GLOBAL_EMAIL`, `GARMIN_GLOBAL_PASSWORD`
- Produces: independent post-COROS Global sync step

- [ ] **Step 1:** Add Global secret mappings to `env` without changing existing secret mappings.
- [ ] **Step 2:** Leave existing `Run Garmin Sync` step byte-for-byte unchanged.
- [ ] **Step 3:** Add `Run Garmin Global Sync` immediately afterward with `continue-on-error: true` and command `python scripts/garmin/garmin_sync_global.py`.
- [ ] **Step 4:** Fetch final workflow and verify original COROS command/structure remains intact.

### Task 4: Real upload verification

**Files:** none

- [ ] **Step 1:** Confirm repository secrets `GARMIN_GLOBAL_EMAIL` and `GARMIN_GLOBAL_PASSWORD` exist (values never printed).
- [ ] **Step 2:** Run `workflow_dispatch` for the feature branch or merged workflow.
- [ ] **Step 3:** Inspect Global step result. A normal upload or duplicate result proves GitHub-hosted runner can reach Garmin Global; 429/login errors are recorded as the exact next engineering problem without changing the COROS path.

# Garmin Global Sync Design

## Goal

在不修改现有 Garmin 中国区 → COROS 同步实现的前提下，新增一个独立旁路模块，把现有流程下载得到的 Garmin 活动文件同步到 Garmin Global。

## Hard constraints

- 不修改 `scripts/garmin/garmin_sync_coros.py`。
- 不修改现有 COROS 上传逻辑、Garmin CN 下载逻辑和现有数据库状态逻辑。
- Garmin Global 使用独立凭据：`GARMIN_GLOBAL_EMAIL`、`GARMIN_GLOBAL_PASSWORD`。
- Garmin Global 同步失败不能影响现有 Garmin → COROS workflow 的成功执行。
- 优先复用仓库现有 `GarminClient.upload_activity()` 能力，不引入完整 DailySync。

## Architecture

现有链路保持不变：

`Garmin CN → 下载活动 ZIP → COROS`

新增旁路：

`现有 garmin-fit ZIP → 解压 FIT → Garmin Global`

新增独立脚本 `scripts/garmin/garmin_sync_global.py`。该脚本扫描 `GARMIN_FIT_DIR` 下现有 `.zip`，解压其中 `.fit` 文件到临时目录，并用 Garmin Global 账号上传。

现有 `.github/workflows/garmin-sync-coros.yml` 仅新增 Global 凭据环境变量和一个独立 step；原来的 `Run Garmin Sync` step 内容保持不变。Global step 使用 `continue-on-error: true`，确保 Global 侧登录、429、上传异常都不会破坏 COROS 链路。

## Data flow

1. 现有 `garmin_sync_coros.py` 正常运行并下载 ZIP 到 `garmin-fit/`。
2. COROS 同步按原逻辑完成。
3. 新的 `garmin_sync_global.py` 扫描 `garmin-fit/*.zip`。
4. 每个 ZIP 中找到 `.fit` 文件并解压到临时目录。
5. 新建配置为 Global 域的 `GarminClient`，使用 `GARMIN_GLOBAL_EMAIL` / `GARMIN_GLOBAL_PASSWORD` 登录。
6. 调用现有 `upload_activity(fit_path)`。
7. `SUCCESS` 记录成功；`DUPLICATE_ACTIVITY` 视为幂等成功；其他结果记录失败但继续处理其他文件。

## Error handling

- 缺少 Global 凭据：脚本明确报错并以非零状态退出；workflow 因 `continue-on-error: true` 不影响 COROS。
- ZIP 无 FIT：记录并跳过。
- Garmin Global 429 / 登录失败 / 上传异常：记录错误，不修改 COROS 数据库同步状态。
- 重复活动：按 `DUPLICATE_ACTIVITY` 处理，不视为故障。

## Test strategy

- 单元测试覆盖 ZIP 中 FIT 发现/解压。
- 单元测试 mock `GarminClient.upload_activity()`，覆盖 SUCCESS、DUPLICATE_ACTIVITY、失败三种结果。
- Workflow 结构检查：确认原 `Run Garmin Sync` 命令未变化，Global 是后置独立 step，且 `continue-on-error: true`。
- 最终通过手动 workflow_dispatch 做真实 Global 上传验证；若真实环境返回 429，再单独处理 Global runner，不迁移原 COROS 链路。

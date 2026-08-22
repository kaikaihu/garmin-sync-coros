# 项目状态

更新日期：2026-08-22

## 已投入运行

### Garmin 中国区活动 → COROS

- 默认分支上的原有生产链路继续运行。
- `db/garmin.db` 保存同步状态，不能无证据删除。
- 这条链路不依赖 Garmin 国际区健康研究。

### Garmin 中国区活动 → Garmin 国际区

- 使用独立工作流 `.github/workflows/garmin-sync-global.yml` 和 Python 3.12 环境。
- 同步状态保存在 `db/garmin_global_state.json`。
- 与 COROS 主链路分开调度，避免登录失败或状态提交相互影响。

### Garmin 中国区健康数据 → Intervals.icu

- 默认分支每天北京时间 10:15 自动运行，覆盖最近 3 天。
- 写入睡眠、HRV、训练准备度、静息心率和步数等语义一致的 Wellness 字段。
- 2026-06-01 至 2026-08-22 已补齐 83 个日期并完成官方 API 回读：无缺日、无重复。
- 2026-07-10 的 HRV、睡眠评分和睡眠时长在 Garmin 中国区源端即缺失，不属于上传失败。

### Garmin 中国区历史活动 → Intervals.icu

- 2026-01-01 至 2026-08-22 已完成审计型补传。
- 最终 Garmin 与 Intervals.icu 均为 218 条，一对一匹配 218 条，缺失 0。
- 工具仍保留为手动入口，默认只读，并支持 `max_upload` 小批量 canary。

## 仍在研究

### Garmin 中国区健康数据 → Garmin 国际区

已经确认：

- Garmin 官方健康导出包含 Wellness、Sleep、HRV 和 Metrics FIT，而不是普通活动 FIT。
- Garmin 国际区账号已有主可穿戴设备身份。
- 持久化 garth session 可以避开每次 GitHub Runner 密码登录造成的部分 429 风险。

尚未确认：

- Garmin Global 接受设备健康 FIT 的实际 ingest endpoint。
- 设备认证、序列号和服务端校验要求。
- 一个可以最小化、验证并回滚的公开写入方法。

因此当前明确边界是：活动 FIT 可上传，不代表健康 FIT 可写入；没有经过观察和验证的私有设备同步协议不得猜测调用。

## 分支职责

| 分支 | 职责 |
|---|---|
| `master` | 生产调度与同步状态 |
| `research/garmin-cn-global-health` | 健康同步实现、测试、证据和只读探测 |
| `probe/garmin-health-devices` | 早期只读设备探测历史分支 |

默认分支的健康同步和历史活动补传工作流会固定检出已经验证的研究提交，避免研究分支后续变化自动进入生产。

## GitHub Actions 清理记录

2026-08-22 已禁用 8 个历史测试或只读探测工作流：

- `full-cn-coros-global-test`
- `garmin-global-live-test`
- `probe-garmin-health-devices`
- `refactor-garmin-global-ci`
- `test-garmin-global-429`
- `test-garmin-global`
- `test-global-mapped-secrets`
- `test-global-upload-live`

当前保留 4 个启用工作流：

- `garmin-sync-coros`
- `garmin-sync-global`
- `sync-garmin-cn-health-to-intervals`
- `backfill-garmin-cn-activities-to-intervals`

旧版反向同步 `coros-sync-garmin` 继续保持手动禁用。GitHub 的历史运行记录和研究分支文件没有删除，以便追溯；所有禁用操作均可恢复。

## 维护风险

- Garmin Connect 使用私有 API，接口和登录策略可能变化。
- Garmin Global 密码 OAuth 容易在 `oauth/preauthorized` 阶段触发 HTTP 429；不要连续重试。
- 默认分支存在自动生成的同步状态提交。人工修改前先获取远端最新状态，提交时禁止 force push。
- 旧版工作流与研究工具的 Python 依赖不同，不应在一次“整理”中同时升级。
- 任何批量写入必须先只读比对，写后从目标端回读，而不是只看 Action 是否绿色。

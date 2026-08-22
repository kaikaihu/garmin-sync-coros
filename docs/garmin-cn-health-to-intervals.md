# Garmin 中国区健康数据 → Intervals.icu

## 当前实现

实验分支：`research/garmin-cn-global-health`

独立工作流：`.github/workflows/sync-garmin-cn-health-to-intervals.yml`

- 不修改现有活动同步工作流。
- 每天北京时间 10:15 重新读取并覆盖最近 3 天，补偿 Garmin 延迟结算或偶发失败。
- 使用 Intervals.icu `PUT /api/v1/athlete/0/wellness-bulk`，同一日期重复运行是幂等的。
- 手动触发默认 `dry_run=true`；日志只显示日期和字段名，不显示健康数值或 token。
- 实验分支修改相关代码时会自动触发只读 dry-run；`push` 事件永远不会上传。
- 默认分支只放置调度入口；运行时固定检出已验证的研究提交 `1cf3fb235f10d36c7d66ad789d059756389ae9f2`，避免把其他实验代码并入生产分支。
- 不把原始健康 JSON、FIT 或 Intervals API key 写进 Git 仓库和 Action artifact。

## 字段映射

| Intervals.icu | Garmin 中国区来源 | 单位/语义 |
|---|---|---|
| `restingHR` | Daily Summary `restingHeartRate` | bpm |
| `hrv` | HRV `hrvSummary.lastNightAvg`，缺失时用 Sleep `avgSleepHRV` | ms |
| `sleepSecs` | Sleep `sleepTimeSeconds` | 秒 |
| `sleepScore` | Sleep `sleepScores.overall.value` | 0–100 |
| `avgSleepingHR` | Sleep `averageSleepHeartRate`/`avgSleepHeartRate`（设备返回时） | bpm |
| `spO2` | Sleep `avgSpO2` | 百分比 |
| `readiness` | Training Readiness 的起床后分数 | 0–100 |
| `steps` | Daily Summary `totalSteps` | 步 |
| `respiration` | Sleep `avgRespirationValue` | 次/分钟 |

没有直接写入：Garmin `averageStressLevel` 和 Body Battery。Intervals 的 `stress` 是主观 1–4 量表，并不等同 Garmin 的 0–100 压力；Intervals 当前也没有 Body Battery 原生字段。强行换算会污染训练判断。

任一来源缺失时，该字段会从请求体省略，因此不会用 `null` 清掉 Intervals 中已有的数据。

## GitHub Secrets

必需：

- `INTERVALS_API_KEY`：Intervals.icu Settings 页面底部的个人 API key。
- Garmin 认证二选一：
  - 推荐 `GARMIN_CN_GARTH_TOKEN`；或
  - 现有 `GARMIN_EMAIL` + `GARMIN_PASSWORD` 作为后备。

可选：

- `GARMIN_DISPLAY_NAME`：只有 token 无法恢复 profile/display name 时才需要。

在可信的本地 Mac 上一次性生成中国区 session：

```bash
cd "/Users/hukai/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/garmin-sync-coros"
python3 -m scripts.garmin.garmin_cn_token_bootstrap
```

把输出完整保存成 GitHub Actions secret `GARMIN_CN_GARTH_TOKEN`。不要把输出粘贴到聊天、Issue、日志或仓库文件。

## 上线顺序

1. 在实验分支手动运行一次，保留 `dry_run=true`、`days=1`。
2. 检查 Action 只显示 `validated YYYY-MM-DD: 字段名...`，且无敏感值。
3. 再手动运行同一天，设置 `dry_run=false`，然后从 Intervals.icu UI/API 读回核对。
4. 重复上传同一天，确认值不重复而是原位更新。
5. 验证后仅把这套新增文件合入默认分支；GitHub 的 `schedule` 只会执行默认分支中的工作流。

## 已确认的公开接口依据

- [Intervals.icu 当前 OpenAPI](https://intervals.icu/api/v1/docs)：`Wellness` schema 和 `wellness-bulk` PUT。
- [Intervals.icu API Integration Cookbook](https://forum.intervals.icu/t/intervals-icu-api-integration-cookbook/80090)：个人 API key Basic Auth 与批量 Wellness 示例。
- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)：Garmin Connect 只读 Daily Summary、Sleep、HRV、Training Readiness endpoint 和响应字段。

## 已知边界

- Garmin Connect 私有 API 随时可能变化。
- `garth==0.4.38` 已固定在本仓库；优先复用 session，避免每次 GitHub Runner 都走密码登录。
- 若 Garmin 使现有 session 和密码登录同时失效，Action 会明确失败，不会向 Intervals 写入空值。届时需要人工重新取得 session，或迁移到仍能认证的新客户端。
- 定时入口已通过提交 `da518d4` 部署到默认分支；它只新增一个工作流文件，现有活动同步工作流未修改。实现仍隔离在研究分支，并由完整提交 SHA 固定。

## GitHub Runner 验证证据（2026-08-22）

- 第一次 push dry-run 暴露两个实现问题：push 事件被表达式误判为上传模式，以及 garth 的 `userName` 被误当作 Garmin `displayName`。Garmin 首个健康请求返回 403，且 `INTERVALS_API_KEY` 未配置，因此没有向 Intervals 写入。随后已把 push 条件改成永远只读、改用 profile `displayName`，并让 CLI 错误只显示异常类型，避免在公开日志中继续展开 Garmin URL/标识。
- [第二次 GitHub Actions dry-run](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32547808524) 成功。Runner 日志确认 `SYNC_UPLOAD=false`，并连续验证 2026-08-20 至 2026-08-22 三天的 `hrv、readiness、restingHR、sleepScore、sleepSecs、steps`；日志末尾明确为 `Intervals.icu was not modified`。
- [第一次单日写入](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32548356259) 在 Intervals 认证阶段失败。Garmin 读取和 payload 验证均成功，但错误取用了设置页的短显示值而非密钥弹窗中的完整值，Intervals 返回 HTTP 401，因此没有写入。
- 改用弹窗完整密钥后，只读认证探测返回 HTTP 200。[第二次单日写入](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32548514863) 成功，日志确认向 Intervals 上传 1 条 2026-08-21 Wellness 记录。
- 写入后通过 `GET /api/v1/athlete/0/wellness/2026-08-21` 回读，确认 `restingHR、hrv、sleepSecs、sleepScore、readiness、steps` 六个字段均为非空。回读过程不在日志中输出具体健康数值。
- [默认分支调度入口 dry-run](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32548645382) 成功：固定检出已验证研究提交，测试通过，`SYNC_UPLOAD=false`，并明确记录 `Intervals.icu was not modified`。
- 至此已形成可复现链路：GitHub Runner 读取 Garmin 中国区健康数据，转换为 Intervals Wellness payload，使用加密 Secret 写入并通过 API 回读验证；默认分支每日北京时间 10:15 自动重跑最近 3 天。

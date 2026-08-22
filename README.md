# Garmin 数据同步自动化

这个仓库维护个人 Garmin、COROS 与 Intervals.icu 之间的活动和健康数据同步。当前重点是稳定运行已有生产链路，同时把高风险实验保留在独立研究分支。

## 当前数据链路

| 数据链路 | 类型 | 入口 | 状态 |
|---|---|---|---|
| Garmin 中国区活动 → COROS | 定时生产同步 | `.github/workflows/garmin-sync-coros.yml` | 运行中 |
| Garmin 中国区活动 → Garmin 国际区 | 定时生产旁路 | `.github/workflows/garmin-sync-global.yml` | 运行中；与 COROS 链路隔离 |
| COROS 活动 → Garmin | 旧版反向同步 | `.github/workflows/coros-sync-garmin.yml` | 保留，按需使用 |
| Garmin 中国区健康数据 → Intervals.icu | 每日生产同步 | `.github/workflows/sync-garmin-cn-health-to-intervals.yml` | 每天北京时间 10:15 重跑最近 3 天 |
| Garmin 中国区历史活动 → Intervals.icu | 手动补传 | `.github/workflows/backfill-garmin-cn-activities-to-intervals.yml` | 仅手动运行，默认先只读比对 |
| Garmin 中国区健康数据 → Garmin 国际区 | 隔离研究 | `research/garmin-cn-global-health` | 尚无已验证的公开写入链路 |

“活动同步到 Garmin 国际区”和“健康数据写入 Garmin 国际区”是两件不同的事。前者已经可用；后者仍受 Garmin 私有设备同步协议限制，不能把活动 FIT 上传成功等同于 Wellness 写入成功。

## 安全边界

- 默认分支 `master` 承载生产调度；健康写入和历史补传入口固定检出已验证的研究提交。
- 研究代码位于 `research/garmin-cn-global-health`，只读探测优先。
- 不在仓库、Issue、Actions 日志或聊天中保存 Garmin token、密码和 Intervals API key。
- `db/garmin.db` 与 `db/garmin_global_state.json` 是同步状态，不要把删除它们作为常规修复手段。
- 历史补传先使用只读模式和小批量 canary；不做按日期范围的盲目删除或覆盖。
- Garmin 登录出现 HTTP 429 时停止重复密码登录，优先恢复或更新持久化 session。

## GitHub Secrets

| Secret | 用途 |
|---|---|
| `GARMIN_EMAIL` / `GARMIN_PASSWORD` | Garmin 中国区登录后备凭据 |
| `GARMIN_AUTH_DOMAIN` | Garmin 区域，当前中国区使用 `CN` |
| `GARMIN_CN_GARTH_TOKEN` | Garmin 中国区持久化 session，健康同步优先使用 |
| `GARMIN_DISPLAY_NAME` | 仅在 session 无法恢复 profile 时使用 |
| `GARMIN_GLOBAL_EMAIL` / `GARMIN_GLOBAL_PASSWORD` | Garmin 国际区活动旁路 |
| `COROS_EMAIL` / `COROS_PASSWORD` | COROS 同步 |
| `INTERVALS_API_KEY` | Intervals.icu 健康同步与活动补传 |
| `GARMIN_NEWEST_NUM` | 旧版活动同步读取数量设置 |

研究分支的只读设备探测另使用 `GARMIN_GLOBAL_GARTH_TOKEN`，它不应回退到 GitHub Runner 上的重复密码登录。

## 日常操作

1. 在 GitHub Actions 查看对应工作流，不要仅凭绿色状态判断数据完整；同时检查日志中的处理数量和目标端回读结果。
2. 手动运行健康同步时，默认保持 `dry_run=true`。确认日期和字段后再执行写入。
3. 手动运行活动补传时，先保持 `upload=false`；实际写入先设置较小的 `max_upload`。
4. 修改同步代码时只在研究分支验证。生产入口只能固定到已经测试并回读确认的完整提交 SHA。
5. 涉及数据库状态的恢复前先保存证据并备份，不 force push，不覆盖远端较新的状态提交。

## 项目结构

```text
.github/workflows/     GitHub Actions 调度与手动入口
scripts/garmin/        Garmin 中国区及研究脚本
scripts/garmin_global/ Garmin 国际区活动旁路（默认分支）
scripts/coros/         COROS 同步
db/                    生产同步状态
docs/                  项目状态、证据与历史说明
tests/                 研究分支健康/补传测试
doc/                   上游旧版配置截图
```

## 文档入口

- [当前项目状态](docs/PROJECT_STATUS.md)
- [文档索引](docs/README.md)
- [上游旧版 Garmin ↔ COROS 配置教程](docs/legacy-upstream-garmin-coros-setup.md)

详细的健康同步、活动补传证据和 Garmin 国际区健康写入边界保留在研究分支，文档索引中提供了直接链接。

## 致谢

Garmin 模块最初来自 [yihong0618/running_page](https://github.com/yihong0618/running_page)，原始项目为 [XiaoSiHwang/garmin-sync-coros](https://github.com/XiaoSiHwang/garmin-sync-coros)。本仓库在此基础上增加了隔离的 Garmin Global 活动旁路、Intervals.icu 健康同步与审计型补传工具。

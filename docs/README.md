# 文档索引

## 当前入口

- [项目状态](PROJECT_STATUS.md)：生产链路、完成事项、研究边界和维护注意事项。
- [仓库首页](../README.md)：项目用途、Secrets、日常操作和目录结构。
- [上游旧版配置教程](legacy-upstream-garmin-coros-setup.md)：早期 Garmin ↔ COROS 配置截图，仅作历史参考。

## 已验证实现与证据

以下文档目前保留在隔离研究分支，避免把实验实现直接混入默认分支：

- [Garmin 中国区健康数据 → Intervals.icu](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/garmin-cn-health-to-intervals.md)
- [Garmin 中国区历史活动 → Intervals.icu 补传](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/garmin-cn-activities-to-intervals-backfill.md)
- [Garmin 中国区 → 国际区健康同步研究](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/garmin-cn-global-health-research.md)

## 历史设计资料

- [Garmin Global 活动旁路设计](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/superpowers/specs/2026-08-10-garmin-global-sync-design.md)
- [Garmin 健康设备只读探测设计](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/superpowers/specs/2026-08-10-garmin-health-device-probe-design.md)
- [Garmin 健康设备探测实施计划](https://github.com/kaikaihu/garmin-sync-coros/blob/research/garmin-cn-global-health/docs/superpowers/plans/2026-08-10-garmin-health-device-probe.md)

## 文档维护规则

- README 只保留稳定入口和操作边界，不堆积逐次实验日志。
- 可复现证据写进对应专题文档，包含日期、工作流运行链接、结果和失败点。
- 未验证的推测必须明确标注，不得写成已实现能力。
- Secrets、token、密码、原始健康 JSON 和临时 FIT 不进入 Git。

# Garmin 中国区历史活动 → Intervals.icu 补传

## 目标与范围

- 时间范围：2026-01-01 至运行当天（Asia/Shanghai）。
- 只补传 Garmin 中国区存在、Intervals.icu 缺失的活动。
- 不删除或覆盖 Intervals.icu 中已有活动。
- 研究实现保留在 `research/garmin-cn-global-health`；生产活动同步工作流不修改。

## 对账与去重

两个账户中的活动 ID 不具备跨平台一致性，因此不能直接按 ID 判断重复。工具为每条活动建立指纹，并执行一对一匹配：

- 本地开始时间误差不超过 120 秒；
- 运动类型族一致（跑步、骑行、步行、徒步、力量、游泳等）；
- 时长误差不超过 120 秒或 5%；
- 距离误差不超过 250 米或 3%；
- 一条 Intervals 活动最多匹配一条 Garmin 活动。

只有没有任何合格匹配项的 Garmin 活动才进入补传列表。上传时使用 Garmin 官方活动下载接口取得原始 ZIP，再通过 Intervals.icu 官方 `POST /api/v1/athlete/0/activities` multipart 接口上传。临时 ZIP 只存在于 Runner 临时目录，任务结束自动删除。

## 安全控制

- 研究分支 push 永远是 `UPLOAD=false`，只读对账。
- 实际补传只允许默认分支上的 `workflow_dispatch`，且必须显式设置 `upload=true`。
- `max_upload` 可限制单次写入数量；首轮必须设为 `1` 做金丝雀验证。
- API key 和 Garmin 凭据只来自 GitHub Actions Secrets，不写日志、代码或 artifact。
- CLI 失败日志只报告异常类型，不输出响应体、认证信息或活动 ID。
- 上传活动设置 `external_id=garmin-cn-<activityId>`，便于后续识别；工具本身没有删除能力。

## 只读验证证据（2026-08-22）

最终固定研究提交：`7d74fe8d0ec802e69ca61b62145e6a98096ba28d`

[GitHub Actions dry-run 32550809432](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32550809432)：

- 14 项活动补传与认证测试通过；
- `UPLOAD=false`；
- Garmin 中国区活动 218 条；
- Intervals.icu 活动 147 条；
- 已有 147 条全部一对一匹配；
- 缺失 71 条；
- 月份分布：1 月 10、4 月 5、5 月 29、6 月 26、7 月 1；
- 类型分布：跑步 60、骑行 3、步行 6、徒步 1、力量 1；
- 日志明确为 `Intervals.icu was not modified`。

## 写入与终审证据

用户于 2026-08-22 明确批准补传 71 条运动。仅手动触发的默认分支入口由提交 `751b02a` 新增，现有生产活动同步文件未修改；入口固定检出研究提交 `7d74fe8d0ec802e69ca61b62145e6a98096ba28d`。

1. [金丝雀上传 32550936840](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32550936840)：`upload=true, max_upload=1`。上传 1 条并回读成功，缺失数由 71 降至 70。
2. [剩余 70 条补传 32551005621](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32551005621)：运行前 Intervals 为 148 条、匹配 148 条、缺失 70 条；70/70 均上传成功，任务内回读缺失为 0。
3. [独立只读终审 32551312865](https://github.com/kaikaihu/garmin-sync-coros/actions/runs/32551312865)：重新从两端读取完整范围，14 项测试通过，`UPLOAD=false`；Garmin 218、Intervals 218、一对一匹配 218、缺失 0，并明确记录 `Intervals.icu was not modified`。

最终两端总数相等，且匹配算法不允许一条 Intervals 活动匹配多条 Garmin 活动，因此 2026-01-01 至 2026-08-22 范围内没有未补活动，也没有由本次补传造成的额外重复活动。

若未来需要回滚，依据本轮新增活动的 `source=UPLOAD` 与 `external_id=garmin-cn-*` 精确识别，再由用户批准后删除；不得按日期范围批量删除。

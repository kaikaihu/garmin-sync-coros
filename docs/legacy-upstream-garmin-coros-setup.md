# 上游旧版 Garmin ↔ COROS 配置教程

这份教程来自仓库早期版本，仅保留上游配置截图和历史操作路径。当前仓库已经增加 Garmin Global 与 Intervals.icu 链路，请以根目录 [README](../README.md) 和 [项目状态](PROJECT_STATUS.md) 为准。

> 注意：旧教程曾建议同步异常时直接删除 `db/garmin.db`。该文件现在属于生产同步状态，除非已经完成证据核对和备份，否则不要删除。

## 上游注意事项

由于 COROS 平台只允许单设备登录，同步期间打开 COROS 网页可能使同步失败。

## 旧版参数

| 参数名 | 说明 |
|---|---|
| `GARMIN_EMAIL` | Garmin 登录邮箱 |
| `GARMIN_PASSWORD` | Garmin 登录密码 |
| `GARMIN_AUTH_DOMAIN` | 国际区为 `COM`，中国区为 `CN` |
| `GARMIN_NEWEST_NUM` | 最新记录条数，默认 0 |
| `COROS_EMAIL` | COROS 登录邮箱 |
| `COROS_PASSWORD` | COROS 登录密码 |

## GitHub Secrets 配置截图

打开仓库 Settings：

![打开 Settings](../doc/3451692931372_.pic.jpg)

进入 Secrets and variables：

![Secrets and variables](../doc/3461692931472_.pic.jpg)

新增 Secret：

![填写 Secret](../doc/3471692931624_.pic.jpg)

## Actions 权限截图

进入 Settings → Actions → General：

![配置 Workflow 权限](../doc/3481692931856_.pic.jpg)

## 旧版工作流配置截图

旧版教程要求在 `garmin-sync-coros.yml` 中填写 GitHub 用户名和邮箱：

![修改 GitHub 身份](../doc/3491692932110_.pic.jpg)

![提交修改](../doc/3501692932345_.pic.jpg)

## 旧版 Fork 与数据库操作截图

以下截图仅供识别旧操作界面，不构成当前恢复建议：

![同步 Fork](../doc/image.png)

![数据库操作 1](../doc/image5.png)

![数据库操作 2](../doc/image-1.png)

![数据库操作 3](../doc/image-2.png)

![数据库操作 4](../doc/image-3.png)

![数据库操作 5](../doc/image-4.png)

原始项目：[XiaoSiHwang/garmin-sync-coros](https://github.com/XiaoSiHwang/garmin-sync-coros)。Garmin 模块来源：[yihong0618/running_page](https://github.com/yihong0618/running_page)。

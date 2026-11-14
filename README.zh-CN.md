# crossover-parallels-trial-reset

在 macOS 上于启动前重置 **CrossOver** 与 **Parallels Desktop** 的试用状态，带通用适配器层、
launchd 监视器与可直接被 agent 执行的 skill。

> `pip install -e .` → `trialreset`

在 macOS 应用**启动之前**重置它的本地试用/许可状态，配一个 launchd 监视器兜底，再加可选的
账号/许可域名阻断。

内置适配器：**CrossOver**、**Parallels Desktop**。新增应用只需要写一个 spec 文件。

## 原理

```
启动器（可选）                launchd 监视器（可选）
      │ 启动前重置                  │ 应用写偏好后重置
      ▼                            ▼
            trialreset reset <app>
      ┌──────────────┬───────────────┬────────────────┐
      │ 删/改偏好键   │ 结束进程       │ 清缓存          │ 阻断域名
      └──────────────┴───────────────┴────────────────┘
```

覆盖两种试用模型：

| 模型 | 例子 | 重置动作 |
| --- | --- | --- |
| 时间戳 | CrossOver（`FirstRunDate`、`SULastCheckTime`） | 日期往前挪 N 小时 |
| 许可块 | Parallels（`License.*`、`WiConfig`） | 删键、清缓存、重启服务 |

细节看 [docs/how-it-works.md](docs/how-it-works.md)，坑看 [docs/pitfalls.md](docs/pitfalls.md)。

## 安装

```bash
git clone https://github.com/yokeman-young/crossover-parallels-trial-reset.git
cd trial-reset-kit
pip install -e .
trialreset --json doctor
```

## 用法

```bash
trialreset list
trialreset check parallels
trialreset reset parallels --dry-run
trialreset reset parallels
trialreset launch parallels
trialreset watch install parallels
trialreset block parallels            # 需要 sudo
```

所有子命令支持 `--json`，退出码：`0` 成功 / `1` 校验失败 / `2` 应用缺失。

## 新增应用

在 `trialreset/adapters/` 加一个 `AppSpec`（见 [docs/adding-an-app.md](docs/adding-an-app.md)），
注册到 `__init__.py`，立即出现在 `trialreset list` 里。

## Agent skill

`skills/trial-reset/SKILL.md` 是可直接安装的 skill（frontmatter + 步骤 + 断言表 + 失败处理）。

```bash
cp -R skills/trial-reset ~/.claude/skills/    # 或 ~/.dsh/skills/
```

## 局限

- Parallels 的试用可能由账号/服务端判定，阻断只能让客户端拿不到结论，不改变厂商已知信息。
- 删许可键同样会删掉**正版激活**；购买后请 `touch ~/.trialreset/<app>/disabled`。
- hosts 只能拦域名解析，硬编码 IP 需要 PF 规则。
- 仅 macOS；适配器层刻意做薄，便于以后移植。

MIT License。

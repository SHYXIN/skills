---
name: wizard-wx
description: 生成一个互动式 bash 向导，一步步带着人完成只有人能做的操作。用于 provision 基础设施、配置凭据或 CI secret、走陌生的第三方后台、或跑一次性的迁移/切换。agent 自己能做的步骤不要用它。
---

# 向导（Wizard）

**wizard** 是一个 bash 脚本，它一步步带着人，走完一个手工流程——这个流程亲手做很繁琐，每次都重新给 AI 讲一遍也很烦。它帮你打开每个 URL、说清要点击和复制什么、把取到的值写到该写的地方（`.env`、GitHub secret）、在每一步确认、并显示还剩几步。它可以配置第三方服务、跑一次性迁移、或把项目从一个状态切到另一个状态。

顺滑的体验已经由 [template.sh](template.sh) 解决好了——分阶段进度、确认闸门、跨平台打开 URL（含 WSL）、隐藏式 secret 输入、幂等的 `.env` 更新、`gh secret` / `gh variable` 写入，以及收尾总结。**你（agent）的工作只是界定流程、写出各个 stage。** `STAGES` 标记以上的库在每个 wizard 里都一模一样；保持一致就是意义所在——不要手改它。

wizard 默认是临时的——为单次运行而生，存到 scratch 或 `scripts/` 路径，用完即删。只有用户想要一条可复用的安装路径、并希望它留在仓库里时，才提交它。

## 流程

### 1. 界定流程（Scope the procedure）

理清人必须亲手做的每一步，以及沿途要取到的每一个值。先读仓库——别冷着问：

- 配置类：`.env`、`.env.example`、`.env.*`、`README`、`docker-compose*`、框架配置，以及 `.github/workflows/*`（每一个 `secrets.*` / `vars.*` 引用，都是 wizard 要产出的值）。
- 迁移 / 切换类：当前状态、目标状态，以及两者之间不可逆的动作。

然后给用户看一份有序的 stage 清单，以及每个 stage 产出的值，并确认——用户可以增、删、或重排。

**完成标准：** 每个 stage 都按顺序排列好；对每个取到的值，你都知道 (a) 人从哪里拿到它，(b) 它写到哪里（`.env`、GitHub secret、两者、还是哪都不写——有些 stage 是纯动作），(c) 它是 secret（隐藏输入）还是公开。

### 2. 画出每个 stage 的路线（Map each stage's journey）

对每个 stage，写出人要走的确切路径：打开哪个 URL、在那里做什么、值显示在哪里、填进哪个变量——比如「Dashboard → Developers → API keys → Reveal test key → 复制」。凡是你确实不知道当前 UI 或确切命令的地方，如实说明并向用户确认或查文档——**不要编造可能不存在的步骤**。

**完成标准：** 每个 stage 都能追溯到陌生人可照做的明确指令。

### 3. 写 wizard（Author the wizard）

把 `template.sh` 复制到目标路径。把示例 stage 换成你的每一步，按依赖顺序各写一个 `stage`。用库里的辅助函数——`stage`、`say` / `step`、`open_url`、`ask` / `ask_secret`、`write_env`、`set_secret` / `set_var`、`pause` / `confirm`——并把 `TOTAL_STAGES` 设成你写的 stage 数量。

守住 template 立下的标杆：要取的值，先 `open_url` 再问；任何 secret 用 `ask_secret`；每个持久化的值都 `write_env`；`set_secret` 只写 CI 真正需要的值；任何不可逆动作前用 `confirm`。每个 `stage` 会清屏，所以屏幕上只留当前这一步——一个 stage 只做一件聚焦的事，别让人需要的东西滚出屏幕。`STAGES` 标记以上的库不要碰。

### 4. 验证与交付（Verify and hand off）

- `bash -n <script>`；如可用则跑 `shellcheck`。
- `chmod +x <script>`。
- 不要自己端到端跑——它会开浏览器、卡在人输入上。改为静态追溯：第 1 步里的每个值都被取到、并落到第 1 步说好的地方；每个 `set_secret` 的名字都和 CI 里的 `secrets.*` 引用精确对应。
- 告诉用户怎么运行。如果是可复用的安装路径，提交它并在 README 里链过去，让下一个人跑脚本而不是来问 AI。

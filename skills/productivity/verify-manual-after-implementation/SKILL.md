---
name: verify-manual-after-implementation
description: 在 to-spec -> to-tickets -> implement 或类似实现流程完成后，生成可人工打开网站/API/CLI 执行的验收手册。用于用户要求“生成测试手册”“手动验收”“怎么打开网站测试”“implement 完之后验收”“写一份手动测试指南”“补 dev.sh 后生成验收手册”等场景。会审计当前仓库、必要时创建 scripts/dev.sh，并输出 docs/verification/manual-test-guide.md。
---

# 实现后手动验收手册

为刚完成实现的项目生成一份可执行的手动验收手册。默认输出到：

`docs/verification/manual-test-guide.md`

如果该文件已存在，覆盖更新。不要只给建议；除非用户明确要求只设计，否则直接检查仓库并生成文件。

## 工作流

### 1. 轻量完成度审计

先从当前仓库自动收集事实，不要把能查到的信息再问用户。

优先检查：

- `docs/specs/`、`.scratch/**/issues/`、`issues/`、`tickets/` 中的 spec 和 tickets
- `git status --short`、`git log --oneline -5`、必要时 `git diff --stat`
- `README.md`、`package.json`、`pyproject.toml`、`Makefile`、`docker-compose.yml`、`compose.yaml`
- 前端路由、导航、页面入口、表单和按钮
- 后端 API 路由、健康检查、认证接口、上传/导入/运行类接口
- 测试命令、构建命令、启动命令
- `sample`、`fixture`、`seed`、`demo`、`example`、测试账号、测试 zip 或示例数据

在手册开头写“验收前提与风险”，说明：

- 手册基于哪个工作区状态生成
- 是否有未提交变更
- 是否找到一键启动方式
- 是否找到自动化测试命令
- 是否找到样例数据
- 哪些信息需要人工补充

### 2. 判断是否需要创建 `scripts/dev.sh`

如果仓库已经有可靠的一键启动入口，不要重复创建：

- `scripts/dev.sh`
- `docker-compose.yml` / `compose.yaml`
- `Makefile` 中有 `dev`
- 根 `package.json` 中有可启动全项目的 `dev`
- README 已写明一条命令可启动主要服务

如果没有一键启动入口，但能可靠判断项目启动方式，则创建或更新 `scripts/dev.sh`。

`scripts/dev.sh` 应该保守、可读、可停：

- 不自动安装依赖
- 支持环境变量覆盖端口，如 `API_PORT`、`WEB_PORT`
- 写日志到 `.tmp-logs/`
- 检查端口占用，并让用户确认是否停止已有进程
- `Ctrl+C` 清理由脚本启动的进程
- 只启动能可靠识别的服务
- 无法判断启动方式时，不强行生成脚本，在手册中标记“启动方式待确认”

常见探测规则：

- Docker Compose 项目：优先使用 `docker compose up`
- 全栈 Web 项目：分别启动 API 和 Web
- Vite/React/Vue/Svelte：优先使用对应 `package.json` 的 `dev`
- Next.js：使用 `npm/pnpm/yarn run dev`
- FastAPI：优先使用 `uv run uvicorn <module>:app --reload`，模块名从项目结构判断
- 纯后端：只启动 API
- 纯前端：只启动 Web

### 3. 生成手动验收手册

手册按“用户操作流程”组织，而不是按 ticket 编号组织。最后附 ticket/需求覆盖矩阵。

必须包含这些章节，按项目实际情况删减或改名：

```markdown
# 手动验收手册

## 验收前提与风险

## 1. 自动检查

## 2. 启动服务

## 3. 准备测试数据

## 4. 手动验收流程

## 5. 报告与失败定位

## 6. Ticket/需求覆盖矩阵

## 7. 失败记录模板
```

### 自动检查

列出人工验收前建议先跑的命令，例如：

- 后端测试：`pytest`、`uv run pytest`、`npm run test:api`
- 前端构建：`npm run build`、`pnpm build`
- 类型检查：`tsc`、`npm run typecheck`
- Docker 检查：`docker compose config`

不要把自动测试当成人工验收的替代品。

### 启动服务

优先引用 `scripts/dev.sh`。如果没有生成该脚本，就写清楚现有启动命令。

必须写：

- 命令从哪个目录执行
- 默认 URL 和端口
- 健康检查 URL 或首页 URL
- 日志位置
- 停止服务的方法

默认不自动启动服务。只有用户明确说“帮我跑一下”“打开看看”“验证 URL 可用”时，才启动服务并检查页面/API。

### 准备测试数据

优先引用仓库已有的 sample、fixture、seed、demo、example、测试账号或测试包。

如果没有现成数据，在手册里写“最小测试数据说明”，包括：

- 需要创建哪些账号或角色
- 需要上传哪些文件
- 文件目录结构
- 示例 JSON/Markdown/YAML
- 必填字段
- 成功导入后的可见结果

默认不要新增大量 fixture 文件。只有用户明确要求时才生成样例文件。

### 手动验收流程

每个步骤都必须可直接执行，避免“测试一下是否正常”这种模糊描述。

每个验收项使用这个结构：

```markdown
### 4.x 功能名称

**目的**：

**前置条件**：

**操作**：
1. ...
2. ...
3. ...

**预期结果**：

**通过标准**：

**常见失败原因**：

**失败时记录**：
- 页面截图：
- 浏览器 Console：
- API 响应：
- 后端日志：
- 关联 ticket：
```

对 Web 项目，操作要以“打开/点击/填写/上传/提交/刷新/查看”为主。

对 API 项目，操作要给出 curl 或 Postman 方式，并写明 HTTP 状态码和响应字段。

对 CLI 项目，操作要给出命令、输入文件、输出文件和退出码。

对全栈项目，要覆盖从 UI 操作到后端结果持久化或报告生成的完整链路。

### Ticket/需求覆盖矩阵

从 tickets/spec 推导覆盖关系。格式：

```markdown
| Ticket/需求 | 验收步骤 | 覆盖点 | 状态 |
| --- | --- | --- | --- |
| 01 - ... | 4.1, 4.2 | ... | 待人工验证 |
```

如果找不到 ticket，也可以用功能点、接口、页面或提交摘要替代。

### 失败记录模板

手册末尾必须包含：

```markdown
## 失败记录模板

- 时间：
- 环境：
- 操作步骤：
- 期望结果：
- 实际结果：
- 截图/日志：
- 关联 ticket：
- 初步判断：
- 复现稳定性：
```

## 输出要求

- 使用中文。
- 内容要具体到测试人员可以照着点。
- 先写打开网站/启动系统的主路径，再写边界和失败定位。
- 不修改业务标准答案、剧本、原始需求文档，除非用户明确要求。
- 可以创建或更新 `scripts/dev.sh` 和 `docs/verification/manual-test-guide.md`。
- 生成完成后，在最终回复中列出文件路径、是否生成了 `dev.sh`、主要覆盖范围、未能确认的信息。


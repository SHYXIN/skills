# GitLab Runner 部署：架构与流程图解

本文件用字符图解释「从一台新机器到 CI/CD 跑通」的整体链路，帮助理解 skill 每一步在做什么、谁在做什么。

---

## 1. 整体架构（运行时）

```text
┌─────────────────────────────────────────────────────────────────────┐
│ 你的电脑（Git Bash / 终端）                                          │
│   └─ 运行 scripts/*.sh（本机侧做检测、远程执行命令）                  │
└───────────────┬─────────────────────────────────────────────────────┘
                │  SSH（免登录，端口 22）
                v
┌─────────────────────────────────────────────────────────────────────┐
│ 远程服务器（新机器，Linux）                                          │
│                                                                     │
│   Docker daemon                                                     │
│    └─ 容器: gitlab-runner  (gitlab/gitlab-runner:v15.x)             │
│          │  · 负责“向 GitLab 要 job、跑 job、回写结果”               │
│          │  · executor=docker：每个 job 由它临时拉起一个独立容器跑    │
│          │                                                          │
│          └── 会拉起的 job 容器，例如:                                │
│              · python:3.11-slim   （跑你的打包/脚本）                 │
│              · alpine:latest      （跑 curl/jq 等）                  │
└───────────────┬─────────────────────────────────────────────────────┘
                │  HTTPS（轮询 / 上报）
                v
┌─────────────────────────────────────────────────────────────────────┐
│ GitLab 服务器 (<你的GitLab地址>)                                          │
│   · 存代码、触发流水线                                               │
│   · Runners 页登记了哪些 runner 可用（online/pending）               │
└─────────────────────────────────────────────────────────────────────┘
```

**三个角色一句话**
- **GitLab**：发任务的老板（你 push 代码 → 它派发 job）
- **gitlab-runner 容器**：打工的（跑到 GitLab 领 job，用 docker 起临时容器执行）
- **job 容器**：真正干活的（跑你 `.gitlab-ci.yml` 里写的 `script`）

---

## 2. 一次 CI 的完整链路

```text
你 push 代码
    │
    v
GitLab 收到新提交，生成 Pipeline
    │
    v
发现项目绑定的 runner（我们注册的）是否在线？
    │ 否 → 流水线一直 pending（最常见卡住原因）
    v 是
gitlab-runner 容器领取 job
    │
    v
docker executor 拉起 job 容器（按 job 的 image: 指定）
    │
    v
容器里执行 script:（例如 echo / 打包 zip / 上传）
    │
    v
结果回写 GitLab → 流水线变绿 ✅ / 红 ❌
```

---

## 3. 部署流程（skill 的五步）

```text
本机                                             远程服务器
─────                                            ─────────

[Step 1] check_ssh.sh
    │  ssh 免登录测试 ───────────────►  通？
    │  ◄─────────────────────────────  回 OK
    ▼ 不通
[Step 1b] ensure_ssh.sh
    生成密钥 + ~/.ssh/config
    ssh-copy-id（人工输密码一次）────►  授权公钥
    ▼
[Step 2] provision.sh
    │  远程执行 ────────────────────►  装 Docker（如无）
    │                              └─ 起 gitlab-runner 容器（如无）
    ▼
[Step 3] register_runner.sh
    │  远程执行 register ──────────►  用 token 注册到 GitLab
    │  ◄───────────────────────────  拿到认证 token，写入 config.toml
    ▼
[Step 4] verify.sh
    │  远程检查 ────────────────────►  docker 版本、容器状态、runner 列表
    ▼                                 到 GitLab Runners 页确认 online
[Step 5] 最小 CI
    加 .gitlab-ci.yml（hello world）
    push ──────────────────────────►  GitLab 派 job → runner 执行 → 绿 ✅
```

---

## 4. "半自动"：脚本做什么、你做什么

| 环节 | 谁做 | 脚本/命令 |
| --- | --- | --- |
| 检测 SSH 免登 | 脚本自动 | `check_ssh.sh` |
| 配置免登 | 脚本生成 + **你输密码一次** | `ensure_ssh.sh` |
| 装 Docker | 脚本远程执行 | `provision.sh` |
| 起 runner 容器 | 脚本远程执行 | `provision.sh` |
| 注册 runner | 脚本远程执行，**你提供 token** | `register_runner.sh` |
| 校验状态 | 脚本自动 + **你到 GitLab 网页确认** | `verify.sh` |
| 跑通 CI | **你写 .gitlab-ci.yml 并 push** | 手动 |

**需要你提供的敏感输入**（脚本不落盘、不硬编码）：
- 机器地址（`user@host`）
- 密码（仅 ensure_ssh 推公钥那一次）
- 注册 token（项目/群组 → CI/CD → Runners 页复制）

---

## 5. 容易混淆的三个"token"

```text
registration token（注册令牌）
    └─ 注册时用一次，格式 GR... / glrt-...，来自 GitLab 项目/群组 Runners 页
       注册成功后 GitLab 返回 authentication token（认证令牌）
       └─ 存在 runner 容器 /etc/gitlab-runner/config.toml 里，之后靠它通信
```
- 项目级 token → runner 只服务该项目
- 群组级 token → runner 服务该群组下所有项目（群组 runner 需 Owner，GitLab < 15.7）

---

## 6. 关键配置速查

```text
Runner 类型（注册时决定）:
  project_type  只服务一个项目
  group_type    服务一个群组
  shared_type   服务整个实例

executor = docker（runner 拉起 job 的方式）:
  job 的 image: python:3.11-slim ──► 跑打包
  job 的 image: alpine:latest    ──► 跑 curl/jq

tags 与 run_untagged:
  run-untagged=true   → 无 tags 的 job 也能跑（本 skill 默认，省事）
  run-untagged=false  → job 必须带 tags 匹配 runner 的 tag-list
```

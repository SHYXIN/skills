---
name: gitlab-runner-provision
description: 从一台新机器开始，完成「SSH 免登录 → 安装 Docker → 安装/注册 GitLab Runner → 最小 CI/CD 成功」的全流程引导。半自动：SKILL.md 给出步骤与命令模板，scripts/ 提供检测/配置/校验脚本，用户只需提供机器地址与 GitLab token。当用户说"配 runner"、"新机器装 gitlab runner"、"给 gitlab 加个 runner"、"跑通 CICD"时触发。
---

# GitLab Runner 新机器部署（gitlab-runner-provision）

在一台新 Linux 机器上把 GitLab Runner 从零跑通，最终以「push 一个 hello-world 流水线变绿」作为验收。半自动：脚本负责检测/生成/校验，需要你确认的敏感输入（token、机器地址）会在每一步明确提示。

> 📖 觉得流程抽象，先看 [docs/architecture.md](docs/architecture.md)：整体架构、CI 执行链路、部署流程图解。

## 输入参数（用户提供）

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| SSH 目标 | `root@<新机器IP>` | 新机器地址，可带端口 `root@<新机器IP>:22` |
| GitLab URL | `https://<你的GitLab地址>/` | 你的 GitLab 实例地址 |
| 注册 token | `<注册token>` 或 `glrt-...` | 项目级：项目 → Settings → CI/CD → Runners 页复制；群组级：群组 → Settings → CI/CD → Runners 页复制 |
| Runner tags | `docker`（可逗号分隔） | 注册时的 tag，CI job 用 `tags:` 匹配 |
| GitLab Runner 版本 | `v15.11.1` | **必须匹配 GitLab 版本**：CE 15.x 用 v15.11.1，最新版 Runner 不支持旧 GitLab（`gitlab/gitlab-runner:latest` 需要 GitLab 16+） |

## 通用前置

```bash
# 本机要求：Git Bash / Linux 终端，有 ssh 客户端
# 脚本位置
SKILL_DIR=skills/skills/devops/gitlab-runner-provision
```

## 工作流

### Step 1：SSH 免登录检查（可能已有，直接检测）

```bash
bash "$SKILL_DIR/scripts/check_ssh.sh" root@<新机器IP>
```

- 输出 `SSH 免登录已可用` → 跳到 Step 2
- 输出 `SSH 免登录不可用` → 执行 Step 1b

### Step 1b：配置 SSH 免登录（只需一次密码）

```bash
bash "$SKILL_DIR/scripts/ensure_ssh.sh" root@<新机器IP>
```

脚本自动完成：无密钥则生成 `ed25519` 密钥 → 追加 `~/.ssh/config` 条目 → `ssh-copy-id` 推送公钥（**这一步会要求输入目标机器密码一次**）。完成后重新执行 Step 1 验证。

### Step 2：安装 Docker + 启动 gitlab-runner 容器

```bash
bash "$SKILL_DIR/scripts/provision.sh" root@<新机器IP> v15.11.1
```

脚本远程检测：
- Docker 未装 → 自动 `curl -fsSL https://get.docker.com | sh` 安装
- `gitlab-runner` 容器不存在 → 创建并 `--restart always` 启动

> 注意：脚本挂载 `/var/run/docker.sock` 到 runner 容器（docker executor 需要）。若服务器 docker 守护进程 socket 路径不同，手动调整 `provision.sh` 里的 `-v` 参数。

### Step 3：注册 Runner

```bash
bash "$SKILL_DIR/scripts/register_runner.sh" \
  root@<新机器IP> \
  "https://<你的GitLab地址>/" \
  "<注册token>" \
  "runner-on-<host>" \
  "docker"
```

- 项目级 token：只服务该项目
- 群组级 token：服务该群组下所有项目
- `--run-untagged=true`：允许 CI job 不带 `tags:` 也能跑（无需给现有 `.gitlab-ci.yml` 加 tags）

### Step 4：校验

```bash
bash "$SKILL_DIR/scripts/verify.sh" root@<新机器IP>
```

同时到 GitLab 对应项目/群组的 **Settings → CI/CD → Runners** 确认新 runner 显示 **online**。

### Step 5：最小 CI/CD 验收（hello world）

1. 在目标 GitLab 项目创建/找到仓库，本地 clone（或已在本地）。
2. 在仓库根目录添加 `.gitlab-ci.yml`：

```yaml
stages:
  - test

hello:
  stage: test
  script:
    - echo "Hello, CI works!"
```

3. push 触发流水线：

```bash
git add .gitlab-ci.yml
git commit -m "ci: hello world"
git push origin master
```

4. 到 GitLab 项目 → CI/CD → Pipelines 看流水线变绿（runner 在线才会开始跑）。

## 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 流水线一直 `pending` | 无可用 runner，或 runner tags 不匹配 | 确认 runner online；`run-untagged=true` 可免 tags |
| `register` 报 401/403 | token 无效或权限不足 | 项目级需 Maintainer+，群组级需 Owner（GitLab < 15.7） |
| 容器起不来 `Cannot connect to the Docker daemon` | docker.sock 未挂载或权限 | 检查 `provision.sh` 的 `-v /var/run/docker.sock` 与 docker 组权限 |
| Runner 版本太新启动失败 | GitLab 版本太老不兼容 | 按 GitLab 版本选 `gitlab/gitlab-runner:v15.x` |
| job 报 `docker: not found` | docker executor 的 image 问题 | 确认 runner 容器能访问 Docker Hub/镜像源 |

## 设计说明

- **半自动**：安装动作发生在远程服务器，脚本只做"检测 / 生成配置 / 远程执行 / 校验"，token、密码等敏感输入由用户提供，不在仓库或脚本中硬编码。
- **通用化**：不绑定任何具体机器/IP/项目；所有机器信息通过参数传入。

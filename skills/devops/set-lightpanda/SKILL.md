---
name: set-lightpanda
description: "在一台有 Docker + Nginx 的 Linux 服务器上部署 Lightpanda Browser（Zig 写的 headless 浏览器，专为 AI agent 设计）的 MCP 服务，并接入本机 agent CLI。覆盖：镜像离线搬运（服务器直连 Docker Hub 慢时本地中转）、MCP-only 容器启动、Nginx 反代（硬编码 Host 校验坑：域名必须改写 Host 头）、IP 白名单（MCP 无鉴权时的唯一防线）、codebuddy/claude mcp add 接入、端到端验收、镜像升级。用户手动调用（/set-lightpanda）。"
disable-model-invocation: true
---

# Set Lightpanda（浏览器 MCP 部署引导）

把 [Lightpanda Browser](https://github.com/lightpanda-io/browser) 的 MCP 服务部署到一台 Linux 服务器，供本机 agent CLI 远程调用浏览器能力（navigate / tree / markdown / extract / eval / screenshot），最终以「本机 `mcp list` 显示 Connected + 真实抓取一个网页」作为验收。半自动：改 Nginx、动防火墙的环节每步明确提示。

本 skill 只管**部署、接入、升级**；部署好之后什么任务该用 lightpanda、什么任务该用别的抓取工具，见 `web-reader-wx` skill。

## 输入参数（用户提供）

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| 服务器地址 | `root@<服务器IP>` | SSH 免密可达、已装 Docker |
| 公网域名 | `<public-domain>` | 服务器上 Nginx 已有 443 server 块和证书 |
| 允许的出口 IP | `<office-egress-ip>` | 访问方的公网出口 IP（办公网/家庭宽带），白名单用 |

## 通用前置（只读探测，直接执行）

```bash
ssh <server> "docker --version && docker info --format '{{.Architecture}}' && nginx -v"
# Docker 版本与架构（镜像按 linux/amd64 搬运，arm 服务器需换镜像）、Nginx 在位
ssh <server> "ss -tlnp | grep 9223 || echo free"
# 9223 端口未被占用
curl -sI -m 8 https://registry-1.docker.io/ | head -1
# 本机能否直连 Docker Hub（决定 Step 1 走直拉还是离线搬运）
```

## Step 1：镜像离线搬运

服务器直连 Docker Hub 大文件慢（国内服务器典型），从本机中转（本机 Docker 与服务器架构一致时）：

```bash
# 本机（需能访问 Docker Hub，必要时开代理）
docker pull lightpanda/browser:latest
docker save lightpanda/browser:latest | gzip > "$TEMP/lightpanda-browser.tar.gz"   # 约 57MB

# 中转到服务器并载入
scp "$TEMP/lightpanda-browser.tar.gz" <server>:/data/
ssh <server> "gunzip -c /data/lightpanda-browser.tar.gz | docker load && docker images lightpanda/browser"
```

本机直连 Docker Hub 通畅时，可跳过中转直接在服务器 `docker pull`。

## Step 2：容器启动（只开 MCP，不开 CDP）

```bash
ssh <server> "docker run -d --name lightpanda-mcp --restart unless-stopped \
  -p 127.0.0.1:9223:9222 \
  lightpanda/browser:latest /bin/lightpanda mcp --host 0.0.0.0 --port 9222 --log_level info"
```

- **只绑 127.0.0.1**：MCP 无鉴权，绝不 `-p 9223:9222` 直开公网；公网入口只走 Nginx（云 NAT 通常也只映射 443/80）
- **只开 MCP 不开 CDP**：agent CLI 原生支持 HTTP MCP，一条 `mcp add` 即接入；未来要给 Playwright 用再加 `--cdp-port`（见维护节）

验证容器内握手：

```bash
ssh <server> "curl -s -X POST http://127.0.0.1:9223/mcp/ -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"smoke\",\"version\":\"0\"}}}' | head -3"
```

返回含 `"serverInfo"` 且 name 为 lightpanda 即容器就绪。

## Step 3：Nginx 反代（含 Host 改写）

> 坑 1 见下：Lightpanda 硬编码校验 Host 头，走域名反代**必须改写 Host**，否则 403。

```bash
ssh <server> "cp /etc/nginx/conf.d/<site>.conf /etc/nginx/conf.d/<site>.conf.bak.lightpanda-$(date +%s)"
```

在 443 server 块内插入（位置不影响，惯例放在既有 `location` 组之后）：

```nginx
location ^~ /lightpanda/mcp/ {
    allow <office-egress-ip>;   # IP 白名单：MCP 无鉴权，这是唯一访问控制
    deny all;
    proxy_pass http://127.0.0.1:9223;
    proxy_set_header Host 127.0.0.1:9223;   # 不能写 $host，否则 403 "Host not allowed"
    proxy_http_version 1.1;
}
```

```bash
ssh <server> "nginx -t && nginx -s reload"
```

验证公网握手（在白名单内的网络环境执行）：

```bash
curl -s -X POST https://<public-domain>/lightpanda/mcp/ -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' | head -3
```

## Step 4：本机 agent CLI 接入

```bash
codebuddy mcp add -s user -t http lightpanda https://<public-domain>/lightpanda/mcp/
claude mcp add -s user -t http lightpanda https://<public-domain>/lightpanda/mcp/
# 按需选一或都加；-s user 全局生效
codebuddy mcp list   # lightpanda ... ✓ Connected 即接入成功
```

## Step 5：端到端验收

让 agent 实际调一次（新开会话，MCP 连接随会话建立）：

> 用 lightpanda 打开 https://github.com/trending，用 markdown 工具读出前 3 个仓库名。

- 返回仓库名列表 → **验收绿**
- 已知能力边界（不是部署问题）：navigate / tree / markdown / extract / eval 可靠；**screenshot 是文本布局近似**（中文显示为豆腐块、无 WebGL 渲染），需要真截图的场景换 Playwright 类工具

## 维护

**镜像升级**（同分发流程）：

```bash
# 本机 pull 新版 → save → scp → load（同 Step 1）
ssh <server> "docker rm -f lightpanda-mcp"
# 然后按 Step 2 原命令重建容器（配置无状态，无数据卷）
```

**未来开 CDP**（给 Playwright 用）：容器启动命令追加 `--cdp-port 9224` 并映射；Nginx 需另加 WebSocket 升级头配置（`proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`）。

**出口 IP 变化**（办公网搬迁/在家办公 → 403）：改 Nginx `allow` 行后 `nginx -s reload`。

## 坑位清单

1. **硬编码 Host 校验**：Lightpanda 源码 `src/mcp/HttpServer.zig` 的 `checkHeaders` 只接受 `localhost:*` 或字面 IP 的 Host，域名一律 403（防 DNS rebinding，不可配置）。走域名反代必须 `proxy_set_header Host 127.0.0.1:9223`，写 `$host` 必 403。
2. **MCP 无鉴权**：IP 白名单是唯一访问控制。容器只绑 127.0.0.1、公网只走 Nginx + allow/deny，三缺一都等于裸奔。
3. **403 两种成因要分清**：Nginx `deny all` 命中返回的是 Nginx 的 403；Lightpanda 的 Host 校验拒绝返回的也是 403 但 body 含 `Host not allowed`。看 body 定位是白名单问题还是 Host 改写问题。

## 排障速查

| 症状 | 原因 | 处置 |
| --- | --- | --- |
| 403，body 含 `Host not allowed` | Nginx 没改写 Host 或写了 `$host` | 坑 1 的 `proxy_set_header` |
| 403，body 为 Nginx 默认页 | 出口 IP 不在白名单 | 改 `allow` 行后 reload |
| 容器内握手通、公网不通 | location 没生效 / reload 没执行 | `nginx -t && nginx -s reload`；核对 location 前缀 |
| `mcp list` 连不上但 curl 通 | CLI 进程未重载 MCP 配置 | 新开会话重试 |
| 抓取超时 | 目标站反爬或容器内无外网出口 | 先在容器内 `curl -sI` 目标站验证连通性 |
| 中文页面 screenshot 全是豆腐块 | 能力边界：无字体渲染/WebGL | 换 markdown/tree 读内容，真截图用 Playwright |

## 护栏

- 改 Nginx 前备份（`.bak.lightpanda-<ts>`），`nginx -t` 通过才 reload；现有 location 零改动，只追加。
- 容器端口只绑 127.0.0.1；任何「临时开公网直连」的要求都拒绝，走 Nginx 白名单。
- 白名单 IP、域名、服务器地址等环境事实只在命令占位符出现，不写进本文档这类发布文件。
- 服务器上已有同名容器（`lightpanda-mcp`）先探再动，不盲目覆盖。

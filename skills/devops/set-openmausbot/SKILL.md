---
name: set-openmausbot
description: "在一台有 Docker 的 Linux 服务器上从零部署 OpenMausBot（开源 AI bot 车队聊天壳），并出公网 HTTPS 地址。覆盖：镜像离线搬运（服务器直连 ghcr.io 超时时）、邮箱验证码登录（QQ 码易混淆推荐 Gmail）、容器常驻启动、cloudflared 二进制手动落位（大文件下载被掐时）、设备配对（每个新设备一次）、OpenAI-compat 引擎接入（直写 config.json）、端到端验收。用户手动调用（/set-openmausbot）。"
disable-model-invocation: true
---

# Set OpenMausBot（服务器部署引导）

把 [OpenMausBot](https://www.openmausbot.com)（开源 Grok Bot 替代品：聊天壳 + bot 车队 + bot 专属浏览器）部署到一台 Linux 服务器，最终以「浏览器发一条消息 → 服务端日志确认引擎回复」作为验收。半自动：命令模板已给全，需要你确认/动手的敏感环节（邮箱验证码、API key、配对）每步明确提示。

本 skill 只管**从零部署到验收绿**；日常使用（bot 怎么派活）、MCP 工具挂载、coding CLI 引擎升级不在范围内。

## 输入参数（用户提供）

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| 服务器地址 | `root@<服务器IP>` | SSH 免密可达、已装 Docker |
| 登录邮箱 | `<your-email>` | 推荐 Gmail（见坑 1）；部署期间要能随手打开收件箱 |
| 引擎三件套（可选） | 自建 OpenAI-compat 网关 | OpenAI-compat 的 `url` / `key` / `model`，不提供则先跳过第 6 步 |

## 通用前置（只读探测，直接执行）

```bash
ssh <server> "docker --version && curl -sI -m 8 https://registry-1.docker.io/ | head -1"
# 本机能否直连 ghcr.io / GitHub release（决定第 2/5 步走直拉还是离线搬运）
curl -sI -m 8 https://github.com/cloudflare/cloudflared/releases | head -1
```

任一探测失败不影响流程——本 skill 的默认路径就是**离线搬运**，两处网络不通都绕得开。

## Step 1：镜像离线搬运

服务器直连 ghcr.io 大文件会超时（国内服务器典型），从本机中转：

```bash
# 本机（需能访问 ghcr.io，Clash 开全局）
docker pull ghcr.io/milind-soni/openmausbot:latest
docker save ghcr.io/milind-soni/openmausbot:latest | gzip > "$TEMP/openmausbot-latest.tar.gz"

# 中转到服务器并载入
scp "$TEMP/openmausbot-latest.tar.gz" <server>:/data/openmausbot/
ssh <server> "gunzip -c /data/openmausbot/openmausbot-latest.tar.gz | docker load"
```

验证：`ssh <server> "docker run --rm --entrypoint node ghcr.io/milind-soni/openmausbot:latest dist-server/openmausbot.js badcmd 2>&1 | head -5"` 打印用法即镜像可用。

## Step 2：账号登录（邮箱验证码）

用**临时容器**执行，凭据落在 `omb-data` 卷里供正式容器复用：

```bash
ssh -tt <server> "docker run --rm -it -v omb-data:/data --entrypoint node \
  ghcr.io/milind-soni/openmausbot:latest /app/dist-server/openmausbot.js login --email <email>"
```

- 验证码 8 位数字发到邮箱，**几分钟有效**；收不到翻垃圾箱（国外发件人常进）
- 输码方式二选一：交互终端直接输；或后台挂起后 `ssh <server> "docker run --rm -i -v omb-data:/data --entrypoint node ... login --email <email>" <<< '<8位码>'`
- **只用最新一封邮件的码**——重复发起 login 会作废旧码，新旧混淆会报 `code is not valid`

> 坑 1：QQ 邮箱收国外信易进垃圾箱且多封并存时极易拿错；Gmail 看码依赖梯子但送达稳。二选一，核心是「部署这几分钟里随手能打开收件箱」。
> 坑 2：`< /dev/null` 会让等码进程直接退出（stdin 已关）——重跑时务必带 stdin（`-tt` 或 `<<<`）。

## Step 3：容器常驻启动

```bash
ssh <server> "docker run -d --name openmausbot --restart unless-stopped \
  -v omb-data:/data --entrypoint node \
  ghcr.io/milind-soni/openmausbot:latest /app/dist-server/openmausbot.js serve --tunnel --no-pair"
ssh <server> "sleep 30 && docker logs openmausbot 2>&1 | tail -12"
```

首次启动会尝试自下载 cloudflared——服务器连不上 GitHub 时会卡在这里，走 Step 4 修复。

## Step 4：cloudflared 手动落位（下载超时才需要）

容器启动时按 pinned 版本从 GitHub release 拉 cloudflared（约 40MB），国际带宽差的服务器会重试超时。本机下载后塞进卷内约定路径，容器重启即认：

```bash
# 本机下载 pinned 版本（版本与 sha256 取自 OpenMausBot 源码 scripts/prepare-cloudflared.mjs，
# 换版本时以当时源码为准）
curl -L -o "$TEMP/cloudflared-linux-amd64" \
  https://github.com/cloudflare/cloudflared/releases/download/2026.10.3/cloudflared-linux-amd64
# 校验（pinned digest，源码内声明）
sha256sum "$TEMP/cloudflared-linux-amd64"   # 应为 053b80b0a23031a038fdbf3c073f59f82b8f1f152aa67971d7383ffafc0dbab0

scp "$TEMP/cloudflared-linux-amd64" <server>:/data/openmausbot/
ssh <server> "docker cp /data/openmausbot/cloudflared-linux-amd64 openmausbot:/tmp/cloudflared && \
  docker exec -u root openmausbot sh -c 'mkdir -p /data/.openmausbot/dist-native/cloudflared/linux-x64 && \
  cp /tmp/cloudflared /data/.openmausbot/dist-native/cloudflared/linux-x64/cloudflared && \
  chmod +x /data/.openmausbot/dist-native/cloudflared/linux-x64/cloudflared && \
  chown -R 1001:1001 /data/.openmausbot/dist-native' && \
  docker restart openmausbot"
ssh <server> "sleep 60 && docker logs --since 2m openmausbot 2>&1 | grep -iE 'tunnel|live' | tail -3"
```

日志出现 `tunnel: live at https://c-xxxx.openmausbot.com` 即通。**这个地址是 OpenMausBot 云端按登录账号自动预留的固定子域**（Cloudflare Tunnel，免端口免 DNS），一个安装对应一个，只服务 MausBot 自己——不是可复用的通用域名。

## Step 5：设备配对

每个新设备（浏览器/手机）首次访问都要配对一次，配完永久信任：

```bash
ssh <server> "docker exec openmausbot node /app/dist-server/openmausbot.js pair --label '<设备名>'"
```

输出三样东西任选其一用：
- **配对码**（`XXXX-XXXX-XXXX`，单次有效，数小时过期）→ 设备浏览器开 `<public-url>/pair` 输入
- **带码直连**：`<public-url>/pair#code=<码>`，点开即配
- **二维码**（终端 ASCII）→ 手机相机扫

未配对设备访问会得到 `403 forbidden: ... (pair this device to use the server remotely)`——这是设计行为不是故障，生成新配对码即可。

## Step 6：（可选）OpenAI-compat 引擎接入

默认无引擎。要接自建网关（任何 OpenAI-compat 端点）时，停容器直写卷内 `config.json`：

```bash
ssh <server> "docker stop openmausbot && cat > /var/lib/docker/volumes/omb-data/_data/.openmausbot/config.json << 'EOF'
{
  \"instances\": {
    \"openaiCompat\": {
      \"driver\": \"openai-compat\",
      \"displayName\": \"<显示名>\",
      \"config\": {
        \"key\": \"<API key>\",
        \"url\": \"<网关地址，如 https://<gateway-host>/v1>\",
        \"model\": \"<模型名>\",
        \"managedModels\": [\"<模型名>\", \"<备选模型，可省>\"]
      }
    }
  },
  \"onboarding\": { \"completedAt\": \"<ISO时间>\", \"version\": 1, \"hintsSeen\": [] }
}
EOF
docker start openmausbot"
```

> 坑 3：写完必须 `chown 1001:1001` + `chmod 600`（容器内 maus 用户 uid=1001，root 写入后它读不了，引擎会一直不可用）：
> `ssh <server> "docker exec -u root openmausbot sh -c 'chown 1001:1001 /data/.openmausbot/config.json && chmod 600 /data/.openmausbot/config.json'"`

若文件已存在（含 onboarding 记录），只合并 `instances` 段，别整个覆盖丢历史。

## Step 7：端到端验收

```bash
# 服务端状态：应显示 public address + signed in
ssh <server> "docker exec openmausbot node /app/dist-server/openmausbot.js status"
# 引擎状态：available / authenticated
ssh <server> "docker exec openmausbot sh -c 'cat /data/.openmausbot/config.json' | grep -A3 openaiCompat"
```

浏览器（已配对设备）打开 public address，发一条「你是什么模型」→ 页面正常回复；服务端 `docker logs openmausbot --since 5m | grep -iE 'turn|model'` 看到回合进出 → **验收绿**。

## 排障速查

| 症状 | 根因 | 处置 |
| --- | --- | --- |
| login 报 `code is not valid` | 新旧码混淆 / 过期 / 带空格 | 重发 login，用最新一封、纯数字 |
| 等码进程秒退 | `< /dev/null` 关了 stdin | 用 `-tt` 或 `<<< '<码>'` |
| 启动卡在下载 cloudflared | 服务器拉 GitHub 40MB 超时 | Step 4 手动落位 |
| 页面 403 要求 pair | 新设备未配对 | Step 5 生成新码 |
| 引擎一直 unavailable | config.json 属主/权限不对 | 坑 3 的 chown/chmod |
| 公网地址变了 | 换了登录账号 | 地址按账号预留，换号即换址 |

## 护栏

- 所有 `docker stop / rm`、写 `config.json` 动作前向用户确认（正在跑的会话会被打断）。
- API key、验证码、服务器地址、登录邮箱等环境事实只在命令占位符出现，不写进本文档这类发布文件；机器级的具体值由运行时环境或用户记忆提供。
- 服务器上已有的同名容器（`openmausbot`）先探再动，不盲目覆盖。
- 本 skill 产出物（镜像 tar 包、cloudflared 二进制）留在服务器 `/data/openmausbot/` 即可，验收后可清理。

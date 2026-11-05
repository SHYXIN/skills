---
name: set-openmausbot
description: "在一台有 Docker 的 Linux 服务器上从零部署 OpenMausBot（开源 AI bot 车队聊天壳），并出公网 HTTPS 地址。覆盖：镜像离线搬运（服务器直连 ghcr.io 超时时）、邮箱验证码登录（QQ 码易混淆推荐 Gmail）、容器常驻启动、cloudflared 二进制手动落位（大文件下载被掐时）、设备配对（每个新设备一次）、OpenAI-compat 引擎接入（直写 config.json）、BYO-VPS 云端电脑（bot 的 Computer 容器跑本服务器，含老内核补丁）、端到端验收。用户手动调用（/set-openmausbot）。"
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
# 服务器能否直连 docker.io（决定 Step 8.2 是否必须预 build Cua 镜像）
curl -sI -m 8 https://github.com/cloudflare/cloudflared/releases | head -1
# 本机/服务器能否直连 GitHub release（决定 Step 1/4 走直拉还是离线搬运）
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

## Step 8：（可选）BYO-VPS 云端电脑

让 bot 的 Computer（云端电脑）跑在**本服务器自己**身上（Self-hosted VPS 后端）：omb 容器通过 `docker -H ssh://<vps-alias>` 控制宿主 dockerd，为每个 bot 建独立 Cua 容器（XFCE 桌面 + VNC，无公网端口），浏览器里远程操作。前提：Step 1–7 已绿，bot 无进行中回合。

### 8.1 前置探测

```bash
# 宿主内核 ≥4.6 才支持 cgroup namespaces（Cua 容器默认 --cgroupns private）；
# CentOS 7 内核 3.10 不支持 → 必须走 8.4 的补丁
ssh <server> "uname -r"
# omb 容器内要能免密 SSH 回宿主
ssh <server> "docker exec openmausbot sh -c 'which ssh || echo NO_SSH; which docker || echo NO_DOCKER_CLI'"
```

### 8.2 预 build 托管镜像（绕开 docker.io 被墙）

omb provision 时会从 docker.io 拉基础镜像并本地 build 衍生镜像（装 cua-driver + 字体）；国内服务器拉不动 docker.io，**预先在本机（或能直连的机器）build 好**推到宿主，检测到即跳过 pull+build。

镜像按 digest 锁定基础层，4 个 label 校验兼容性（`com.openmausbot.local-vm=1` / `cua-driver=<版本>` / `cua-base=<digest>` / `image-layer=<n>`）。Dockerfile 从 omb 源码模板逐字提取（源码内 `localVmDockerfile` 相关模板），只把 FROM 换成 digest 锁定的镜像源（如 `dockerproxy.net/trycua/xfce-cua@sha256:<digest>`）。基础镜像 digest 与 cua-driver 版本以**当时 omb 源码**为准（`docker run --rm --entrypoint node <omb镜像> -e "..."` 可打印）。

```bash
# 本机 build（基础镜像走可直连的 proxy 源 + digest 锁定）
docker build -f omb-cua.Dockerfile -t openmausbot/cua-local-vm:driver-<ver>-v<n> .
docker save <镜像名> | gzip > "$TEMP/omb-cua.tar.gz"
scp "$TEMP/omb-cua.tar.gz" <server>:/data/openmausbot/
ssh <server> "gunzip -c /data/openmausbot/omb-cua.tar.gz | docker load"
# 验证 4 个 label
ssh <server> "docker inspect <镜像名> --format '{{json .Config.Labels}}'"
```

### 8.3 omb 容器装工具 + SSH 通道

omb 镜像内缺 `ssh` 和 `docker` CLI，装在可写层（**容器重建会丢**，装完 snapshot 成镜像）：

```bash
ssh <server> "docker exec -u root openmausbot sh -c 'apk add openssh-client' && \
  docker cp \$(which docker) openmausbot:/usr/local/bin/docker && \
  docker exec -u root openmausbot sh -c 'chmod +x /usr/local/bin/docker'"
# snapshot（重建容器时改用它启动，工具不丢）
ssh <server> "docker commit openmausbot omb-with-vps-tools:latest"

# SSH 密钥：落持久卷 /data/.ssh/（容器 HOME=/data），公钥进宿主 authorized_keys
ssh <server> "docker exec -u root openmausbot sh -c 'ssh-keygen -t ed25519 -N \"\" -f /data/.ssh/id_ed25519 -C omb-vps-link && cat /data/.ssh/id_ed25519.pub'"
# ↑ 公钥追加进宿主 /root/.ssh/authorized_keys，并写 /data/.ssh/config：
#   Host <vps-alias>
#     HostName <服务器IP>
#     User root
#     IdentityFile /data/.ssh/id_ed25519
#     StrictHostKeyChecking accept-new
ssh <server> "ln -sfn /data/.ssh /home/maus/.ssh"   # 容器内 maus 家目录软链（若 omb 以绝对路径读则不需要）
```

### 8.4 老内核补丁（内核 ≥4.6 跳过）

CentOS 7 内核 3.10 无 cgroup namespaces，`--cgroupns private` 会直接失败，且 hardening 检查也认 private。改容器内 3 个编译后 JS（`/app/dist-server/` 下；`index.js` 里变量名带 `3` 后缀如 `config3`，先 grep 再改）：

| 文件 | 改动 |
| --- | --- |
| `vps-computer.js` + `index.js` | docker run 参数 `--cgroupns` 的值 `private` → `host` |
| `container-computer.js` + `index.js` | hardening 检查 `CgroupnsMode === "private"` → `["private","host"].includes(...)` |
| `index.js`（vpsSshTunnelArgs） | `"-o","ExitOnForwardFailure=yes"` 后插入 `"-o","ControlMaster=no","-o","ControlPath=none"` |

```bash
# 备份原始文件到持久卷，再打补丁（sed/perl 均可；改完 grep 验证 token 完整，别把 "--cgroupns" flag 本身删掉）
ssh <server> "docker cp openmausbot:/app/dist-server/vps-computer.js /data/vps-computer.js.bak && \
  docker exec -u root openmausbot perl -pi -e 's/...' /app/dist-server/vps-computer.js /app/dist-server/index.js && \
  docker restart openmausbot"
```

> 坑 4：sed 多文件替换时 flag token（`"--cgroupns"`）和值 token 分属两处，别把 flag 一起删了——只剩孤立 `"host"` 会被 docker 当镜像名。
> 坑 5：补丁后 provision 若复用**首次失败残留的旧容器**（cgroupns=private），补丁看似不生效——`docker ps | grep vps-` 找到残留容器 `docker rm` 后重试。
> 坑 6：隧道 join 报 `SSH viewer tunnel exited` 但手动跑隧道命令正常 → ControlMaster mux 坑：docker 传输留下的 mux master（`-N` 无转发）让后续 `-L` 子进程秒退 0 被误判失败。补丁加 `ControlMaster=no ControlPath=none`，并 `ssh -O exit <vps-alias>` 清掉现有 mux master 后重启。

### 8.5 注册 VPS 后端 + provision

API 直操作（容器内 loopback `127.0.0.1:8799` 是 admin 可信身份，不用 UI）：

```bash
# 1) 全局配置 sshAlias（要求所有 bot 空闲；busy 的先停回合）
ssh <server> "docker exec openmausbot curl -s -X PUT -H 'Content-Type: application/json' \
  -d '{\"vps\":{\"sshAlias\":\"<vps-alias>\"}}' http://127.0.0.1:8799/api/config"

# 2) 给目标 bot 设 cloudBackend=vps（先 PATCH 再 provision，否则报 Choose Cloud computer）
ssh <server> "docker exec openmausbot curl -s -X PATCH -H 'Content-Type: application/json' \
  -d '{\"cloudBackend\":\"vps\",\"computer\":\"cloud\"}' http://127.0.0.1:8799/api/bots/<botId>"

# 3) provision（首次 build/启动 Cua 容器，数分钟；之后秒级唤醒）
ssh <server> "docker exec openmausbot curl -s -X POST http://127.0.0.1:8799/api/bots/<botId>/computer/provision"
# 响应应含 ready=true, desktopReady=true, security=hardened

# 4) 验证：宿主上出现 Cua 容器，四进程 RUNNING
ssh <server> "docker ps | grep vps- && docker exec <cua容器> ps aux | grep -cE 'Xvnc|xfce|cua-driver'"
# 5) join 出浏览器访问地址（vnc.html 应 200）
ssh <server> "docker exec openmausbot curl -s -X POST http://127.0.0.1:8799/api/bots/<botId>/computer/join"
```

日常运维：`POST .../computer/sleep` 休眠（释放资源，下次 provision 秒级唤醒）。改 VPS 配置前先满足护栏中的 bot 空闲要求。

### 8.6 快速恢复清单（容器重建/镜像升级后按序核对）

1. 容器用 `omb-with-vps-tools:latest` 启动（ssh + docker CLI 在）→ 缺则重做 8.3
2. `/data/.ssh/` 密钥与 config 在持久卷 → 宿主 authorized_keys 公钥还在
3. 对照 `/data/*.patched` 重打 8.4 三个 JS 补丁（新镜像必做）
4. 托管镜像 `cua-local-vm:driver-<ver>-v<n>` 还在宿主 → 缺则重做 8.2
5. `vps.sshAlias` 配置在 omb-data 卷 → PUT /api/config 重写一遍
6. 逐 bot 重新 provision（PATCH cloudBackend 不用重做，随 bot 数据持久化）

## 排障速查

| 症状 | 根因 | 处置 |
| --- | --- | --- |
| login 报 `code is not valid` | 新旧码混淆 / 过期 / 带空格 | 重发 login，用最新一封、纯数字 |
| 等码进程秒退 | `< /dev/null` 关了 stdin | 用 `-tt` 或 `<<< '<码>'` |
| 启动卡在下载 cloudflared | 服务器拉 GitHub 40MB 超时 | Step 4 手动落位 |
| 页面 403 要求 pair | 新设备未配对 | Step 5 生成新码 |
| 引擎一直 unavailable | config.json 属主/权限不对 | 坑 3 的 chown/chmod |
| 公网地址变了 | 换了登录账号 | 地址按账号预留，换号即换址 |
| provision 报 cgroup namespaces 不支持 | 宿主内核 3.10（CentOS 7） | 8.4 补丁 `--cgroupns host` |
| provision 报 Choose Cloud computer | bot 未设 cloudBackend | 先 PATCH `cloudBackend=vps` 再 provision |
| provision 重复拉 docker.io 失败 | 预 build 镜像 label 不全/没被识别 | 8.2 核对 4 个 label（cua-driver/cua-base/image-layer） |
| 补丁改了但不生效 | 失败残留的旧 Cua 容器被复用 | 坑 5：删残留容器重 provision |
| join 报 SSH viewer tunnel exited | ControlMaster mux master 干扰 | 坑 6：补丁 + `ssh -O exit` 清 mux |
| 容器重建后 SSH/docker 工具消失 | 装在可写层 | 用 `omb-with-vps-tools:latest` 启动，或重装 8.3 |
| omb 镜像升级后 VPS 功能失效 | 容器内补丁被新镜像覆盖 | 对照 `/data/*.patched` 备份重打 8.4 |

## 护栏

- 所有 `docker stop / rm`、写 `config.json` 动作前向用户确认（正在跑的会话会被打断）。
- API key、验证码、服务器地址、登录邮箱等环境事实只在命令占位符出现，不写进本文档这类发布文件；机器级的具体值由运行时环境或用户记忆提供。
- 服务器上已有的同名容器（`openmausbot`）先探再动，不盲目覆盖。
- 本 skill 产出物（镜像 tar 包、cloudflared 二进制）留在服务器 `/data/openmausbot/` 即可，验收后可清理。
- Step 8 的 PUT /api/config 要求**所有 bot 空闲**；provision/patch 前确认没有进行中的回合。
- Step 8 容器内改 JS 是对编译产物的补丁，**镜像升级即失效**——备份（`/data/*.patched`）和重打步骤必须留给用户。

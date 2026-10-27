---
name: bookpipe
description: "forcoder.net → suufun.com 加速 → book-to-skill 转换的每日书籍流水线。带 URL 直接跑单本全链路（下载+解压到 ~/bookpipe）；不带参数抓今日书目并分级预勾选（AI/编程默认勾选，MP4 永不自动）。所有浏览器操作走 opencli session bookpipe（认证在浏览器，脚本零凭据）。hCaptcha 处暂停等人工。转换本身用 book-to-skill skill 完成。"
---

# bookpipe：forcoder 每日书籍流水线

把 forcoder.net 的新书经 suufun.com 加速下载、解压到本地，交给 book-to-skill 转换。值钱的是探明的链路知识，脚本是链路的固化。

## 链路知识（2026-10 实测，勿重新逆向）

```
forcoder.net 书页 (Cloudflare 拦 curl，必须浏览器)
  └─ DOWNLOAD 区 /goto/ 链接（hCaptcha 过后可见，人工点，不绕过）
       └─ 书页有多个 /goto/ 链接（Homepage + .rar 文件名），必须取文本以 .rar 结尾的那个
            └─ 跳转到 Rapidgator 真实下载页
                 └─ suufun.com/check 粘贴 → 提取链接（扣流量）
                      └─ 添加到中转队列 → 服务端中转
                           └─ 签名直链（48h 时效）→ curl 下载 .rar → 7z 解压
```

关键事实：
- forcoder 首页 Cloudflare 检查页通常几秒自动放行，脚本轮询等待；书页下载区有 hCaptcha，**人工点，脚本暂停等重跑**（`PausePoint`，退出码 2）
- 首页条目选择器：`article.latestPost`，标题链接 `h2.title a`，元信息（日期/ISBN/格式/大小）全在 `article.innerText`
- suufun API：`POST /api/task/v2/search_check`（检测列表）、`POST /api/task/v2/search_task`（转存列表，`steps` 必须 uppercase 数组）；完成任务对象 `d` 字段 = 主线路签名直链
- `search_task` 的 `steps` 传多状态数组（如 `["WAIT_ALLOT","URL","DL"]`）会返回空，**单状态查询（如 `["COMPLETE"]`）才可靠**
- 检测提交后任务不是立即可查：提交后 sleep 2 秒一次性查 `search_check` 会漏（实测发生过），查不到时等几秒重查或重新提交
- suufun 认证在浏览器，全部 API 调用经 opencli 在已登录页面里 fetch，脚本零凭据
- 提取链接扣 suufun 流量（约 5 倍文件大小），直链 48 小时失效（失效用 `bp_run.py url <任务名>` 取新链）
- 7-Zip 在 `C:\Program Files\7-Zip\7z.exe`

## 使用

### 抓今日书目（无参数调用的入口）

```bash
cd scripts && python bp_run.py list
```

输出分级清单：`[x]` 预勾选（PDF/EPUB 且标题命中 AI/编程关键词）、`[ ]` 候选（其余文档）、`-` 跳过（MP4/视频、已处理）。过滤规则在 `~/bookpipe/config.json`（可选，不存在用默认）。

把清单给用户挑选，用户点哪本跑哪本。

### 跑单本全链路

```bash
python bp_run.py run https://forcoder.net/<slug>/
```

成功 → 书落 `~/bookpipe/extracted/<名>/`，打印摘要和下一步提示。
遇到 hCaptcha → 退出码 2 + 暂停说明，**让用户在 Chrome 里点掉验证码，然后原命令重跑**。

### 转换与登记（agent 手工步骤，脚本不做）

1. 对解压出的 PDF/EPUB 调 **book-to-skill** skill 完成转换
2. 转换产物 commit + push 到 `~/book-skills`（私有仓库，一书一目录）
3. 登记状态（去重靠它）：

```bash
python bp_run.py mark <书URL> --title <标题> --isbn <ISBN> \
  --skill-name <skill名> --commit <hash>
```

### 其他子命令

- `status` — 已处理清单
- `url <任务名>` — 取某中转任务的新签名直链

## 状态

`$BOOKPIPE_HOME/state/processed.json`（默认 `~/bookpipe`），按 URL 去重，原子写。已种子首本书（build-applications-local-ai-models-mac，commit 1e7ee7c）。

## 每日自动化（以后外挂，不进 skill）

跑稳后用 CronCreate 每日触发一个 prompt：调本 skill → `list` → 预勾选清单给用户 → 用户挑 → 逐本 `run`。cron prompt 只做调度，链路逻辑全部留在本 skill。

## 边界

- 不绕过任何验证码；hCaptcha 一律人工
- 不存任何账号/凭据；suufun 认证永远在用户浏览器
- MP4/视频课程永不自动下载（省流量）
- 私有内容（书源、账号细节）不进公开仓库

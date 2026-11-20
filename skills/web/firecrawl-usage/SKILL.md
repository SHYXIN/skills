---
name: firecrawl-usage
description: Firecrawl 抓取服务的 agent 使用元工作流。何时用（批量 crawl 整站、search 全文返回、changeTracking 页面监控、Alexandria 结构化数据源）、三层接入（零安装 npx / login 解锁 / Local 版）、CLI 速查、实测坑。触发词："firecrawl"、"抓取"、"整站爬"、"批量抓网页"。与 web-reader-wx 分工：单页读取走那个路由器，本技能管 Firecrawl 产品线。不搬运 API/SDK 细节——运行时以 CLI help 和官方文档为准。
---

# Firecrawl 使用元工作流

Firecrawl（firecrawl/firecrawl，AGPL-3.0）= 给 agent 用的抓取 API：scrape/crawl/search 一个管道出干净 Markdown/JSON。本技能只写「何时用 + 怎么接入 + CLI 速查 + 坑」；API/SDK 细节一律运行时 `npx firecrawl-cli <cmd> --help` 或查官方文档。

## 何时启用

- **批量采集**：crawl 整站文档转 Markdown（喂知识库 / RAG），每页一文件
- **搜索取数**：search 返回结果页全文（WebFetch 只能逐页点，Firecrawl 一步拿全）
- **页面监控**：changeTracking 格式，定时抓同一页只返回差异（盯定价页/文档更新）
- **结构化数据**：Alexandria 550+ 数据源（人/公司/论文）一个 API
- **何时不用**：单页偶尔读 → `web-reader-wx` 路由器（WebFetch/lightpanda/opencli browser）；需登录态或过反爬 → opencli browser

## 接入（三层）

```bash
# 一、零安装（默认，scrape 免注册直接用）
npx -y firecrawl-cli@latest scrape <url>

# 二、login 解锁 crawl/search/map/Alexandria（浏览器点一下，无终端输入）
npx -y firecrawl-cli@latest login --browser
#    或环境变量：FIRECRAWL_API_KEY=fc-...

# 三、Local 版（Windows 未实测——官方只给 macOS/Linux 编译指引，需 Rust+C 编译器）
cargo install firecrawl-local
```

Cloud 按 credit 计费（scrape 免费额度可用）；Local 版 localhost API 无 key，但 JS 渲染依赖本机 Chrome。

## CLI 速查（已实测）

```bash
npx -y firecrawl-cli@latest scrape <url>                      # 默认出 markdown，stdout 直出
npx -y firecrawl-cli@latest scrape <url> --only-main-content  # 去导航/横幅噪音
npx -y firecrawl-cli@latest scrape <url> --format markdown,links  # 多格式→JSON
npx -y firecrawl-cli@latest crawl <url>                       # 整站，异步 job，需 login
npx -y firecrawl-cli@latest map <url>                         # 列全站 URL，需 login
npx -y firecrawl-cli@latest search "<query>"                  # 搜索+全文，需 login
```

- 单格式 = 裸内容输出；多格式 = JSON 信封
- MCP 接 agent：`npx firecrawl-mcp` + `FIRECRAWL_API_KEY` env；一条命令接全：`npx -y firecrawl-cli@latest init --all --browser`
- crawl/search/map/Alexandria 全部要认证；**scrape 是唯一免 key 操作**

## 实测坑（2026-11-20，firecrawl-cli latest）

1. **无 `--markdown` flag**：默认就是 markdown；传了报 unknown option
2. **Cloud 代理隧道坑**：部分站点报 `ERR_TUNNEL_CONNECTION_FAILED`（Firecrawl 内部代理错误）——firecrawl.dev/docs 域已验通，自建站/小站可能隧道失败；重试或换 Local 版绕开 Cloud 代理层
3. **crawl 限页参数不是 `--limit`**（scrape 子命令没这参数，具体以 `crawl --help` 实时输出为准）
4. **本机代理环境**：NODE_TLS_REJECT_UNAUTHORIZED=0 警告刷屏，不影响功能
5. **免注册额度**：scrape 可匿名，其余操作直接报 `Not authenticated. Run "firecrawl login --browser"`

## 与 web-reader-wx 的边界

- `web-reader-wx` 路由器保持三分流（WebFetch/lightpanda/opencli）不动：管「读一个网页怎么选工具」
- 本技能管 Firecrawl 产品线：单页读 → 路由器；批量/搜索/监控取数 → 本技能
- 层级参照：Lightpanda 是引擎（自托管可控零成本），Firecrawl 是服务（免维护但数据过第三方、按 credit）——量大且要控数据流向自建 lightpanda，量小要省事用 Firecrawl

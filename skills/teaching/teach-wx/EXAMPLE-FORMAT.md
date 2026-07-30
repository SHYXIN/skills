# Examples 格式

技术主题、代码库和 GitHub 仓库类 lesson 默认配套一个小示例。示例用于把 lesson 里的机制变成可运行、可观察的小实验。

## 目录结构

示例统一放在学习区根目录的 `examples/` 下。运行环境在 `examples/` 级别共享，不要每个示例各建一套依赖。

```text
examples/
├── README.md
├── .gitignore
├── package.json              # JS/TS 示例共享，按需创建
├── pyproject.toml            # Python 示例共享，按需创建
├── requirements.txt          # 简单 Python 示例可用，按需创建
├── .env.example              # 需要环境变量时创建，不能写真实 .env
├── .venv/                    # 本地 Python 虚拟环境，必须忽略
├── node_modules/             # 本地 Node 依赖，必须忽略
└── 0001-{slug}/
    ├── README.md
    └── demo.{py|ts|js|sh|...}
```

## examples/.gitignore

```gitignore
.venv/
node_modules/
.env
dist/
build/
__pycache__/
*.pyc
```

## examples/README.md

````md
# Examples

这个目录保存 lesson 配套的小实验。依赖在 `examples/` 级别共享，单个示例不要自己创建 `.venv` 或 `node_modules`。

## Python

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

## Node / TypeScript

```bash
npm install
```

## 规则

- 每个示例小到 5-10 分钟能读完和跑完。
- 每个示例目录必须有自己的 `README.md`。
- 如果当前环境无法验证，示例 README 必须标注“未验证”和原因。
````

## 单个示例 README.md

````md
# {示例名}

## 对应 lesson

../lessons/0001-{slug}.html

## 目标

{这个示例验证什么机制。}

## 运行

```bash
{命令}
```

## 预期结果

{看到什么输出，或者应该观察哪段行为。}

## 修改实验

{一个 5 分钟内能做的小改动。}

## 验证状态

已验证 / 未验证：{如果未验证，说明原因。}
````

## 示例代码规则

- 必须有可执行入口，例如 `demo.py`、`demo.ts`、`demo.js` 或 `demo.sh`。
- 必须在 README 写清运行命令和预期结果。
- 示例服务当前 lesson，不追求完整工程。
- 不复制原仓库大段代码。
- 不创建大型 demo app。
- 优先选择最小可运行栈；不要为了展示完整性同时引入 Python、Node 和 Docker。
- Shell/CLI 示例尽量零依赖。
- 需要环境变量时只写 `.env.example`，不写真实 `.env`。

---
name: dp-dev-bootstrap
description: 快速把一个 monorepo 的 dev 环境跑起来。换新电脑/依赖缺失/native 模块重编译/sidecar 下载/build tools 安装等启动前置问题，一键体检（preflight）+ 确定性修复。内置 deepworks profile，其他仓库可加 profile 或退化到纯诊断。用户手动调用（/dp-dev-bootstrap）。
---

# Dev Bootstrap

把"这个仓库为什么跑不起来"从一轮轮排障压缩成一次体检 + 几条确定性命令。

**核心概念 — preflight（起飞前检查）**：像飞行员起飞前过检查单一样，把 dev 启动的全部前置条件列成清单，逐项验证；不合格项给出（或直接执行）修复命令。

## 工作方式

```bash
# 1. 体检（只诊断，不改动）
node <skill_dir>/scripts/preflight.mjs --repo <仓库路径>

# 2. 体检 + 自动修复轻量项（types build / pnpm install / sidecar / native 重编译）
node <skill_dir>/scripts/preflight.mjs --repo <仓库路径> --fix
```

`--json` 输出机器可读结果。流程：

1. 读仓库 `package.json` 识别项目 → 匹配 `profiles/` 里的声明文件
2. 逐项跑检查（路径存在性、配置内容等）
3. 失败项按 `severity` 分级处理：
   - `fix`：确定性修复命令，`--fix` 时直接执行
   - `prompt`：重量级操作（如 VS Build Tools 数 GB 安装、需提权），**只打印命令和说明，等用户确认**，绝不自动跑
   - `advisory`：仅提示（如镜像配置建议）

## Profile：声明式清单

`profiles/<name>.json` 是该项目 dev 启动前置的知识库：

```json
{
  "match": { "packageJsonNames": ["deepworks"] },
  "checks": [
    { "id": "types-dist", "severity": "fix", "label": "…",
      "check": { "type": "pathExists", "path": "packages/types/dist" },
      "fixCmd": "pnpm --filter @openwork/types build" }
  ]
}
```

- 检查项 `type`：`pathExists`（相对仓库根）| `fileContains`（path + needle）
- **新增仓库支持 = 加一个 profile 文件**，不改引擎
- 若目标仓库自己带了 preflight 脚本（如 `scripts/dev-preflight.mjs`），优先调用仓库自己的，本 skill 退化为调用器

## 已内置 profile

- **deepworks**：依赖安装 → types 构建 → sidecar（opencode/rg）→ better-sqlite3 native 重编译 → VS Build Tools（prompt 级）→ Electron 镜像检查（advisory 级）。换新电脑后跑一次 `--fix` 即可从镜像拉齐全部轻量项。

## 边界

- 引擎只做"前置条件"层；启动本身仍用仓库自己的命令（如 `pnpm dev`）
- `prompt` 级项需要用户手动执行后重跑体检确认
- profile 里不写密钥、不写绝对路径，全部相对仓库根

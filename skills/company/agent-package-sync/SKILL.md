---
name: agent-package-sync
description: 公司内部 agent/专家结果包上传前同步工作流。用于检查 result 包改动、同步 AGENTS.md 命名、按实际 skills 目录重打 zip、排除缓存并输出上传清单；不执行 git commit 或 push。
---

# Agent Package Sync

## 目标

用于公司工作中整理任意 agent/专家结果包。典型结果包结构：

```text
<repo>/
  result/
    AGENTS.md
    soul.md
    README.md
    skills/
      <skill-name>/
      <skill-name>.zip
```

默认路径：

- `repo_root`: 当前仓库根目录，或用户指定目录
- `package_root`: `<repo_root>/result`

如果用户给出明确路径，以用户路径为准。

## 工作流

1. 检查 git 状态和变更摘要，只用于了解改动范围。
2. 检查主指令命名：
   - 如果存在 `Instructions.md` 且不存在 `AGENTS.md`，改名为 `AGENTS.md`。
   - 如果两者都存在，不覆盖，提示用户确认。
   - 如果只有 `AGENTS.md`，保持不动。
   - Windows 下如果出现 `agents.md / AGENTS.md` 大小写冲突，提示规范为 `AGENTS.md`。
3. 扫描 `<package_root>/skills` 下所有一级目录作为候选 skill。
4. 对每个候选 skill：
   - 如果缺少同名 `.zip`，生成。
   - 如果目录内源文件比 `.zip` 新，重打。
   - 如果用户要求全部重打，全部重打。
5. 打包规则：
   - zip 内保留顶层 skill 目录名。
   - 排除 `__pycache__` 和 `.pyc`。
   - 不默认排除业务文件；如果用户明确要求保留 `auth.json`，必须打入 zip。
6. 输出上传清单：
   - `AGENTS.md`
   - `soul.md`
   - 实际生成或存在的 skill zip
   - 其他用户指定的文档

## 禁止事项

- 不执行 `git add`。
- 不执行 `git commit`。
- 不执行 `git push`。
- 不回滚用户修改。
- 不删除业务目录，除非用户明确要求并且路径已核验。

## 推荐脚本

优先使用：

```powershell
python <skill>/scripts/package_sync.py --repo <repo_root>
```

常用参数：

```powershell
python <skill>/scripts/package_sync.py --repo C:\code_proj\maintenance-execution-expert
python <skill>/scripts/package_sync.py --package C:\code_proj\maintenance-execution-expert\result
python <skill>/scripts/package_sync.py --repo C:\code_proj\maintenance-execution-expert --all
```

脚本只整理文件和 zip，不做提交。

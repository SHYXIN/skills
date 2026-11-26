#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent-memory-sync — 把本机各 AI agent 的历史记忆增量导入 engram。

子命令：
  scan                          扫描所有已知/候选记忆源，列清单等人勾选
  sync --source <key> [--project P] [--dry-run] [--scope S]
                                增量导入一个源（指纹没变的自动跳过）
  sync --source <key> --reconcile
                                首跑对账：按标题在库里查重，命中即登记跳过
  status                        查看 state 摘要
  agents-md                     生成 AGENTS.md 指引段（标记对内幂等替换）

仅依赖标准库；Python 3.8+。md 源只读，写入只进 engram。
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
ENGRAM_CANDIDATES = [HOME / ".local" / "bin" / "engram.exe", Path("engram.exe")]
STATE_FILE = HOME / ".engram" / "agent-memory-sync-state.json"
MD_START = "<!-- agent-memory-sync:start -->"
MD_END = "<!-- agent-memory-sync:end -->"
SKIP_DIRS = {"node_modules", ".git", ".venv", "__pycache__", "target", "dist"}

# 实测确认过的分库映射（codebuddy 编码目录名 → engram project）
KNOWN_PROJECTS = {
    "c-code_proj": "code-proj",
    "c-Users-DEEPEXI": "deepexi-home",
}

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.S)
FIELD_RE = {k: re.compile(r"^%s:\s*(.+)$" % k, re.M) for k in ("name", "description", "type")}
SAVED_RE = re.compile(r"Memory saved: #(\d+)")
HIT_RE = re.compile(r"#(\d+) \(\w+\) — (.*)")


# ---------- 基础设施 ----------

def engram_bin():
    for c in ENGRAM_CANDIDATES:
        if c.exists():
            return str(c)
    return "engram"


def run_engram(args, timeout=90):
    env = {**os.environ, "ENGRAM_NO_UPDATE_CHECK": "1"}
    p = subprocess.run([engram_bin(), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"entries": {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def sha256_of(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def parse_md(path):
    """返回 (title, msg, type)。frontmatter 的 name/description/type 优先，文件名前缀后备。"""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    stem = Path(path).stem
    title, desc, mtype, body = stem, "", None, raw
    m = FM_RE.match(raw)
    if m:
        fm, body = m.group(1), m.group(2)
        for field, rx in FIELD_RE.items():
            fm_m = rx.search(fm)
            if fm_m:
                if field == "name":
                    title = fm_m.group(1).strip()
                elif field == "description":
                    desc = fm_m.group(1).strip()
                else:
                    mtype = fm_m.group(1).strip()
    if not mtype:
        for prefix, t in (("project_", "project"), ("reference_", "reference"), ("feedback_", "feedback")):
            if stem.startswith(prefix):
                mtype = t
                break
    msg = (desc + "\n\n" + body.strip()) if desc else body.strip()
    return title, msg, mtype or "reference"


# ---------- 适配器：记忆源发现 ----------

def md_entries(dir_path):
    """目录下的记忆条目 md，排除索引文件，按名排序。"""
    return sorted(p for p in Path(dir_path).glob("*.md") if p.name != "MEMORY.md")


def source_codebuddy():
    out = []
    base = HOME / ".codebuddy"
    glob_mem = base / "memery"
    if glob_mem.is_dir():
        files = list(glob_mem.glob("*_memery.md"))
        if files:
            out.append(dict(key="codebuddy-global", agent="codebuddy",
                            roots=[str(glob_mem)], files=files,
                            project="deepexi-home", note="全局个人档案，建议并入 home 库（可改）"))
    proj_base = base / "projects"
    if proj_base.is_dir():
        for d in sorted(proj_base.iterdir()):
            mem = d / "memory"
            if mem.is_dir():
                files = md_entries(mem)
                if files:
                    project = KNOWN_PROJECTS.get(d.name, re.sub(r"[^a-z0-9]+", "-", d.name.lower()).strip("-"))
                    note = "" if d.name in KNOWN_PROJECTS else "project 名为推断，请确认"
                    out.append(dict(key="codebuddy-proj:%s" % d.name, agent="codebuddy",
                                    roots=[str(mem)], files=files, project=project, note=note))
    return out


def probe_dir_memory(base, agent, key):
    """在某个 agent 目录下探测 MEMORY.md / memory / memery 特征。"""
    hits = []
    if not base.is_dir():
        return hits
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        depth = Path(root).relative_to(base).parts
        if len(depth) >= 4:
            dirs[:] = []
            continue
        low = [f.lower() for f in files]
        if "memory.md" in low or "memory" in [d.lower() for d in dirs] or "memery" in [d.lower() for d in dirs]:
            sub = Path(root) / "memory"
            if not sub.is_dir():
                sub = Path(root) / "memery"
            target = sub if sub.is_dir() else Path(root)
            entries = md_entries(target) if target.is_dir() else []
            if entries:
                hits.append(dict(key="%s:%s" % (key, target.name.lower()), agent=agent,
                                 roots=[str(target)], files=entries,
                                 project=re.sub(r"[^a-z0-9]+", "-", agent.lower()),
                                 note="探测点命中，请确认是否入库"))
    return hits


def source_generic():
    """兜底：用户目录一层 dotdir 里找记忆特征，排除已知适配器覆盖的目录。"""
    covered = {HOME / ".codebuddy"}
    out = []
    for d in HOME.iterdir():
        if not (d.is_dir() and d.name.startswith(".") and d not in covered):
            continue
        out.extend(probe_dir_memory(d, d.name[1:], "generic-%s" % d.name[1:]))
    return out


def all_sources():
    seen = {}
    for s in source_codebuddy() + source_generic():
        seen[s["key"]] = s
    return list(seen.values())


# ---------- 子命令 ----------

def cmd_scan(_args):
    sources = all_sources()
    state = load_state()["entries"]
    if not sources:
        print("没有发现任何记忆源。")
        return
    for s in sources:
        done = sum(1 for f in s["files"] if str(f) in state)
        print("[%(key)s]  agent=%(agent)s  files=%(n)d  project=%(project)s  已登记=%(done)d"
              % dict(s, n=len(s["files"]), done=done))
        for r in s["roots"]:
            print("    root: %s" % r)
        if s["note"]:
            print("    note: %s" % s["note"])
    print("\n下一步：逐源确认后跑  sync --source <key> [--project <库>] [--dry-run]")


def cmd_sync(args):
    src = next((s for s in all_sources() if s["key"] == args.source), None)
    if src is None:
        sys.exit("找不到源 %s，先跑 scan 看清单" % args.source)
    project = args.project or src["project"]
    state = load_state()
    entries = state["entries"]
    ok = skip = fail = recon = 0

    if args.reconcile:
        print("对账中（每条一次查询，较慢）…")
        for f in src["files"]:
            sp = str(f)
            if sp in entries:
                skip += 1
                continue
            title, _, _ = parse_md(f)
            rc, out = run_engram(["search", title, "--project", project, "--limit", "5"])
            hit_id = None
            for line in out.splitlines():
                hm = HIT_RE.search(line)
                if hm and hm.group(2).strip() == title.strip():
                    hit_id = hm.group(1)
                    break
            if hit_id:
                entries[sp] = dict(sha256=sha256_of(f), project=project, obs_id=hit_id,
                                   imported_at=dt.datetime.now().isoformat(timespec="seconds"),
                                   reconciled=True)
                save_state(state)
                recon += 1
            elif args.dry_run:
                print("  [reconcile] 不在库: %s" % title)
        print("RECONCILE DONE: 登记已有=%d 已登记跳过=%d 总数=%d" % (recon, skip, len(src["files"])))
        return

    for f in src["files"]:
        sp = str(f)
        sha = sha256_of(f)
        old = entries.get(sp)
        if old and old.get("sha256") == sha and old.get("project") == project:
            skip += 1
            continue
        title, msg, mtype = parse_md(f)
        if args.dry_run:
            act = "更新" if old else "新增"
            print("  [%s] %s -> %s" % (act, title, project))
            ok += 1
            continue
        save_args = ["save", title, msg, "--type", mtype, "--project", project]
        if args.scope:
            save_args += ["--scope", args.scope]
        rc, out = run_engram(save_args, timeout=120)
        sm = SAVED_RE.search(out)
        if rc == 0 and sm:
            entries[sp] = dict(sha256=sha, project=project, obs_id=sm.group(1),
                               imported_at=dt.datetime.now().isoformat(timespec="seconds"))
            save_state(state)
            ok += 1
        else:
            fail += 1
            print("  FAIL: %s (%s)" % (f.name, out.strip().splitlines()[-1] if out.strip() else rc))
        if (ok + skip + fail) % 20 == 0:
            print("  progress: %d/%d" % (ok + skip + fail, len(src["files"])))
    print("SYNC DONE: synced=%d skipped=%d fail=%d total=%d project=%s%s"
          % (ok, skip, fail, len(src["files"]), project, " (dry-run)" if args.dry_run else ""))


def cmd_status(_args):
    entries = load_state()["entries"]
    if not entries:
        print("state 为空（还没用本脚本导入过；手工灌过的先跑 --reconcile 登记）。")
        return
    by_proj = {}
    for e in entries.values():
        by_proj.setdefault(e["project"], []).append(e)
    for proj, items in sorted(by_proj.items()):
        newest = max(i.get("imported_at", "") for i in items)
        print("%-16s %4d 条  最近导入 %s" % (proj, len(items), newest))
    print("state: %s" % STATE_FILE)


def cmd_agents_md(_args):
    entries = load_state()["entries"]
    by_proj = {}
    for sp, e in entries.items():
        by_proj.setdefault(e["project"], set()).add(str(Path(sp).parent))
    lines = [
        "## Agent 记忆指引（engram）",
        "",
        "各 agent 历史记忆已收拢进 engram（agent-memory-sync 维护）；遇到历史决策、部署档案、踩坑教训、协作偏好类问题时先查记忆再下结论：",
        "",
    ]
    for proj, roots in sorted(by_proj.items()):
        n = sum(1 for e in entries.values() if e["project"] == proj)
        lines.append("- **%s**（%d 条）：engram search \"<关键词>\" --project %s；源（只读）：%s"
                     % (proj, n, proj, "、".join(sorted(roots))))
    lines += [
        "- 跨项目纪律/偏好类结论已标 `--scope global`，跨库查询用 `--all`",
        "- md 记忆源由原 agent 维护，只读参考；新结论用 `engram save \"<标题>\" \"<内容>\" --project <对应库>` 存入",
        "",
    ]
    print(MD_START)
    print("\n".join(lines))
    print(MD_END)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="扫描记忆源列清单").set_defaults(func=cmd_scan)
    sp = sub.add_parser("sync", help="增量导入一个源")
    sp.add_argument("--source", required=True, help="scan 输出的源 key")
    sp.add_argument("--project", help="覆盖推断的 engram 库名")
    sp.add_argument("--scope", help="附加 scope（如 global）")
    sp.add_argument("--dry-run", action="store_true", help="只打印将做什么，不写入")
    sp.add_argument("--reconcile", action="store_true", help="首跑对账：按标题查重登记，不写入")
    sp.set_defaults(func=cmd_sync)
    sub.add_parser("status", help="state 摘要").set_defaults(func=cmd_status)
    sub.add_parser("agents-md", help="生成 AGENTS.md 指引段").set_defaults(func=cmd_agents_md)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

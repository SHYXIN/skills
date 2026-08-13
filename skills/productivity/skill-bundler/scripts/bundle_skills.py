#!/usr/bin/env python3
"""bundle_skills.py — 把用户的 agent skills 逐个打成独立 zip，方便上传到平台。

默认源：~/.agents/skills（Windows 也认 ~/.codebuddy/skills 作回退）。
默认输出：当前目录 skills-zips/，每个 skill 一个 <name>.zip，zip 内保留 <name>/ 顶层目录。
附 MANIFEST.txt 列出每个 zip 与来源。

注意：输出只用 ASCII 字符，避免 Windows GBK 终端编码报错。
"""

import argparse
import datetime
import os
import sys
import zipfile

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".tox", ".idea", ".ruff_cache",
}
SKIP_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
SKIP_EXT = {".pyc"}


def default_root() -> str:
    base = os.path.expanduser("~")
    cand = os.path.join(base, ".agents", "skills")
    if os.path.isdir(cand):
        return cand
    cand2 = os.path.join(base, ".codebuddy", "skills")
    if os.path.isdir(cand2):
        return cand2
    return cand  # 即便不存在也返回，让后面统一报错


def discover_skills(root: str):
    """返回 [(key, skill_dir), ...]；key 是相对 root 的路径（深度无关）。
    凡是直接含 SKILL.md 的目录都算一个 skill。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "SKILL.md" in filenames:
            rel = os.path.relpath(dirpath, root)
            found.append((rel, dirpath))
    return sorted(found)


def matches(name: str, key: str) -> bool:
    """--skill / --exclude 的匹配：精确 key，或结尾一段（扁平名）。"""
    return key == name or key.split(os.sep)[-1] == name


def should_skip(parts):
    for part in parts:
        if part in SKIP_DIRS or part in SKIP_FILES:
            return True
        if os.path.splitext(part)[1] in SKIP_EXT:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description="把 agent skills 逐个打成 zip")
    ap.add_argument("--root", default=default_root(),
                    help="skills 根目录（默认 ~/.agents/skills）")
    ap.add_argument("--output-dir", default=None,
                    help="输出目录（默认 ./skills-zips）")
    ap.add_argument("--skill", action="append", default=[], metavar="NAME",
                    help="只打包指定 skill（可多次，扁平名或相对路径皆可）；默认全部")
    ap.add_argument("--exclude", action="append", default=[], metavar="NAME",
                    help="排除指定 skill（可多次）")
    ap.add_argument("--all", dest="all_", action="store_true",
                    help="显式打包全部（默认行为，可省略）")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        sys.exit(f"源目录不存在: {root}")

    discovered = discover_skills(root)
    if not discovered:
        sys.exit(f"在 {root} 下没有找到任何含 SKILL.md 的 skill")

    keys = [k for k, _ in discovered]
    if args.skill:
        selected = []
        for n in args.skill:
            hit = [k for k in keys if matches(n, k)]
            if hit:
                selected.extend(hit)
            else:
                print(f"  [skip] 未知 skill: {n}")
    else:
        selected = list(keys)

    exclude = set(args.exclude)
    selected = [k for k in selected if not any(matches(e, k) for e in exclude)]
    if not selected:
        sys.exit("没有可打包的 skill")

    out_dir = args.output_dir or os.path.join(os.getcwd(), "skills-zips")
    os.makedirs(out_dir, exist_ok=True)

    manifest = []
    used = set()
    written = 0
    for key in selected:
        skill_dir = os.path.join(root, key)
        base = key.split(os.sep)[-1]
        zip_name = base + ".zip"
        if zip_name in used:                       # 分类重名时退回完整路径命名
            zip_name = key.replace(os.sep, "-") + ".zip"
        used.add(zip_name)

        zip_path = os.path.join(out_dir, zip_name)
        count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(skill_dir):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if fn in SKIP_FILES:
                        continue
                    rel = os.path.relpath(os.path.join(dirpath, fn), skill_dir)
                    parts = rel.split(os.sep)
                    if should_skip(parts):
                        continue
                    arcname = os.path.join(base, rel)   # 顶层 <skill>/ 包装
                    zf.write(os.path.join(dirpath, fn), arcname)
                    count += 1
            if count == 0:
                zf.writestr(os.path.join(base, ".keep"), "")
                count = 1
        manifest.append(f"  - {zip_name}  <-  {key}  ({count} files)")
        written += 1
        print(f"  [OK] {zip_name} ({count} files)")

    manifest_lines = [
        "skills bundle manifest (one zip per skill)",
        f"source_root: {root}",
        f"generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"skill_count: {written}",
        f"output_dir: {out_dir}",
        "zips:",
    ] + manifest
    with open(os.path.join(out_dir, "MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(manifest_lines) + "\n")

    print(f"\n[done] packaged {written} skills -> {out_dir}")


if __name__ == "__main__":
    main()

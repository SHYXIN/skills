#!/usr/bin/env python3
"""Scaffold a deepworks-loadable knowledge workspace from templates.

Usage:
  python scaffold.py --project-root <dir> --project-name <name> \
      --display-name <中文名> --schema <schema.json|--spec ontology-spec.yaml> [--force-spec]

Creates:
  SKILL.md  reference/wiki-spec.yaml  reference/ontology-spec.yaml (fixed via deepworks validator when possible)
  raw/  wiki/indexes/  foil/ontology/  scripts/  .opencode/skills/deepworks-knowledge-center (copied from deepworks repo if found)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

WIKI_SPEC = """schema_version: 1
project_name: "{name}"
purpose: 单段式知识库（原始资料直编 foil）。链路 raw/ -> scripts/compile_xmind.py -> foil/ontology/。
mode: custom
page_types:
  - type: index
    directory: wiki/indexes
    display_name: 索引
    purpose: 兼容骨架的入口页
"""

SKILL_MD = """---
name: {name}
description: {display_name}——由 dp-knowledge-compile 生成的 deepworks 知识工作区。原始资料在 raw/，编译产物在 foil/ontology/，重新编译运行 scripts/compile_xmind.py。
---

# {display_name}

- 原始资料：`raw/`
- 编译：`python scripts/compile_xmind.py <xmind路径>`
- 编译产物：`foil/ontology/`（objects.json / links.json / ontology.sqlite）
- 映射配置：`reference/mappings.yaml`（label→类型/属性/关系）
- Schema 基准：`reference/foil-schema-online.json` 与 `reference/ontology-spec.yaml`
"""


def find_deepworks_repo() -> Path | None:
    for cand in ("C:/code_proj/deepworks", "./deepworks", "../deepworks"):
        p = Path(cand).resolve()
        if (p / "packages/types/dist/deepworks/knowledge/ontology-schema.js").exists():
            return p
    return None


def fix_spec(deepworks: Path, spec_path: Path) -> bool:
    script = SKILL_DIR / "scripts" / "fix-ontology-spec.mjs"
    r = subprocess.run(["node", str(script), str(spec_path)],
                       capture_output=True, text=True, encoding="utf-8")
    # fix script hardcodes repo path; override via env-style cwd trick not needed:
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--display-name", default=None)
    ap.add_argument("--schema", required=True,
                    help="schema 来源：foil-schema-online.json 或现成 ontology-spec.yaml")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    name = args.project_name
    display = args.display_name or name

    for d in ("raw", "wiki/indexes", "foil/ontology", "scripts", "reference"):
        (root / d).mkdir(parents=True, exist_ok=True)

    (root / "SKILL.md").write_text(
        SKILL_MD.format(name=name, display_name=display), encoding="utf-8")
    (root / "reference" / "wiki-spec.yaml").write_text(
        WIKI_SPEC.format(name=name), encoding="utf-8")
    for f in ("compile_xmind.py", "fix-ontology-spec.mjs"):
        shutil.copy2(SKILL_DIR / "scripts" / f, root / "scripts" / f)

    schema = Path(args.schema).resolve()
    if schema.suffix == ".json":
        shutil.copy2(schema, root / "reference" / "foil-schema-online.json")
        spec = root / "reference" / "ontology-spec.yaml"
        if not spec.exists():
            gen = SKILL_DIR / "scripts" / "gen_spec_from_schema.py"
            r = subprocess.run(
                [sys.executable, str(gen),
                 "--schema", str(schema), "--out", str(spec),
                 "--project-name", name, "--display-name", display],
                capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                print(r.stdout or "", r.stderr or "", sep="\n", file=sys.stderr)
                sys.exit(f"error: json→spec 生成失败（{gen.name}）")
    else:
        shutil.copy2(schema, root / "reference" / "ontology-spec.yaml")

    # deepworks-knowledge-center skill 副本
    dw = find_deepworks_repo()
    if dw:
        src = dw / ".opencode" / "skills" / "deepworks-knowledge-center"
        dst = root / ".opencode" / "skills" / "deepworks-knowledge-center"
        if src.exists() and not dst.exists():
            shutil.copytree(src, dst)
        print(f"deepworks repo: {dw}")
    else:
        print("note: 未找到本地 deepworks 仓库，跳过 knowledge-center skill 副本与本地校验能力")

    print(f"scaffolded: {root}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate reference/ontology-spec.yaml from foil-schema-online.json.

Fills all fields required by deepworks schema v3 (Zod validated).
Usage: python gen_spec_from_schema.py --schema <foil-schema-online.json> \
           --out <ontology-spec.yaml> --project-name <name> --display-name <中文名> [--deepworks <repo>]
Validates with deepworks' own parser before writing. Fails closed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def find_deepworks() -> Path:
    for cand in ("C:/code_proj/deepworks", "./deepworks", "../deepworks"):
        p = Path(cand).resolve()
        if (p / "packages/types/dist/deepworks/knowledge/ontology-schema.js").exists():
            return p
    raise SystemExit("error: 未找到 deepworks 仓库（探测过 C:/code_proj/deepworks、./deepworks、../deepworks）；可用 --deepworks 指定")


def sanitize_name(name: str) -> str:
    """onto_project_name 必须匹配 ^[a-z0-9_]{1,200}$。"""
    import re
    cleaned = re.sub(r"[^a-z0-9_]", "_", name.lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return (cleaned or "knowledge_base")[:200]


def build_doc(data: dict, name: str, display: str) -> dict:
    def uuid5_stub(seed: str, i: int) -> str:
        import hashlib
        h = hashlib.sha1(f"{seed}|{i}".encode()).hexdigest()
        return f"{h[0:8]}-{h[8:12]}-4{h[13:16]}-8{h[17:20]}-{h[20:32]}"

    obj_types = []
    for i, ot in enumerate(data.get("object_types", [])):
        props = []
        for j, p in enumerate(ot.get("properties", [])):
            props.append({
                "id": p.get("id") or uuid5_stub(f"{ot['name']}|{p['name']}|prop", j),
                "name": p["name"],
                "data_type": p.get("data_type") or "VARCHAR(1024)",
                "display_name": p.get("display_name") or p["name"],
                "required": bool(p.get("required")),
                "default_value": None,
                "is_unique": bool(p.get("is_unique")),
                "related_field_name": p.get("related_field_name"),
                "description": p.get("description") or "",
                "is_primary_key": bool(p.get("is_primary_key")),
                "is_title_key": bool(p.get("is_title_key")),
            })
        if not any(p["is_primary_key"] for p in props):
            props.insert(0, {
                "id": uuid5_stub(f"{ot['name']}|id|pk", 0), "name": "id",
                "data_type": "VARCHAR(1024)", "display_name": "ID", "required": True,
                "default_value": None, "is_unique": True, "related_field_name": "id",
                "description": "稳定对象标识。", "is_primary_key": True, "is_title_key": False,
            })
            props.insert(1, {
                "id": uuid5_stub(f"{ot['name']}|title|tk", 1), "name": "title",
                "data_type": "VARCHAR(1024)", "display_name": "标题", "required": True,
                "default_value": None, "is_unique": False, "related_field_name": "title",
                "description": "图谱展示标题。", "is_primary_key": False, "is_title_key": True,
            })
        obj_types.append({
            "id": ot.get("id") or uuid5_stub(f"ot|{ot['name']}", i),
            "name": ot["name"],
            "display_name": ot.get("display_name") or ot["name"],
            "description": ot.get("description") or f"{ot.get('display_name') or ot['name']}对象类型。",
            "category": None, "icon": None, "color": None,
            "is_abstract": False, "extends_object_type_id": None, "type_version": "1.0.0",
            "related_dataset_id": None, "related_dataset_metadata": None,
            "related_database": None, "related_table_name": None,
            "properties": props, "derived_properties": [],
        })

    link_types = []
    for i, lt in enumerate(data.get("link_types", [])):
        link_types.append({
            "id": lt.get("id") or uuid5_stub(f"lt|{lt['name']}", i),
            "name": lt["name"],
            "display_name": lt.get("display_name") or lt["name"],
            "reverse_showname": None,
            "description": lt.get("description") or f"{lt.get('display_name') or lt['name']}关系。",
            "cardinality": lt.get("cardinality") or "MANY_TO_MANY",
            "source_object_type_id": lt["source_object_type_id"],
            "target_object_type_id": lt["target_object_type_id"],
            "source_property_ids": [], "target_property_ids": [],
            "is_both_direct": False,
            "related_dataset_id": None, "related_resource_name": None,
            "related_table_name": None,
            "related_source_column_names": [], "related_target_column_names": [],
            "properties": [], "derived_properties": [],
        })

    return {
        "onto_project_id": data.get("onto_project_id"),
        "onto_project_name": sanitize_name(name),
        "display_name": display,
        "description": f"{display} 本体配置。由 dp-knowledge-compile 从 foil schema 生成。",
        "icon": None, "color": None, "labels": [],
        "object_types": obj_types,
        "link_types": link_types,
        "deepworks": {
            "schema_version": 3,
            "workspace_id": uuid5_stub(f"ws|{name}", 0),
            "goals": ["从 Wiki 提取可追溯的知识对象和关系"],
            "object_mappings": [{
                "object_type_id": ot["id"],
                "source_selector": {"topic_ids": [], "page_type_ids": [], "local_directory_hint": None},
                "property_mappings": [],
                "update_strategy": "identity",
                "projection": {"kind": "object", "index": "foil/ontology/ontology.sqlite"},
            } for ot in obj_types],
            "link_mappings": [{
                "link_type_id": lt["id"],
                "extract_from": ["frontmatter.related"],
                "property_mappings": [],
            } for lt in link_types],
            "source_types": [],
            "governance": {"publish_statuses": ["accepted", "published"], "review_on_low_evidence": True},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--display-name", default=None)
    ap.add_argument("--deepworks", default=None)
    args = ap.parse_args()

    data = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    doc = build_doc(data, args.project_name, args.display_name or args.project_name)

    dw = Path(args.deepworks).resolve() if args.deepworks else find_deepworks()
    # 用官方序列化器输出，再用官方解析器验证
    script = (
        "import { readFileSync, writeFileSync } from 'node:fs';\n"
        "import { createRequire } from 'node:module';\n"
        f"const require = createRequire('{(dw / 'package.json').as_posix()}');\n"
        f"const m = await import('file:///{(dw / 'packages/types/dist/deepworks/knowledge/ontology-schema.js').as_posix()}');\n"
        "const doc = JSON.parse(readFileSync(0, 'utf8'));\n"
        "const y = m.stringifyOntologySchemaYaml(doc);\n"
        "const p = m.parseOntologySchemaYaml(y);\n"
        "if (!p.success) { console.error(JSON.stringify(JSON.parse(p.error.message).slice(0,8), null, 2)); process.exit(2); }\n"
        "writeFileSync(process.argv[2] ?? '', y);\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as f:
        f.write(script)
        tmp_js = f.name
    r = subprocess.run(
        ["node", tmp_js, str(Path(args.out).resolve())],
        input=json.dumps(doc, ensure_ascii=False),
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        print(r.stderr or "spec 生成后未通过 deepworks 校验", file=sys.stderr)
        sys.exit(r.returncode or 2)
    print(f"OK: {args.out}（已通过 deepworks Zod 校验）")


if __name__ == "__main__":
    main()

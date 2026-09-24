#!/usr/bin/env python
"""Generic xmind -> foil ontology compiler.

Compiles an xmind diagnosis tree into the deepworks-loadable artifacts:
  - foil/ontology/ontology-schema.json   (schema, copied from online baseline)
  - foil/ontology/objects.json / links.json + ontology.sqlite (instances)

The script is business-agnostic: all label->type mappings live in
reference/mappings.yaml. Object ids are deterministic
(prefix + sha1(type|title)) so recompiles are stable.

Usage:
  python scripts/compile_xmind.py <source.xmind> --project-root <root>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path

import yaml


def load_xmind_content(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        with z.open("content.json") as f:
            sheets = json.load(f)
    return sheets[0]["rootTopic"]


def norm_label(s: str) -> tuple[str, str]:
    """Split 'prefix: value' / 'prefix：value' / 'prefix--value' into (prefix, value)."""
    for sep in ("--", "：", ":"):
        if sep in s:
            prefix, _, value = s.partition(sep)
            return prefix.strip(), value.strip()
    return s.strip(), ""


def deterministic_id(prefix: str, type_name: str, title: str) -> str:
    h = hashlib.sha1(f"{type_name}|{title}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{h}"


def walk(topic: dict, parent: dict | None, mappings: dict, objects: dict, links: list,
        meta_defaults: dict, path: str):
    title = (topic.get("title") or "").strip()
    labels = topic.get("labels") or []
    type_label = labels[0].strip() if labels else ""
    type_name = mappings["object_types"].get(type_label)

    this = parent
    if type_name:
        prefix = mappings["id_prefixes"][type_name]
        obj_id = deterministic_id(prefix, type_name, path + "/" + title)
        props: dict = {"id": obj_id, "title": title}
        for label in labels[1:]:
            key, value = norm_label(label)
            if key in ("关系",):
                continue
            if key in ("极性", "需要IOT数据", "需要IOT数据".strip()):
                # non-property annotations; polarity kept as summary suffix
                if key == "极性":
                    props.setdefault("summary", "")
                    props["summary"] = (props["summary"] + f" 极性:{value}").strip()
                continue
            table = mappings["property_labels"].get(type_name) or {}
            table = {**mappings["property_labels"].get("common", {}), **table}
            prop = table.get(key)
            if prop:
                props[prop] = value
        merged_meta = dict(meta_defaults.get("all", {}))
        merged_meta.update(meta_defaults.get(type_name, {}))
        props.update(merged_meta)
        if obj_id not in objects:
            objects[obj_id] = {"_type": type_name, "properties": props}
        this = {"id": obj_id, "type": type_name}

    child_path = path + "/" + title
    # 本节点 label 上的"关系：X"声明 本节点→各有类型子节点 的边
    declared_rels = [v for k, v in (norm_label(l) for l in labels) if k == "关系" and v]
    for child in (topic.get("children", {}).get("attached") or []):
        walk(child, this or parent, mappings, objects, links, meta_defaults, child_path)

    # 子节点遍历完后建边：source=本节点(须有类型), target=每个有类型子节点；
    # 边类型 = 本节点声明的"关系"标签（多个则各建一条）
    if type_name and this and this.get("id"):
        for child in (topic.get("children", {}).get("attached") or []):
            child_labels = child.get("labels") or []
            child_type_label = child_labels[0].strip() if child_labels else ""
            if child_type_label not in mappings["object_types"]:
                continue
            child_title = (child.get("title") or "").strip()
            child_type_name = mappings["object_types"][child_type_label]
            child_prefix = mappings["id_prefixes"][child_type_name]
            child_id = deterministic_id(child_prefix, child_type_name,
                                        child_path + "/" + child_title)
            for rel in declared_rels:
                link_name = mappings["link_types"].get(rel)
                if link_name:
                    links.append({
                        "source": this["id"],
                        "target": child_id,
                        "link_type": link_name,
                    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xmind", type=Path)
    ap.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--source-name", default=None, help="source_file 属性值，默认 xmind 文件名")
    args = ap.parse_args()

    root = args.project_root
    mappings = yaml.safe_load((root / "reference" / "mappings.yaml").read_text(encoding="utf-8"))

    schema_baseline = json.loads(
        (root / mappings["schema_source"]).read_text(encoding="utf-8"))
    type_by_name = {o["name"]: o for o in schema_baseline["object_types"]}
    link_by_name = {l["name"]: l for l in schema_baseline["link_types"]}

    objects: dict = {}
    links: list = []
    root_topic = load_xmind_content(args.xmind)
    walk(root_topic, None, mappings, objects, links, mappings.get("meta_defaults", {}),
         root_topic.get("title", "").strip())

    src_name = args.source_name or args.xmind.name
    # meta_defaults 已在 walk 里注入；此处按 schema 声明剔除未声明属性，避免 unknown_property
    schema_props = {o["name"]: {p["name"] for p in o.get("properties", [])}
                    for o in schema_baseline["object_types"]}
    for obj in objects.values():
        declared = schema_props.get(obj["_type"])
        if declared is not None:
            for k in list(obj["properties"].keys()):
                if k not in declared:
                    del obj["properties"][k]
        obj["properties"]["source_file"] = src_name

    # 验证 link_type 方向与线上 schema 一致（source/target 对象类型必须匹配声明）
    type_id_by_name_pre = {o["name"]: o["id"] for o in schema_baseline["object_types"]}
    checked_links = []
    seen_edges = set()
    skipped = []
    for lk in links:
        lt = link_by_name[lk["link_type"]]
        src_t = objects[lk["source"]]["_type"]
        tgt_t = objects[lk["target"]]["_type"]
        if (type_id_by_name_pre[src_t] != lt["source_object_type_id"]
                or type_id_by_name_pre[tgt_t] != lt["target_object_type_id"]):
            skipped.append(f"{lk['link_type']}: {src_t}->{tgt_t} (schema 要求 "
                           f"{lt.get('source_object_type_name')}/{lt.get('target_object_type_name')})")
            continue
        edge = (lk["link_type"], lk["source"], lk["target"])
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        checked_links.append({**lk,
                              "source_type": src_t, "target_type": tgt_t,
                              "link_type_id": lt["id"]})
    if skipped:
        print(f"warning: skipped {len(skipped)} edges failing schema direction:")
        for s in skipped:
            print("  -", s)

    foil_dir = root / "foil" / "ontology"
    foil_dir.mkdir(parents=True, exist_ok=True)

    # objects.json / links.json：deepworks list-outputs.mjs 读取格式
    out_objects = [{
        "object_type": obj["_type"],
        "primary_key": {"id": obj["properties"]["id"]},
        "properties": obj["properties"],
        "deepworks": {
            "source_page": src_name,
            "sources": [f"raw/sources/{src_name}"],
            "tags": [obj["_type"], obj["properties"]["title"]],
            "evidence": [],
        },
    } for obj in objects.values()]
    (foil_dir / "objects.json").write_text(
        json.dumps(out_objects, ensure_ascii=False, indent=2), encoding="utf-8")

    type_id_by_name = {o["name"]: o["id"] for o in schema_baseline["object_types"]}
    out_links = [{
        "link_type": lk["link_type"],
        "source_primary_key": {"id": lk["source"]},
        "target_primary_key": {"id": lk["target"]},
        "source_object_type": lk["source_type"],
        "target_object_type": lk["target_type"],
        "deepworks": {
            "source_page": src_name,
            "sources": [f"raw/sources/{src_name}"],
            "tags": [lk["link_type"]],
            "evidence": [],
        },
    } for lk in checked_links]
    (foil_dir / "links.json").write_text(
        json.dumps(out_links, ensure_ascii=False, indent=2), encoding="utf-8")

    # ontology-schema.json：与线上 schema 一致
    schema_out = {
        "onto_project_id": schema_baseline["onto_project_id"],
        "onto_project_name": schema_baseline.get("onto_project_name", "equipment-diagnosis"),
        "display_name": "设备诊断",
        "description": "xmind 编译生成的设备诊断本体（schema 与线上一致）。",
        "object_types": schema_baseline["object_types"],
        "link_types": schema_baseline["link_types"],
    }
    (foil_dir / "ontology-schema.json").write_text(
        json.dumps(schema_out, ensure_ascii=False, indent=2), encoding="utf-8")

    (foil_dir / "links.json").write_text(
        json.dumps(out_links, ensure_ascii=False, indent=2), encoding="utf-8")

    # ontology.sqlite：完全复刻 deepworks 已发布库的表结构（object_instances 等）
    db_path = foil_dir / "ontology.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
      );
    CREATE TABLE ontology_metadata (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        active_publication_id TEXT,
        schema_revision TEXT,
        authoring_revision INTEGER NOT NULL DEFAULT 0,
        database_version INTEGER NOT NULL
      , authoring_updated_at TEXT);
    CREATE TABLE publications (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL UNIQUE,
        schema_revision TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'active', 'superseded', 'failed')),
        object_count INTEGER NOT NULL,
        link_count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        activated_at TEXT
      );
    CREATE TABLE extraction_pages (
        page_id TEXT PRIMARY KEY,
        wiki_path TEXT NOT NULL UNIQUE,
        content_fingerprint TEXT NOT NULL,
        schema_revision TEXT NOT NULL,
        last_successful_run_id TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
    CREATE TABLE object_instances (
        id TEXT PRIMARY KEY,
        object_type TEXT NOT NULL,
        primary_key_hash TEXT NOT NULL,
        primary_key_json TEXT NOT NULL,
        deepworks_json TEXT NOT NULL,
        origin TEXT NOT NULL,
        last_changed_publication_id TEXT NOT NULL REFERENCES publications(id), schema_revision TEXT, extraction_run_id TEXT,
        UNIQUE (object_type, primary_key_hash)
      );
    CREATE TABLE extracted_objects (
        object_key TEXT PRIMARY KEY,
        object_type TEXT NOT NULL,
        payload_json TEXT NOT NULL
      );
    CREATE TABLE object_properties (
        object_id TEXT NOT NULL REFERENCES object_instances(id) ON DELETE CASCADE,
        property_name TEXT NOT NULL,
        value_type TEXT NOT NULL,
        value_text TEXT,
        value_number REAL,
        value_boolean INTEGER,
        value_json TEXT,
        PRIMARY KEY (object_id, property_name)
      );
    CREATE TABLE link_instances (
        id TEXT PRIMARY KEY,
        link_type TEXT NOT NULL,
        link_identity_hash TEXT NOT NULL,
        source_object_id TEXT NOT NULL REFERENCES object_instances(id),
        target_object_id TEXT NOT NULL REFERENCES object_instances(id),
        source_primary_key_json TEXT NOT NULL,
        target_primary_key_json TEXT NOT NULL,
        deepworks_json TEXT NOT NULL,
        last_changed_publication_id TEXT NOT NULL REFERENCES publications(id), schema_revision TEXT, extraction_run_id TEXT,
        CHECK (source_object_id <> target_object_id),
        UNIQUE (link_type, link_identity_hash)
      );
    CREATE TABLE object_instance_sources (
        object_id TEXT NOT NULL REFERENCES object_instances(id) ON DELETE CASCADE,
        source_page TEXT NOT NULL,
        schema_revision TEXT NOT NULL,
        extraction_run_id TEXT NOT NULL,
        PRIMARY KEY (object_id, source_page)
      );
    CREATE TABLE link_instance_sources (
        link_id TEXT NOT NULL REFERENCES link_instances(id) ON DELETE CASCADE,
        source_page TEXT NOT NULL,
        schema_revision TEXT NOT NULL,
        extraction_run_id TEXT NOT NULL,
        PRIMARY KEY (link_id, source_page)
      );
    CREATE TABLE link_properties (
        link_id TEXT NOT NULL REFERENCES link_instances(id) ON DELETE CASCADE,
        property_name TEXT NOT NULL,
        value_type TEXT NOT NULL,
        value_text TEXT,
        value_number REAL,
        value_boolean INTEGER,
        value_json TEXT,
        PRIMARY KEY (link_id, property_name)
      );
    CREATE TABLE object_authoring (
        object_key TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        object_type TEXT NOT NULL,
        primary_key_json TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        revision INTEGER NOT NULL,
        updated_at TEXT NOT NULL
      );
    CREATE TABLE publication_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_id TEXT NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
        instance_kind TEXT NOT NULL CHECK (instance_kind IN ('object', 'link', 'candidate')),
        instance_key TEXT NOT NULL,
        schema_type TEXT NOT NULL,
        change_type TEXT NOT NULL CHECK (change_type IN ('added', 'modified', 'removed', 'unpublished')),
        before_json TEXT,
        after_json TEXT,
        source_page TEXT,
        evidence_json TEXT NOT NULL DEFAULT '[]',
        reason TEXT
      );
    CREATE TABLE ontology_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id TEXT,
        wiki_path TEXT,
        source_path TEXT,
        page_title TEXT,
        excerpt TEXT,
        run_id TEXT
      );
    """)
    now = "2026-09-24T00:00:00.000Z"
    pub_id = "xmind_compile_" + hashlib.sha1(src_name.encode()).hexdigest()[:12]
    schema_rev = hashlib.sha256(json.dumps(schema_out, ensure_ascii=False, sort_keys=True)
                                .encode("utf-8")).hexdigest()
    cur.execute("INSERT INTO schema_migrations VALUES (1, ?)", (now,))
    cur.execute("INSERT INTO publications VALUES (?,?,?,?,?,?,?,?)",
                (pub_id, pub_id, schema_rev, "active", len(objects), len(checked_links), now, now))
    cur.execute("INSERT INTO ontology_metadata (singleton, active_publication_id, schema_revision,"
                " authoring_revision, database_version, authoring_updated_at) VALUES (1,?,?,0,4,?)",
                (pub_id, schema_rev, now))
    cur.execute("INSERT OR REPLACE INTO extraction_pages VALUES (?,?,?,?,?,?)",
                ("page_xmind_" + hashlib.sha1(src_name.encode()).hexdigest()[:8],
                 f"raw/sources/{src_name}", hashlib.sha1(args.xmind.read_bytes()).hexdigest(),
                 schema_rev, pub_id, now))

    def instance_id(prefix: str, seed: str) -> str:
        return prefix + hashlib.sha1(seed.encode("utf-8")).hexdigest()

    obj_row_ids: dict = {}
    for obj in objects.values():
        props = obj["properties"]
        pk_json = json.dumps({"id": props["id"]}, ensure_ascii=False, sort_keys=True)
        pk_hash = hashlib.sha256(pk_json.encode("utf-8")).hexdigest()
        rid = instance_id("object_", f"{obj['_type']}|{pk_json}")
        obj_row_ids[props["id"]] = rid
        dw = {"source_page": f"raw/sources/{src_name}",
              "sources": [f"raw/sources/{src_name}"],
              "tags": [obj["_type"], props["title"]], "evidence": []}
        cur.execute("INSERT INTO object_instances VALUES (?,?,?,?,?,?,?,?,?)",
                    (rid, type_id_by_name[obj["_type"]], pk_hash, pk_json,
                     json.dumps(dw, ensure_ascii=False), "extracted", pub_id, schema_rev, pub_id))
        for k, v in props.items():
            if v is None or v == "":
                continue
            cur.execute("INSERT INTO object_properties VALUES (?,?,?,?,?,?,?)",
                        (rid, k, "text", str(v), None, None, None))
        cur.execute("INSERT INTO object_instance_sources VALUES (?,?,?,?)",
                    (rid, f"raw/sources/{src_name}", schema_rev, pub_id))
        cur.execute("INSERT INTO extracted_objects VALUES (?,?,?)",
                    (f"{type_id_by_name[obj['_type']]}|id=\"{props['id']}\"",
                     type_id_by_name[obj["_type"]],
                     json.dumps({"object_type_id": type_id_by_name[obj["_type"]],
                                 "primary_key": {"id": props["id"]},
                                 "properties": props,
                                 "deepworks": dw}, ensure_ascii=False)))

    link_type_id_by_name = {l["name"]: l["id"] for l in schema_baseline["link_types"]}
    for i, lk in enumerate(checked_links):
        s_pk = json.dumps({"id": lk["source"]}, ensure_ascii=False, sort_keys=True)
        t_pk = json.dumps({"id": lk["target"]}, ensure_ascii=False, sort_keys=True)
        identity = hashlib.sha256(f"{lk['link_type_id']}|{s_pk}|{t_pk}".encode("utf-8")).hexdigest()
        rid = instance_id("link_", f"{lk['link_type']}|{s_pk}|{t_pk}")
        dw = {"source_page": f"raw/sources/{src_name}",
              "sources": [f"raw/sources/{src_name}"], "tags": [lk["link_type"]], "evidence": []}
        cur.execute("INSERT INTO link_instances VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (rid, lk["link_type_id"], identity,
                     obj_row_ids[lk["source"]], obj_row_ids[lk["target"]], s_pk, t_pk,
                     json.dumps(dw, ensure_ascii=False), pub_id, schema_rev, pub_id))
        cur.execute("INSERT INTO link_instance_sources VALUES (?,?,?,?)",
                    (rid, f"raw/sources/{src_name}", schema_rev, pub_id))
    conn.commit()
    conn.close()

    print(f"objects: {len(objects)}  links: {len(checked_links)}")
    print(f"written: {foil_dir}")


if __name__ == "__main__":
    main()

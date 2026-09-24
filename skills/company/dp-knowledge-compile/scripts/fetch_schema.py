#!/usr/bin/env python3
"""Fetch ontology schema (object types + properties + link types) from a foil instance.

Usage:
  python fetch_schema.py --project-id <onto_project_id> --out <output.json>

Environment (injected, never hardcoded):
  FOIL_BASE_URL                 e.g. https://foil-test.deepexi.com
  FOIL_KNOWLEDGE_CENTER_TARGET  test | production
  DEEPWORKS_AGENT_FOIL[_TEST]_ACCOUNT / _PASSWORD

Output JSON shape:
  { onto_project_id, exported_at, source, object_types: [...], link_types: [...] }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foil_iam_auth import authenticate_from_runtime_environment  # noqa: E402

import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402


def http_get_json(base_url: str, path: str, query: dict, token: str) -> dict:
    qs = urllib.parse.urlencode(query)
    req = urllib.request.Request(
        f"{base_url}{path}?{qs}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_list(data: dict) -> list:
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, dict) and isinstance(inner.get("list"), list):
            return inner["list"]
        if isinstance(inner, list):
            return inner
        if isinstance(data.get("list"), list):
            return data["list"]
    return data if isinstance(data, list) else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", required=True, help="foil onto_project_id (uuid)")
    ap.add_argument("--out", required=True, help="output json path")
    args = ap.parse_args()

    base_url = (os.environ.get("FOIL_BASE_URL") or "").rstrip("/")
    if not base_url:
        print("error: FOIL_BASE_URL 未设置。本 skill 不内置环境地址，必须由运行环境注入。", file=sys.stderr)
        sys.exit(2)
    token = authenticate_from_runtime_environment(timeout_seconds=60, base_url=base_url)
    auth = token
    if auth.lower().startswith("bearer "):
        auth = auth[7:]

    obj_types = extract_list(http_get_json(
        base_url, "/ontology-types/object",
        {"onto_project_id": args.project_id, "pageSize": 200}, auth))
    link_types = extract_list(http_get_json(
        base_url, "/ontology-types/link",
        {"onto_project_id": args.project_id, "pageSize": 200}, auth))

    # 每个对象类型拉属性
    for ot in obj_types:
        props = extract_list(http_get_json(
            base_url, f"/ontology-types/object/{ot['id']}/properties",
            {"onto_project_id": args.project_id}, auth))
        ot["properties"] = props

    out = {
        "onto_project_id": args.project_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": base_url,
        "object_types": obj_types,
        "link_types": link_types,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"object_types: {len(obj_types)}  link_types: {len(link_types)}")
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()

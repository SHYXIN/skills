"""bp_state.py — bookpipe 状态文件管理（去重 + 已处理记录）。

状态文件: $BOOKPIPE_HOME/state/processed.json (默认 ~/bookpipe)
记录字段: forcoder_url, title, isbn, format, size_mb, suufun_uid,
          skill_name, commit, processed_at
"""
import json
import os
import tempfile
from pathlib import Path

VERSION = 1


def home() -> Path:
    return Path(os.environ.get("BOOKPIPE_HOME", str(Path.home() / "bookpipe")))


def state_path() -> Path:
    return home() / "state" / "processed.json"


def load() -> dict:
    p = state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            backup = p.with_suffix(".corrupt.json")
            p.replace(backup)
    return {"version": VERSION, "processed": []}


def save(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def norm_url(url: str) -> str:
    u = url.strip().rstrip("/")
    return u.lower()


def find_by_url(state: dict, url: str):
    key = norm_url(url)
    for rec in state.get("processed", []):
        if norm_url(rec.get("forcoder_url", "")) == key:
            return rec
    return None


def is_processed(state: dict, url: str = None, isbn: str = None) -> bool:
    if url and find_by_url(state, url):
        return True
    if isbn:
        for rec in state.get("processed", []):
            if rec.get("isbn") and rec["isbn"] == isbn:
                return True
    return False


def mark(state: dict, url: str, title: str = "", isbn: str = "", fmt: str = "",
         size_mb: float = None, uid: str = "", skill_name: str = "",
         commit: str = "") -> dict:
    """ Upsert 一条已处理记录（按 URL 去重），返回更新后的 state。"""
    rec = find_by_url(state, url) or {}
    rec.update({
        "forcoder_url": url.rstrip("/"),
        "title": title or rec.get("title", ""),
        "isbn": isbn or rec.get("isbn", ""),
        "format": fmt or rec.get("format", ""),
        "size_mb": size_mb if size_mb is not None else rec.get("size_mb"),
        "suufun_uid": uid or rec.get("suufun_uid", ""),
        "skill_name": skill_name or rec.get("skill_name", ""),
        "commit": commit or rec.get("commit", ""),
        "processed_at": rec.get("processed_at") or _today(),
    })
    state.setdefault("processed", [])
    state["processed"] = [r for r in state["processed"]
                          if norm_url(r.get("forcoder_url", "")) != norm_url(url)]
    state["processed"].append(rec)
    save(state)
    return state


def _today() -> str:
    from datetime import date
    return date.today().isoformat()

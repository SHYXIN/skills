#!/usr/bin/env python3
"""compile.py — 对话剧本编译器

把人可读写的对话剧本（MD）编译成两个衍生品：
  1. <name>.questions.json — 评测执行器格式的案例集
  2. <name>.preview.html   — 静态对话预览（单文件自包含）

用法:
  python compile.py <剧本.md> [-o 输出目录]

剧本格式见 references/script-format.md。衍生品永不手改；改剧本重编译。
"""
import argparse
import html
import json
import re
from pathlib import Path

CASE_HEAD = re.compile(r"^##\s+case:\s*(\S+)(?:\s+(.*))?$")
EXPECTED_FENCE = re.compile(r"```expected\s*\n(.*?)```", re.S)
META_LINE = re.compile(r"^meta:\s*(.*)$", re.M)
TAGS_LINE = re.compile(r"^tags:\s*(.*)$", re.M)
USER_TURN = re.compile(r"^\*\*用户\*\*[：:]\s*(.*)$", re.M)
AI_TURN = re.compile(r"\*\*AI\*\*[：:]?\s*\n?")


def parse_script(text: str) -> dict:
    script = {"title": "", "meta": "", "cases": []}
    title_m = re.search(r"^#\s+(.+)$", text, re.M)
    if title_m:
        script["title"] = title_m.group(1).strip()
    meta_m = META_LINE.search(text)
    if meta_m:
        script["meta"] = meta_m.group(1).strip()

    # 按 `## case:` 分块
    blocks = []
    cur = None
    for line in text.splitlines():
        m = CASE_HEAD.match(line)
        if m:
            cur = {"case_id": m.group(1), "desc": (m.group(2) or "").strip(), "body": []}
            blocks.append(cur)
        elif cur is not None:
            cur["body"].append(line)

    for b in blocks:
        body = "\n".join(b["body"])
        case = {
            "case_id": b["case_id"],
            "desc": b["desc"],
            "user_message": "",
            "expected_reply": "",
            "required": [],
            "forbidden": [],
            "max_chars": 0,
            "tags": [],
        }

        fence = EXPECTED_FENCE.search(body)
        fence_text = fence.group(1) if fence else ""
        after_fence = body[fence.end():] if fence else ""
        prose = body[: fence.start()] if fence else body

        # tags 行（围栏前后均可）
        tags_m = TAGS_LINE.search(prose) or TAGS_LINE.search(after_fence)
        if tags_m:
            case["tags"] = [t.strip() for t in tags_m.group(1).split(",") if t.strip()]
            if tags_m.re.search(prose):
                prose = prose[: tags_m.start()] + prose[tags_m.end():]

        # 用户轮 → AI 轮
        user_m = USER_TURN.search(prose)
        ai_m = AI_TURN.search(prose)
        if user_m:
            start = user_m.end()
            end = ai_m.start() if ai_m else len(prose)
            first = user_m.group(1).strip()
            rest = prose[start:end].strip()
            case["user_message"] = (first + "\n" + rest).strip() if rest else first
        if ai_m:
            case["expected_reply"] = prose[ai_m.end():].strip()

        # expected 围栏 → 判分标注
        if fence_text:
            for line in fence_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = re.split(r"[：:]", line, maxsplit=1)
                if len(parts) != 2:
                    continue
                key, val = parts
                key = key.strip().lower()
                val = val.strip()
                if key == "required":
                    case["required"] = [v.strip() for v in re.split(r"[,，]", val) if v.strip()]
                elif key == "forbidden":
                    case["forbidden"] = [v.strip() for v in re.split(r"[,，]", val) if v.strip()]
                elif key == "max_chars":
                    digits = re.sub(r"[^\d]", "", val)
                    case["max_chars"] = int(digits) if digits else 0

        script["cases"].append(case)
    return script


def to_questions(script: dict) -> dict:
    """编译为评测执行器格式（run_eval.py 兼容；额外字段执行器会忽略）。"""
    return {
        "cases": [
            {
                "case_id": c["case_id"],
                "user_message": c["user_message"],
                "expected": {
                    "required_markers": c["required"],
                    "forbidden_markers": c["forbidden"],
                    "answer_max_chars": c["max_chars"],
                },
                "tags": c["tags"],
            }
            for c in script["cases"]
        ]
    }


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def render_html(script: dict) -> str:
    """静态对话分镜：用户在右、AI 在左、判分点高亮。单文件自包含。"""
    cards = []
    for c in script["cases"]:
        reply = esc(c["expected_reply"])
        for m in c["required"]:
            reply = reply.replace(esc(m), f"<mark>{esc(m)}</mark>")
        marks = []
        if c["required"]:
            marks.append(f"<span class='pill req'>必现 {'、'.join(esc(m) for m in c['required'])}</span>")
        if c["forbidden"]:
            marks.append(f"<span class='pill forbid'>禁词 {'、'.join(esc(m) for m in c['forbidden'])}</span>")
        if c["max_chars"]:
            marks.append(f"<span class='pill len'>≤{c['max_chars']} 字</span>")
        marks_html = "".join(marks)
        desc = f"<span class='desc'>{esc(c['desc'])}</span>" if c["desc"] else ""
        cards.append(f"""
  <section class="case">
    <div class="case-head"><code>{esc(c['case_id'])}</code> {desc} {marks_html}</div>
    <div class="turn user"><div class="bubble">{esc(c['user_message'])}</div></div>
    <div class="turn ai"><div class="bubble">{reply}</div></div>
  </section>""")

    meta = f"<p class='meta'>{esc(script['meta'])}</p>" if script["meta"] else ""
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{esc(script['title'])} — 预期对话预览</title>
<style>
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background:#f5f6f8; margin:0; padding:24px; color:#24292f; }}
  h1 {{ font-size:20px; }}
  .meta {{ color:#57606a; font-size:13px; }}
  .case {{ background:#fff; border:1px solid #d8dee4; border-radius:10px; padding:16px 20px; margin:16px 0; }}
  .case-head {{ font-size:13px; color:#57606a; margin-bottom:12px; }}
  .case-head code {{ background:#f0f2f4; padding:2px 6px; border-radius:4px; }}
  .desc {{ margin-left:6px; }}
  .turn {{ display:flex; margin:10px 0; }}
  .turn.user {{ justify-content:flex-end; }}
  .turn.ai {{ justify-content:flex-start; }}
  .bubble {{ max-width:72%; padding:10px 14px; border-radius:14px; white-space:pre-wrap; line-height:1.6; font-size:14px; }}
  .user .bubble {{ background:#1f6feb; color:#fff; border-bottom-right-radius:4px; }}
  .ai .bubble {{ background:#eef1f4; border-bottom-left-radius:4px; }}
  mark {{ background:#fff3ad; padding:0 2px; border-radius:3px; }}
  .pill {{ display:inline-block; font-size:11px; border-radius:10px; padding:1px 8px; margin-left:4px; }}
  .pill.req {{ background:#dafbe1; color:#116329; }}
  .pill.forbid {{ background:#ffebe9; color:#cf222e; }}
  .pill.len {{ background:#ddf4ff; color:#0969da; }}
</style>
</head>
<body>
<h1>{esc(script['title'])} — 预期对话预览</h1>
{meta}
{''.join(cards)}
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="对话剧本 → 案例 JSON + 对话 HTML")
    ap.add_argument("script", help="剧本 MD 路径")
    ap.add_argument("-o", "--out", default=".", help="输出目录（默认当前目录）")
    args = ap.parse_args()

    src = Path(args.script)
    if not src.exists():
        sys_exit(f"剧本不存在: {src}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    script = parse_script(src.read_text(encoding="utf-8"))
    if not script["cases"]:
        sys_exit("剧本中未发现任何 '## case:' 案例")

    stem = src.stem
    q_path = out / f"{stem}.questions.json"
    h_path = out / f"{stem}.preview.html"
    q_path.write_text(json.dumps(to_questions(script), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    h_path.write_text(render_html(script), encoding="utf-8")
    print(f"cases: {len(script['cases'])}")
    print(f"  {q_path}")
    print(f"  {h_path}")


def sys_exit(msg: str):
    print(f"error: {msg}", file=__import__("sys").stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()

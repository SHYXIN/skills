"""bp_run.py — bookpipe 主编排 CLI。

子命令:
  list                    抓 forcoder 首页今日书目，分级预勾选，标记已处理
  run <url>               单本全链路: 书页→captcha暂停→goto→suufun→下载→解压
  mark <url> [options]    记录已处理（转换完成后由 agent 调用）
  status                  状态汇总
  url <task-name>         取某中转任务的新签名直链（48h 时效）

依赖: 同目录 bp_state.py / bp_suufun.py; opencli + Chrome (session: bookpipe);
7-Zip (C:/Program Files/7-Zip/7z.exe); curl。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bp_state
import bp_suufun
from bp_suufun import PausePoint

SEVENZIP = (os.environ.get("BOOKPIPE_SEVENZIP")
            or shutil.which("7z")
            or r"C:\Program Files\7-Zip\7z.exe")

DEFAULT_CONFIG = {
    "auto_keywords": ["ai", "agent", "llm", "machine learning", "deep learning",
                      "python", "rust", "c++", "java", "javascript", "typescript",
                      "programming", "software", "engineering", "developer",
                      "data", "cloud", "devops", "kubernetes", "security",
                      "architecture", "sql", "web"],
    "formats_ok": ["pdf", "epub"],
    "formats_never_auto": ["mp4", "video", "mkv"],
}


def home() -> Path:
    return bp_state.home()


def load_config() -> dict:
    p = home() / "config.json"
    if p.exists():
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except json.JSONDecodeError:
            pass
    return dict(DEFAULT_CONFIG)


# ---------- forcoder 首页 ----------

CF_MARKERS = ("正在进行安全验证", "Just a moment", "challenges.cloudflare")


def wait_cf_pass(timeout: int = 45) -> bool:
    """等 Cloudflare 检查页自动放行。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        try:
            state = bp_suufun.page_state()
        except RuntimeError:
            continue  # 页面导航中（body 未就绪），重试
        html = json.dumps(state, ensure_ascii=False)
        if not any(m in html for m in CF_MARKERS):
            return True
        time.sleep(3)
    return False


def parse_entry(text: str) -> dict:
    """从 article.innerText 解析元信息。"""
    isbn = ""
    m = re.search(r"ISBN:\s*([-\dX]+)", text, re.I)
    if m:
        isbn = m.group(1)
    fmt = ""
    m = re.search(r"\b(PDF|EPUB|MOBI|AZW3|MP4|MKV|VIDEO)\b", text, re.I)
    if m:
        fmt = m.group(1).lower()
    size_mb = None
    m = re.search(r"([\d.]+)\s*(MB|GB)", text, re.I)
    if m:
        size_mb = float(m.group(1)) * (1024 if m.group(2).upper() == "GB" else 1)
    date = ""
    m = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    if m:
        date = m.group(1)
    return {"isbn": isbn, "format": fmt, "size_mb": size_mb, "date": date}


def fetch_list() -> list:
    """浏览器打开 forcoder 首页，提取全部 article.latestPost 条目。"""
    bp_suufun.open_url("https://forcoder.net/", settle=3)
    if not wait_cf_pass():
        raise PausePoint("forcoder 首页 Cloudflare 检查未自动通过，请人工过验证码后重跑")
    raw = bp_suufun.browser_eval(
        "(function(){const arts=document.querySelectorAll('article.latestPost');"
        "return JSON.stringify(Array.from(arts).map(a=>{"
        "const link=a.querySelector('h2.title a')||a.querySelector('a');"
        "return {title:link?link.textContent.trim():'',"
        "url:link?link.href:'',text:a.innerText};}));})()")
    entries = json.loads(raw) if isinstance(raw, str) else (raw or [])
    for e in entries:
        e.update(parse_entry(e.get("text", "")))
    return entries


def classify(entries: list, cfg: dict) -> list:
    """分级: pick(预勾选) / candidate(可手动勾) / skip(永不自动)。"""
    state = bp_state.load()
    kws = [k.lower() for k in cfg.get("auto_keywords", [])]
    never = set(cfg.get("formats_never_auto", []))
    ok_fmts = set(cfg.get("formats_ok", []))
    for e in entries:
        e["processed"] = bp_state.is_processed(state, url=e.get("url"),
                                               isbn=e.get("isbn") or None)
        fmt = (e.get("format") or "").lower()
        if fmt in never or e["processed"]:
            e["tier"] = "skip"
        elif fmt in ok_fmts and any(k in e.get("title", "").lower() for k in kws):
            e["tier"] = "pick"
        else:
            e["tier"] = "candidate"
    return entries


# ---------- 单本链路 ----------

def resolve_rapidgator(book_url: str) -> str:
    """打开书页，等 captcha 过，找 DOWNLOAD 区的 /goto/ 链接并解析最终 URL。"""
    bp_suufun.open_url(book_url, settle=3)
    if not wait_cf_pass():
        raise PausePoint("书页 Cloudflare 未通过，人工过一下再重跑")
    raw = bp_suufun.browser_eval(
        "(function(){const t=document.body.innerText;"
        "if(/Resolve the captcha/i.test(t))return JSON.stringify({captcha:true});"
        "const links=Array.from(document.querySelectorAll('a[href*=\"/goto/\"]'));"
        "if(!links.length)return JSON.stringify({captcha:false,goto:''});"
        "return JSON.stringify({captcha:false,goto:links[0].href});})()")
    info = json.loads(raw) if isinstance(raw, str) else raw
    if info.get("captcha"):
        raise PausePoint(f"书页有 hCaptcha，请人工点掉后重跑: {book_url}")
    goto = info.get("goto", "")
    if not goto:
        raise RuntimeError(f"书页未找到 /goto/ 链接: {book_url}")
    # /goto/ 是跳转链接：在新 tab 打开它，读最终 location
    bp_suufun.open_url(goto, settle=4)
    final = bp_suufun.page_state().get("url", "")
    if "rapidgator" not in final.lower():
        raise RuntimeError(f"/goto/ 解析结果不是 rapidgator: {final}")
    return final


def pipeline_run(book_url: str) -> dict:
    """单本全链路到下载解压完成。返回摘要 dict。"""
    print(f"[1/5] 解析 rapidgator 链接: {book_url}")
    rg_url = resolve_rapidgator(book_url)
    print(f"      -> {rg_url}")

    print("[2/5] suufun 提交检测…")
    task = bp_suufun.submit_link(rg_url)
    if not task:
        raise RuntimeError("提交检测后未在任务列表找到该链接")
    print(f"      -> 检测任务 uid={task.get('uid', '?')}")
    print("[3/5] 等待检测完成（扣流量）…")
    task = bp_suufun.wait_check_done(rg_url)
    name = task.get("name", "")
    print(f"      -> 提取成功: {name}")

    print("[4/5] 添加到中转队列并等待完成…")
    bp_suufun.add_to_transfer()
    done = bp_suufun.wait_transfer_done(name)
    dl_url = done.get("d", "")
    if not dl_url:
        raise RuntimeError(f"中转完成但无直链: {name}")

    print("[5/5] 下载并解压…")
    downloads = home() / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]+", "_", name) or "book"
    rar = downloads / (safe + ".rar")
    r = subprocess.run(["curl", "-sSL", "-o", str(rar), dl_url],
                       capture_output=True, text=True)
    if r.returncode != 0 or not rar.exists() or rar.stat().st_size < 1000:
        raise RuntimeError(f"下载失败: {r.stderr[:200]}")
    print(f"      -> 已下载 {rar.stat().st_size // 1024} KB")

    extracted = home() / "extracted" / safe
    extracted.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([SEVENZIP, "x", "-y", f"-o{extracted}", str(rar)],
                       capture_output=True, text=True)
    files = [str(p) for p in extracted.rglob("*") if p.is_file()]
    docs = [f for f in files if f.lower().endswith((".pdf", ".epub", ".mobi", ".azw3"))]
    if r.returncode != 0 or not docs:
        raise RuntimeError(f"解压失败或无文档: {r.stderr[:200]}")

    return {"book_url": book_url, "rg_url": rg_url, "name": name,
            "uid": done.get("uid", ""), "dl_url": dl_url,
            "dir": str(extracted), "docs": docs}


# ---------- CLI ----------

def cmd_list() -> int:
    cfg = load_config()
    entries = classify(fetch_list(), cfg)
    icons = {"pick": "[x]", "candidate": "[ ]", "skip": "-  "}
    print(f"\nforcoder 今日书目 ({len(entries)} 条，[x]=预勾选 [ ]=可手动勾 -=跳过)\n")
    for e in entries:
        tag = "已处理" if e["processed"] else ""
        size = f"{e['size_mb']:.0f}MB" if e.get("size_mb") else "?"
        print(f"{icons[e['tier']]} {(e.get('format') or '?').upper():5s} {size:>7s}  "
              f"{e.get('title', '')[:70]}  {tag}")
        print(f"      {e.get('url', '')}")
    picks = [e for e in entries if e["tier"] == "pick"]
    print(f"\n预勾选 {len(picks)} 本。跑单本: python bp_run.py run <url>")
    return 0


def cmd_run(url: str) -> int:
    state = bp_state.load()
    if bp_state.is_processed(state, url=url):
        rec = bp_state.find_by_url(state, url)
        print(f"已处理过: {rec.get('title', url)}")
        print(f"skill={rec.get('skill_name')} commit={rec.get('commit')}")
        return 0
    try:
        summary = pipeline_run(url)
    except PausePoint as e:
        print(f"\n== 暂停: {e}")
        print("人工步骤完成后重跑同一命令即可继续。")
        return 2
    print("\n== 完成，摘要 ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n下一步: 在 docs 上跑 book-to-skill 转换，然后:")
    print(f"  python bp_run.py mark {url} --title <标题> --isbn <ISBN> "
          f"--skill-name <名> --commit <hash>")
    return 0


def cmd_mark(url: str, args) -> int:
    state = bp_state.load()
    bp_state.mark(state, url, title=args.title, isbn=args.isbn,
                  fmt=args.format, uid=args.uid, skill_name=args.skill_name,
                  commit=args.commit)
    print(f"已记录: {url}")
    return 0


def cmd_status() -> int:
    state = bp_state.load()
    recs = state.get("processed", [])
    print(f"共处理 {len(recs)} 本:")
    for r in recs:
        print(f"  {r.get('processed_at', '?')}  {r.get('title', '?')[:60]}"
              f"  skill={r.get('skill_name', '?')}")
    return 0


def cmd_url(name: str) -> int:
    dl = bp_suufun.get_download_url(name)
    print(dl if dl else f"未找到 COMPLETE 任务: {name}（可能已过期或未完成）")
    return 0 if dl else 1


def main():
    import argparse
    ap = argparse.ArgumentParser(prog="bp_run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="抓今日书目")
    p_run = sub.add_parser("run", help="单本全链路")
    p_run.add_argument("url")
    p_mark = sub.add_parser("mark", help="记录已处理")
    p_mark.add_argument("url")
    p_mark.add_argument("--title", default="")
    p_mark.add_argument("--isbn", default="")
    p_mark.add_argument("--format", default="")
    p_mark.add_argument("--uid", default="")
    p_mark.add_argument("--skill-name", dest="skill_name", default="")
    p_mark.add_argument("--commit", default="")
    sub.add_parser("status", help="状态汇总")
    p_url = sub.add_parser("url", help="取某任务新直链")
    p_url.add_argument("name")
    args = ap.parse_args()

    if args.cmd == "list":
        sys.exit(cmd_list())
    elif args.cmd == "run":
        sys.exit(cmd_run(args.url))
    elif args.cmd == "mark":
        sys.exit(cmd_mark(args.url, args))
    elif args.cmd == "status":
        sys.exit(cmd_status())
    elif args.cmd == "url":
        sys.exit(cmd_url(args.name))


if __name__ == "__main__":
    main()

"""bp_suufun.py — suufun 中转服务的浏览器桥接层。

所有 API 调用通过 opencli 操控用户已登录的 Chrome（session: bookpipe）完成：
suufun 的认证态在浏览器里，脚本不碰任何凭据。

探明的 API 细节（2026-10 实测，勿重新逆向）:
- POST /api/task/v2/search_check         检测任务列表（body: {page,size}）
- POST /api/task/v2/search_task          转存任务列表（body: {page,page_size,steps,value}）
  steps 必须是 uppercase 字符串数组，如 ["COMPLETE"] / ["WAIT_ALLOT","URL","DL"]
- 检测页点「提取链接」提交；行内点「添加到中转队列」触发中转（内部调 /api/task/download_task）
- 完成后任务对象的 d 字段 = 主线路签名直链（含 ts 参数，有时效，约 48h 有效）
"""
import json
import shutil
import subprocess
import time

SESSION = "bookpipe"
OPENCLI = shutil.which("opencli") or shutil.which("opencli.cmd") or "opencli.cmd"
CHECK_URL = "https://suufun.com/check"
ALL_STEPS = ["WAIT_CHECK", "CHECK", "CHECK_FAILED", "WAIT_ALLOT", "URL",
             "URL_FAILED", "DL", "DL_FAILED", "PAUSE", "COMPLETE",
             "USER_NOT_ENOUGH", "NOT_ENOUGH", "TASK_EXISTS", "CANCELED",
             "MAINTAIN", "DL_REQ_FAILED", "INSTANT", "PROCESSING",
             "WAIT_DL", "POSTPONE", "POSTPONE_DL"]


class PausePoint(Exception):
    """需要人工介入（如 hCaptcha）。"""


def _opencli(args: list) -> str:
    r = subprocess.run([OPENCLI] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.strip()


def browser_eval(js: str):
    out = _opencli(["browser", "eval", "--session", SESSION, js])
    try:
        env = json.loads(out)
    except json.JSONDecodeError:
        raise RuntimeError(f"opencli 返回非 JSON: {out[:200]}")
    if not env.get("ok"):
        raise RuntimeError(f"opencli 错误: {json.dumps(env.get('error'), ensure_ascii=False)[:300]}")
    return env.get("data")


def open_url(url: str, settle: float = 2.5):
    _opencli(["browser", "open", "--session", SESSION, url])
    time.sleep(settle)


def page_state() -> dict:
    return browser_eval(
        "(function(){return JSON.stringify({url:location.href,"
        "title:document.title,"
        "captcha:/Resolve the captcha/i.test(document.body.innerText)});})()")


# ---------- suufun API ----------

def _post(path: str, body: dict):
    js = ("(async function(){const r=await fetch('" + path + "',{method:'POST',"
          "credentials:'include',headers:{'Content-Type':'application/json'},"
          "body:JSON.stringify(" + json.dumps(body) + ")});"
          "return await r.text();})()")
    raw = browser_eval(js)
    return json.loads(raw)


def search_check() -> list:
    d = _post("/api/task/v2/search_check", {"page": 1, "size": 20})
    return (d.get("data") or {}).get("check_tasks") or []


def search_tasks(steps: list) -> list:
    d = _post("/api/task/v2/search_task",
              {"page": 1, "page_size": 50, "steps": steps, "value": ""})
    return (d.get("data") or {}).get("tasks") or []


def submit_link(rapidgator_url: str) -> dict:
    """在检测页粘贴链接并点「提取链接」。返回新建的 check 任务。"""
    open_url(CHECK_URL)
    # React 受控输入：必须用原生 setter + input 事件
    browser_eval(
        "(function(){const ta=document.querySelector('textarea');"
        "if(!ta)return 'no textarea';"
        "const setter=Object.getOwnPropertyDescriptor("
        "window.HTMLTextAreaElement.prototype,'value').set;"
        "setter.call(ta," + json.dumps(rapidgator_url) + ");"
        "ta.dispatchEvent(new Event('input',{bubbles:true}));"
        "return 'filled';})()")
    browser_eval(
        "(function(){const b=Array.from(document.querySelectorAll('button'))"
        ".find(x=>/提取链接/.test(x.textContent||''));"
        "if(!b)return 'button not found';b.click();return 'clicked';})()")
    time.sleep(2)
    for task in search_check():
        if task.get("link") == rapidgator_url:
            return task
    return {}


def wait_check_done(rapidgator_url: str, timeout: int = 300,
                    interval: int = 10) -> dict:
    """轮询检测任务直到 ftime 就绪（提取成功）。"""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        for task in search_check():
            if task.get("link") == rapidgator_url:
                last = task
                if task.get("ftime"):
                    return task
                break
        time.sleep(interval)
    raise TimeoutError(f"检测超时({timeout}s)，最后状态: "
                       f"{(last or {}).get('step') or '未找到任务'}")


def add_to_transfer() -> None:
    """检测页找到「提取成功」行，点「添加到中转队列」。"""
    open_url(CHECK_URL)
    r = browser_eval(
        "(function(){const tr=Array.from(document.querySelectorAll('table tr'))"
        ".find(r=>/提取成功/.test(r.innerText));"
        "if(!tr)return 'no completed row';"
        "const btn=Array.from(tr.querySelectorAll('a,button,span'))"
        ".find(e=>/添加到中转队列/.test(e.textContent||''));"
        "if(!btn)return 'button not found';btn.click();return 'clicked';})()")
    if r != "clicked":
        raise RuntimeError(f"添加到中转队列失败: {r}")
    time.sleep(3)


def wait_transfer_done(name: str, timeout: int = 600,
                       interval: int = 15) -> dict:
    """轮询转存任务直到 COMPLETE，返回任务对象（含 d 直链）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for t in search_tasks(["COMPLETE"]):
            if t.get("name") == name:
                return t
        time.sleep(interval)
    raise TimeoutError(f"中转超时({timeout}s): {name}")


def get_download_url(name: str) -> str:
    for t in search_tasks(["COMPLETE"]):
        if t.get("name") == name and t.get("d"):
            return t["d"]
    return ""

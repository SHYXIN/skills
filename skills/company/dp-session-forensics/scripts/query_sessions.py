#!/usr/bin/env python3
"""DeepWorks 会话取证：查询 opencode.db 会话历史，定位 agent 行为分歧。

用法:
  python query_sessions.py [--env prod|dev] list [--limit 20] [--dir KEYWORD]
  python query_sessions.py [--env prod|dev] dump <session_id> [--roles user,assistant] [--out FILE]
  python query_sessions.py [--env prod|dev] injections <session_id>
  python query_sessions.py [--env prod|dev] reasoning <session_id> [--grep KEYWORD]
  python query_sessions.py [--env prod|dev] export <session_id> [--out DIR]   # html + jsonl
环境:
  --env prod  正式环境库（默认）: ~/AppData/Roaming/com.deepexi.deepworks/...
  --env dev   dev 测试环境库:     ~/AppData/Roaming/com.deepexi.deepworks.test.dev/...
  --db PATH   任意路径直接覆盖上述两者
已知 schema 坑（勿绕过封装手敲 SQL）:
  - role/agent/model 都藏在 message.data 的 JSON 里，表上没有这些列
  - parts 存在独立的 part 表（按 message_id 关联），不在 message.data 里
  - part.data 也是 JSON，reasoning/text/tool/step-start 是不同 part 类型
  - 必须 fetch 完整 data 后 json.loads，substr 截断会产生断 JSON
"""
import argparse
import datetime
import json
import os
import sqlite3
import sys

_ENV_DBS = {
    "prod": os.path.expandvars(
        r"C:/Users/DEEPEXI/AppData/Roaming/com.deepexi.deepworks"
        r"/deepworks-engine-data/xdg/data/opencode/opencode.db"
    ),
    "dev": os.path.expandvars(
        r"C:/Users/DEEPEXI/AppData/Roaming/com.deepexi.deepworks.test.dev"
        r"/deepworks-dev-data/xdg/data/opencode/opencode.db"
    ),
}
DEFAULT_ENV = "prod"


def connect(db_path):
    if not os.path.exists(db_path):
        sys.exit(f"DB 不存在: {db_path}")
    # 只读模式打开，杜绝误写
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def parse_data(raw):
    """完整 data JSON 解析；失败返回 None 而不是炸掉整个查询。"""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def cmd_list(args):
    con = connect(args.db)
    sql = ("SELECT id, title, directory, time_created, model, agent "
           "FROM session")
    params = []
    if args.dir:
        sql += " WHERE directory LIKE ?"
        params.append(f"%{args.dir}%")
    sql += " ORDER BY time_created DESC LIMIT ?"
    params.append(args.limit)
    rows = con.execute(sql, params).fetchall()
    import datetime
    for r in rows:
        ts = datetime.datetime.fromtimestamp(r["time_created"] / 1000)
        model = (parse_data(r["model"]) or {}).get("modelID", "") if r["model"] else ""
        print(f"{r['id']}  {ts:%m-%d %H:%M}  [{model}]  {r['title'][:50]}  ({r['directory']})")
    con.close()


def iter_messages(con, session_id):
    """产出 (message_id, ts, message_json, parts_json_list)。

    注意：parts 存在 part 表（按 message_id 关联），不在 message.data JSON 里。
    """
    cur = con.execute(
        "SELECT id, time_created, data FROM message "
        "WHERE session_id=? ORDER BY time_created", (session_id,))
    for row in cur:
        j = parse_data(row["data"])
        if j is None:
            continue
        parts = []
        for (pd,) in con.execute(
                "SELECT data FROM part WHERE message_id=? ORDER BY time_created",
                (row["id"],)):
            pj = parse_data(pd)
            if pj is not None:
                parts.append(pj)
        yield row["id"], row["time_created"], j, parts


def cmd_dump(args):
    con = connect(args.db)
    roles = set(args.roles.split(",")) if args.roles else None
    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    import datetime
    for mid, ts, j, parts in iter_messages(con, args.session_id):
        role = j.get("role", "?")
        if roles and role not in roles:
            continue
        t = datetime.datetime.fromtimestamp(ts / 1000)
        print(f"\n===== [{role}] {mid} @ {t:%H:%M:%S} =====", file=out)
        print(f"agent={j.get('agent')} model={j.get('modelID', j.get('model'))}", file=out)
        sys_j = j.get("system")
        if sys_j:
            print("--- system 注入 ---", file=out)
            print(sys_j if isinstance(sys_j, str) else json.dumps(sys_j, ensure_ascii=False, indent=2), file=out)
        for p in parts:
            if p.get("type") == "text":
                print(p.get("text", ""), file=out)
    if args.out:
        out.close()
        print(f"已写出 {args.out}")
    con.close()


def cmd_injections(args):
    """找出带 Knowledge 注入（explicitly selected 字样）的轮次。"""
    con = connect(args.db)
    marker = "explicitly selected"
    hit = 0
    for mid, ts, j, parts in iter_messages(con, args.session_id):
        sys_j = j.get("system")
        if isinstance(sys_j, str) and marker in sys_j:
            hit += 1
            ws = ""
            i = sys_j.find("workspacePath")
            if i >= 0:
                ws = sys_j[i:i + 120].replace("\n", " ")
            print(f"turn {mid}: role={j.get('role')} agent={j.get('agent')}")
            print(f"  {ws}")
    print(f"\n共 {hit} 轮带 Knowledge 注入")
    con.close()


def cmd_reasoning(args):
    """提取各轮 reasoning，用于对比两个会话的行为分歧。"""
    con = connect(args.db)
    for mid, ts, j, parts in iter_messages(con, args.session_id):
        if j.get("role") != "assistant":
            continue
        for p in parts:
            if p.get("type") == "reasoning":
                txt = p.get("text", "")
                if args.grep and args.grep not in txt:
                    continue
                print(f"===== reasoning @ {mid} =====")
                print(txt)
                print()
    con.close()


def fmt_ts(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%dT%H:%M:%S")


def load_session_and_messages(con, session_id):
    """返回 (session_row, [(mid, ts, msg_json, parts_list), ...])；会话不存在则退出。"""
    srow = con.execute("SELECT * FROM session WHERE id=?", (session_id,)).fetchone()
    if srow is None:
        sys.exit(f"会话不存在: {session_id}")
    msgs = list(iter_messages(con, session_id))
    return srow, msgs


def write_jsonl(path, session_id, msgs):
    with open(path, "w", encoding="utf-8") as f:
        for mid, ts, j, parts in msgs:
            rec = {
                "mid": mid,
                "time": fmt_ts(ts),
                "role": j.get("role"),
                "agent": j.get("agent"),
                "model": j.get("modelID", j.get("model")),
                "system": j.get("system"),
                "parts": parts,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


import html as html_mod


def esc(s):
    return html_mod.escape(str(s))


def write_html(path, srow, session_id, msgs):
    """生成自包含 HTML：左侧轮次树导航（搜索+角色过滤）+ 右侧阅读区。

    参考 pi export-html 的布局。DeepWorks 会话数据是线性的（无分支 parentId），
    但按对话轮次分组：每轮以 user 消息为根，后续 assistant/工具消息为其子节点，
    折叠成树状展示。
    """
    t0 = datetime.datetime.fromtimestamp(srow["time_created"] / 1000)
    n_user = sum(1 for _, _, j, _ in msgs if j.get("role") == "user")
    n_asst = sum(1 for _, _, j, _ in msgs if j.get("role") == "assistant")

    # 预生成每条消息的导航摘要
    nav_items = []
    for idx, (mid, ts, j, parts) in enumerate(msgs):
        role = j.get("role", "?")
        first_text = ""
        for p in parts:
            if p.get("type") == "text" and p.get("text", "").strip():
                first_text = p["text"].strip()
                break
        if not first_text and any(p.get("type") == "tool" for p in parts):
            first_text = "[工具调用]"
        nav_items.append({
            "idx": idx, "mid": mid, "role": role, "time": fmt_ts(ts)[11:],
            "summary": first_text.replace("\n", " ")[:60] or "(无文本)",
            "has_sys": bool(j.get("system")),
            "n_think": sum(1 for p in parts if p.get("type") == "reasoning"),
            "n_tool": sum(1 for p in parts if p.get("type") == "tool"),
        })

    # 按轮次分组：user 消息开新一轮，其后非 user 消息归入该轮
    turns = []  # [{root: item_idx, children: [item_idx, ...]}]
    for it in nav_items:
        if it["role"] == "user" or not turns:
            turns.append({"root": it["idx"], "children": []})
        else:
            turns[-1]["children"].append(it["idx"])
    turn_json = json.dumps(turns, ensure_ascii=False)

    nav_html = []
    for ti, turn in enumerate(turns):
        root = nav_items[turn["root"]]
        n_children = len(turn["children"])
        n_msgs = 1 + n_children
        badge = []
        if root["has_sys"]:
            badge.append("⚡")
        tb_think = sum(nav_items[c]["n_think"] for c in turn["children"])
        tb_tool = sum(nav_items[c]["n_tool"] for c in turn["children"])
        if tb_think:
            badge.append(f"🧠{tb_think}")
        if tb_tool:
            badge.append(f"🔧{tb_tool}")
        badge_s = f'<span class="nav-badge">{"".join(badge)}</span>' if badge else ""
        # 轮次节点（可折叠）
        nav_html.append(
            f'<div class="nav-turn" data-turn="{ti}">'
            f'<span class="nav-caret">▸</span>'
            f'<span class="nav-role">轮{ti + 1}</span>'
            f'<span class="nav-time">{root["time"]}</span>'
            f'<span class="nav-turn-count">{n_msgs}条</span>{badge_s}'
            f'<div class="nav-sum">{esc(root["summary"])}</div></div>'
        )
        # 轮内消息子节点
        children_idxs = [turn["root"]] + turn["children"]
        for ci, cidx in enumerate(children_idxs):
            it = nav_items[cidx]
            is_last = ci == len(children_idxs) - 1
            prefix_cls = "nav-tree-last" if is_last else "nav-tree-mid"
            badge = []
            if it["has_sys"]:
                badge.append("⚡")
            if it["n_think"]:
                badge.append(f"🧠{it['n_think']}")
            if it["n_tool"]:
                badge.append(f"🔧{it['n_tool']}")
            badge_s = f'<span class="nav-badge">{"".join(badge)}</span>' if badge else ""
            nav_html.append(
                f'<div class="nav-item {prefix_cls} nav-{esc(it["role"])} child-of-turn-{ti}" '
                f'data-idx="{it["idx"]}" data-role="{esc(it["role"])}" data-turn="{ti}">'
                f'<span class="nav-branch"></span>'
                f'<span class="nav-role">{esc(it["role"][:4])}</span>'
                f'<span class="nav-time">{it["time"]}</span>{badge_s}'
                f'<div class="nav-sum">{esc(it["summary"])}</div></div>'
            )
    nav_html_s = "\n".join(nav_html)
    nav_json = json.dumps(nav_items, ensure_ascii=False)

    parts_css = """
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:ui-monospace,'Cascadia Code',Menlo,Consolas,'DejaVu Sans Mono',monospace;
      font-size:12px;line-height:1.55;color:#d4d4d4;background:#18181e;}
    #app{display:flex;min-height:100vh;}
    #nav{width:380px;min-width:260px;max-width:560px;background:#1e1e24;flex-shrink:0;
      display:flex;flex-direction:column;position:sticky;top:0;height:100vh;border-right:1px solid #444;}
    #nav-resizer{width:5px;flex-shrink:0;position:sticky;top:0;height:100vh;cursor:col-resize;
      background:transparent;border-right:1px solid transparent;}
    #nav-resizer:hover{background:#3a3a4a;border-right-color:#666;}
    .nav-head{padding:8px 10px;border-bottom:1px solid #3a3a44;flex-shrink:0;}
    #nav-search{width:100%;padding:4px 8px;font-size:11px;font-family:inherit;background:#18181e;
      color:#d4d4d4;border:1px solid #555;border-radius:3px;}
    .nav-filters{margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;}
    .fbtn{font-size:10px;padding:2px 8px;background:#18181e;border:1px solid #5f87ff;border-radius:3px;
      color:#d4d4d4;cursor:pointer;font-family:inherit;}
    .fbtn:hover{border-color:#00d7ff;}
    .fbtn.on{background:#3a3a4a;border-color:#00d7ff;color:#00d7ff;}
    #nav-list{flex:1;overflow-y:auto;}
    .nav-item{padding:5px 10px 5px 26px;cursor:pointer;border-bottom:1px solid #26262e;position:relative;}
    .nav-item:hover{background:#282832;}
    .nav-item.active{background:#3a3a4a;box-shadow:inset 2px 0 0 #00d7ff;}
    .nav-item.nav-user .nav-role{color:#8abeb7;}
    .nav-item.nav-assistant .nav-role{color:#b5bd68;}
    .nav-turn{padding:6px 10px;cursor:pointer;background:#232329;border-bottom:1px solid #2e2e38;
      border-top:1px solid #2e2e38;user-select:none;}
    .nav-turn:hover{background:#282832;}
    .nav-turn .nav-role{color:#00d7ff;}
    .nav-turn-count{font-size:9px;color:#666;margin-left:6px;}
    .nav-caret{display:inline-block;color:#808080;font-size:9px;margin-right:6px;
      transition:transform .12s;}
    .nav-turn.closed .nav-caret{transform:rotate(-90deg);}
    .nav-branch{position:absolute;left:14px;top:0;bottom:0;width:12px;}
    .nav-branch::before{content:'';position:absolute;left:0;top:0;bottom:0;width:1px;background:#3a3a44;}
    .nav-branch::after{content:'';position:absolute;left:0;top:50%;width:8px;height:1px;background:#3a3a44;}
    .nav-item.nav-user .nav-branch::before{background:#4a5a52;}
    .nav-tree-last .nav-branch::before{bottom:50%;}
    .nav-role{font-weight:bold;font-size:10px;}
    .nav-time{font-size:9px;color:#666;margin-left:6px;}
    .nav-badge{font-size:9px;color:#9575cd;float:right;}
    .nav-sum{font-size:10px;color:#999;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    .nav-item.nav-user .nav-sum{color:#c5c8c6;}
    .nav-turn .nav-sum{color:#b0b8c0;}
    #status{padding:3px 10px;font-size:10px;color:#808080;flex-shrink:0;border-top:1px solid #3a3a44;}
    #content{flex:1;min-width:0;overflow-y:auto;height:100vh;padding:16px 24px;}
    #content-inner{max-width:860px;margin:0 auto;}
    .header{background:#1e1e24;border-radius:6px;padding:14px 18px;margin-bottom:16px;}
    .header h1{font-size:14px;color:#00d7ff;margin:0 0 8px;}
    .meta{font-size:11px;color:#808080;}
    .meta b{color:#b5bd68;font-weight:normal;}
    .msg{border-radius:6px;padding:12px 16px;margin-bottom:12px;scroll-margin-top:12px;}
    .msg.user{background:#343541;}
    .msg.assistant{background:#1e1e24;border-left:3px solid #b5bd68;}
    .msghead{font-size:11px;color:#666;margin-bottom:6px;}
    .msghead .role{font-weight:bold;}
    .msg.user .role{color:#8abeb7;}
    .msg.assistant .role{color:#b5bd68;}
    details{margin:8px 0;border:1px solid #3a3a44;border-radius:4px;}
    summary{cursor:pointer;padding:5px 10px;font-size:11px;color:#9575cd;user-select:none;}
    details[open] summary{border-bottom:1px solid #3a3a44;}
    pre{margin:0;padding:10px;font-size:11px;white-space:pre-wrap;word-break:break-word;color:#a0a8b0;
      max-height:420px;overflow:auto;}
    .text{white-space:pre-wrap;word-break:break-word;}
    .hidden{display:none;}
    mark{background:#665c1e;color:#ffff87;}
    #mobile-btn{display:none;position:fixed;top:10px;left:10px;z-index:99;background:#1e1e24;
      color:#d4d4d4;border:1px solid #5f87ff;border-radius:3px;padding:4px 10px;cursor:pointer;}
    @media (max-width:760px){
      #nav{position:fixed;left:0;top:0;z-index:50;display:none;}
      #nav.open{display:flex;}
      #nav-resizer{display:none;}
      #mobile-btn{display:block;}
      #content{padding:40px 10px 16px;}
    }
    """
    parts_js = """
    const NAV_DATA = __NAV_DATA__;
    const TURN_DATA = __TURN_DATA__;
    const items = Array.from(document.querySelectorAll('.nav-item'));
    const turns = Array.from(document.querySelectorAll('.nav-turn'));
    const searchBox = document.getElementById('nav-search');
    let filterMode = 'all';
    let activeIdx = -1;
    const closedTurns = new Set();

    function turnVisible(ti){
      // 轮次可见性：按过滤快照判断（不看 DOM），折叠隐藏子项不影响轮节点本身
      return filterHitTurns.has(ti);
    }

    const filterHitTurns = new Set();
    function applyView(){
      const q = searchBox.value.toLowerCase();
      let shown = 0;
      items.forEach(el=>{
        const idx = +el.dataset.idx;
        const role = el.dataset.role;
        const info = NAV_DATA[idx];
        let vis = filterMode==='all' || (filterMode==='user' && role==='user')
               || (filterMode==='asst' && role==='assistant')
               || (filterMode==='sys' && info.has_sys);
        if(vis && q && !el.textContent.toLowerCase().includes(q)) vis=false;
        el.classList.toggle('hidden', !vis);
        if(vis){ shown++; filterHitTurns.add(el.dataset.turn); }
      });
      // 应用轮次折叠：搜索/过滤时强制全部展开
      const forceOpen = q.length > 0 || filterMode !== 'all';
      turns.forEach(tel=>{
        const ti = tel.dataset.turn;
        const closed = !forceOpen && closedTurns.has(ti);
        tel.classList.toggle('closed', closed);
        if(closed){
          document.querySelectorAll('.nav-item[data-turn="'+ti+'"]')
            .forEach(el=>el.classList.add('hidden'));
        }
      });
      // 收起无命中的轮次（用快照判断，折叠不影响）
      turns.forEach(tel=>{
        tel.classList.toggle('hidden', !turnVisible(tel.dataset.turn));
      });
      document.getElementById('status').textContent = shown + ' / ' + items.length + ' 条消息';
    }

    function setActive(idx){
      items.forEach(el=>el.classList.remove('active'));
      const el = document.querySelector('.nav-item[data-idx="'+idx+'"]');
      if(el){
        // 若所在轮次被折叠，先展开
        const ti = el.dataset.turn;
        const tel = document.querySelector('.nav-turn[data-turn="'+ti+'"]');
        if(tel && closedTurns.has(ti)){ closedTurns.delete(ti); applyView(); }
        el.classList.add('active'); el.scrollIntoView({block:'nearest'});
      }
    }

    items.forEach(el=>el.addEventListener('click',()=>{
      const idx = +el.dataset.idx;
      setActive(idx);
      const msg = document.getElementById('msg-'+idx);
      if(msg) msg.scrollIntoView({block:'start'});
    }));

    // 轮次点击 = 折叠/展开；双击正文首条
    turns.forEach(tel=>tel.addEventListener('click',()=>{
      const ti = tel.dataset.turn;
      if(closedTurns.has(ti)) closedTurns.delete(ti); else closedTurns.add(ti);
      applyView();
    }));
    turns.forEach(tel=>tel.addEventListener('dblclick',()=>{
      const ti = +tel.dataset.turn;
      const rootIdx = TURN_DATA[ti].root;
      setActive(rootIdx);
      const msg = document.getElementById('msg-'+rootIdx);
      if(msg) msg.scrollIntoView({block:'start'});
    }));

    searchBox.addEventListener('input', applyView);
    document.querySelectorAll('.fbtn').forEach(b=>b.addEventListener('click',()=>{
      document.querySelectorAll('.fbtn').forEach(x=>x.classList.remove('on'));
      b.classList.add('on');
      filterMode = b.dataset.mode;
      applyView();
    }));

    // 右侧滚动时同步高亮左侧；滚入新轮次时自动展开该轮、折叠其他
    const content = document.getElementById('content');
    let autoFold = true;
    content.addEventListener('scroll', ()=>{
      let cur = -1;
      for (const el of document.querySelectorAll('.msg')){
        if(el.getBoundingClientRect().top < 120) cur = +el.dataset.idx; else break;
      }
      if(cur>=0 && cur!==activeIdx){
        activeIdx=cur; setActive(cur);
        if(autoFold){
          const el = document.querySelector('.nav-item[data-idx="'+cur+'"]');
          if(el){
            const curTurn = el.dataset.turn;
            let changed = false;
            closedTurns.forEach(ti=>{ if(ti!==curTurn){ closedTurns.delete(ti); changed=true; } });
            if(!closedTurns.has(curTurn)){ closedTurns.add(curTurn); changed=true; }
            if(changed) applyView();
            setActive(cur);
          }
        }
      }
    });

    // 拖拽调宽
    (()=>{
      const nav = document.getElementById('nav');
      const rz = document.getElementById('nav-resizer');
      let dragging = false;
      rz.addEventListener('mousedown', ()=>dragging=true);
      window.addEventListener('mousemove', e=>{
        if(!dragging) return;
        const w = Math.min(560, Math.max(260, e.clientX));
        nav.style.width = w+'px';
      });
      window.addEventListener('mouseup', ()=>dragging=false);
    })();

    document.getElementById('mobile-btn').addEventListener('click',()=>{
      document.getElementById('nav').classList.toggle('open');
    });

    applyView();
    """
    parts_js = parts_js.replace("__NAV_DATA__", nav_json).replace("__TURN_DATA__", turn_json)

    out = []
    out.append(f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>会话 {esc(session_id)}</title>
<style>{parts_css}</style></head>
<body>
<button id="mobile-btn">☰ 导航</button>
<div id="app">
<nav id="nav">
  <div class="nav-head">
    <input type="text" id="nav-search" placeholder="搜索消息...">
    <div class="nav-filters">
      <button class="fbtn on" data-mode="all">全部</button>
      <button class="fbtn" data-mode="user">User</button>
      <button class="fbtn" data-mode="asst">Assistant</button>
      <button class="fbtn" data-mode="sys">有注入</button>
    </div>
  </div>
  <div id="nav-list">
{nav_html_s}
  </div>
  <div id="status"></div>
</nav>
<div id="nav-resizer"></div>
<main id="content"><div id="content-inner">
<div class="header"><h1>{esc(srow['title'])}</h1>
<div class="meta">session <b>{esc(session_id)}</b><br>
工作区 <b>{esc(srow['directory'])}</b> ｜ 创建 <b>{t0:%Y-%m-%d %H:%M}</b> ｜
消息 <b>{len(msgs)}</b>（user {n_user} / assistant {n_asst}）</div></div>""")

    for idx, (mid, ts, j, parts) in enumerate(msgs):
        role = j.get("role", "?")
        model = j.get("modelID", j.get("model"))
        if isinstance(model, dict):
            model = model.get("modelID", "")
        model_s = f" · {model}" if model else ""
        out.append(f'<div class="msg {esc(role)}" id="msg-{idx}" data-idx="{idx}">')
        out.append(f'<div class="msghead"><span class="role">{esc(role)}</span>'
                   f' {fmt_ts(ts)}{esc(model_s)} · {esc(mid)}</div>')
        sys_j = j.get("system")
        if sys_j:
            sys_s = sys_j if isinstance(sys_j, str) else json.dumps(sys_j, ensure_ascii=False, indent=2)
            out.append(f'<details><summary>⚡ system 注入（{len(sys_s)} 字符）</summary>'
                       f'<pre>{esc(sys_s)}</pre></details>')
        for p in parts:
            ptype = p.get("type")
            if ptype == "text":
                txt = p.get("text", "")
                if txt.strip():
                    out.append(f'<div class="text">{esc(txt)}</div>')
            elif ptype == "reasoning":
                out.append(f'<details><summary>🧠 思考过程</summary>'
                           f'<pre>{esc(p.get("text", ""))}</pre></details>')
            elif ptype == "tool":
                tool = p.get("tool") or p.get("state", {}).get("tool") or "?"
                pj = json.dumps(p, ensure_ascii=False, indent=2)
                out.append(f'<details><summary>🔧 工具: {esc(tool)}</summary>'
                           f'<pre>{esc(pj)}</pre></details>')
        out.append('</div>')
    out.append('</div></main></div>')
    out.append(f'<script>{parts_js}</script></body></html>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def sanitize_filename(s, max_len=60):
    """清洗标题为安全文件名：去掉路径分隔符与 Windows 非法字符。"""
    for ch in '<>:"/\\|?*\n\r\t':
        s = s.replace(ch, " ")
    s = s.strip().strip(".")
    return s[:max_len].strip() or "untitled"


def cmd_export(args):
    """导出会话为 .html（人读交互）+ .jsonl（机器分析）双格式到 tmp 目录。

    文件名：日期_时间_会话标题.html / .jsonl，如
    2026-09-16_1638_连接MES查看当前告警.html
    """
    con = connect(args.db)
    srow, msgs = load_session_and_messages(con, args.session_id)
    outdir = args.out
    os.makedirs(outdir, exist_ok=True)
    t0 = datetime.datetime.fromtimestamp(srow["time_created"] / 1000)
    stem = f"{t0:%Y-%m-%d_%H%M}_{sanitize_filename(srow['title'])}"
    jsonl_path = os.path.join(outdir, f"{stem}.jsonl")
    html_path = os.path.join(outdir, f"{stem}.html")
    write_jsonl(jsonl_path, args.session_id, msgs)
    write_html(html_path, srow, args.session_id, msgs)
    con.close()
    print(f"已导出 {len(msgs)} 条消息（session {args.session_id}）：")
    print(f"  {html_path}")
    print(f"  {jsonl_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", choices=sorted(_ENV_DBS), default=DEFAULT_ENV,
                    help="DeepWorks 环境（决定默认 db 路径，--db 可覆盖）")
    ap.add_argument("--db", default=None, help="opencode.db 路径（覆盖 --env）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="列出最近会话")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--dir", help="按 directory 关键字过滤")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("dump", help="导出会话完整消息")
    p.add_argument("session_id")
    p.add_argument("--roles", help="逗号分隔，如 user,assistant")
    p.add_argument("--out", help="写出文件（默认 stdout）")
    p.set_defaults(fn=cmd_dump)

    p = sub.add_parser("injections", help="找带 Knowledge 注入的轮次")
    p.add_argument("session_id")
    p.set_defaults(fn=cmd_injections)

    p = sub.add_parser("reasoning", help="提取 assistant reasoning")
    p.add_argument("session_id")
    p.add_argument("--grep", help="只显示含关键字的 reasoning")
    p.set_defaults(fn=cmd_reasoning)

    p = sub.add_parser("export", help="导出会话为 html + jsonl 双格式")
    p.add_argument("session_id")
    p.add_argument("--out", default="tmp", help="输出目录（默认 tmp/）")
    p.set_defaults(fn=cmd_export)

    args = ap.parse_args()
    if args.db is None:
        args.db = _ENV_DBS[args.env]
    args.fn(args)


if __name__ == "__main__":
    main()

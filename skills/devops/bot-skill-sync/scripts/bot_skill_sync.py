#!/usr/bin/env python3
"""bot_skill_sync.py — 同步本地技能到 bot 宿主（open-superagent DSH）。

宿主地址不内置，从环境变量取（BOT_SKILL_SYNC_SSH_HOST 必填）。

子命令:
  list                     对比本地技能源目录与远端宿主技能清单
  push <skill> --src DIR   覆盖推送（保护远端 .env / DEPLOY-NOTES.md）
  remove <skill> --yes     软删远端技能目录到 /tmp 备份
"""

import argparse
import hashlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SSH_HOST = os.environ.get("BOT_SKILL_SYNC_SSH_HOST", "")
REMOTE_DIR = os.environ.get("BOT_SKILL_SYNC_REMOTE_DIR", "/data/dsh-home/skills")
CHANGELOG = os.environ.get("BOT_SKILL_SYNC_CHANGELOG", "/data/SKILL-CHANGELOG.md")

PROTECT_FILES = {".env", "DEPLOY-NOTES.md"}
SKIP_PUSH = {".env", "DEPLOY-NOTES.md", "__pycache__"}


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def require_host():
    if not SSH_HOST:
        die("BOT_SKILL_SYNC_SSH_HOST 未设置（宿主地址查 memory 或问用户）")


def sh(cmd: list, check=True, input_text=None) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, input=input_text)
    if check and r.returncode != 0:
        die(f"cmd failed: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout


def ssh(*args, check=True) -> str:
    return sh(["ssh", SSH_HOST, *args], check=check)


def scp(src: str, dst: str):
    sh(["scp", "-r", src, dst])


def md5_of_remote(path: str) -> str:
    out = ssh(f"md5sum {path} 2>/dev/null || true", check=False).strip()
    return out.split()[0] if out else ""


def md5_of_local(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else ""


def resolve_src(args) -> Path:
    src = Path(args.src or os.environ.get("BOT_SKILL_SYNC_LOCAL_ROOT", "") or "")
    if not src or not src.is_dir():
        die(f"本地技能源目录不存在: {src}（用 --src 指定 deepsense-skills/wangxin 路径）")
    return src


def remote_list() -> list:
    out = ssh(f"ls -1 {REMOTE_DIR} 2>/dev/null || true", check=False)
    return [l.strip() for l in out.splitlines() if l.strip()]


def git_rev(src: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(src), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else "norev"


# ---------------- list ----------------

def cmd_list(args):
    require_host()
    src = resolve_src(args)
    remote = remote_list()
    local = sorted(p.name for p in src.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    print(f"远端宿主 ({SSH_HOST}:{REMOTE_DIR})  {len(remote)} 个:")
    for name in remote:
        env = "有.env" if ssh(f"test -f {REMOTE_DIR}/{name}/.env && echo y", check=False).strip() else "无.env"
        note = ssh(f"tail -1 {REMOTE_DIR}/{name}/DEPLOY-NOTES.md 2>/dev/null || true", check=False).strip()
        local_mark = "本地有仓" if name in local else "本地无仓"
        print(f"  {name:32s} {local_mark}  {env}  {note[:60]}")
    only_local = [n for n in local if n not in remote]
    if only_local:
        print(f"\n本地有、远端没有: {', '.join(only_local)}")


# ---------------- push ----------------

def cmd_push(args):
    require_host()
    src_root = resolve_src(args)
    skill = args.skill
    skill_src = src_root / skill
    if not (skill_src / "SKILL.md").exists():
        die(f"本地技能不存在或缺 SKILL.md: {skill_src}")
    remote_skill = f"{REMOTE_DIR}/{skill}"
    exists = ssh(f"test -d {remote_skill} && echo y || true", check=False).strip() == "y"

    env_hash_before = md5_of_remote(f"{remote_skill}/.env") if exists else ""

    if exists:
        # 备份远端独有文件清单（不做整目录备份，push 保留远端 .env/DEPLOY-NOTES）
        pass
    # 远端同名子目录先删再整体复制，远端独有顶层文件不动
    ssh(f"mkdir -p {remote_skill}")
    for child in skill_src.iterdir():
        if child.name in SKIP_PUSH or child.name.startswith("."):
            continue
        remote_child = f"{remote_skill}/{child.name}"
        if child.is_dir():
            ssh(f"rm -rf {remote_child}")
            scp(str(child) + "/", f"{SSH_HOST}:{remote_child}/")
        else:
            scp(str(child), f"{SSH_HOST}:{remote_child}/")

    env_hash_after = md5_of_remote(f"{remote_skill}/.env")
    if env_hash_before and env_hash_before != env_hash_after:
        die(f"远端 .env 校验失败（md5 变化）！立即恢复: ssh {SSH_HOST} 'cd {remote_skill} && git checkout -- .env' 或从备份还原")

    note = f"{datetime.now():%Y-%m-%d %H:%M} push from local by bot-skill-sync (rev {git_rev(src_root)})"
    ssh(f"echo '{note}' >> {remote_skill}/DEPLOY-NOTES.md")
    print(f"OK pushed {skill} -> {SSH_HOST}:{remote_skill}")


# ---------------- remove ----------------

def cmd_remove(args):
    require_host()
    skill = args.skill
    remote_skill = f"{REMOTE_DIR}/{skill}"
    if ssh(f"test -d {remote_skill} && echo y || true", check=False).strip() != "y":
        die(f"远端技能不存在: {remote_skill}")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"/tmp/{skill}-removed-{ts}"
    note = f"{datetime.now():%Y-%m-%d %H:%M} removed by bot-skill-sync -> {backup}"
    ssh(f"echo '{note}' >> {remote_skill}/DEPLOY-NOTES.md 2>/dev/null || true")
    ssh(f"mv {remote_skill} {backup}")
    ssh(f"echo '{note}' >> {CHANGELOG}")
    print(f"OK removed {skill} -> {SSH_HOST}:{backup}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="对比本地与远端技能清单")
    p_list.add_argument("--src", help="本地技能源目录（deepsense-skills/wangxin）")

    p_push = sub.add_parser("push", help="覆盖推送一个技能")
    p_push.add_argument("skill")
    p_push.add_argument("--src", help="本地技能源目录")

    p_rm = sub.add_parser("remove", help="软删远端技能（mv 到 /tmp 备份）")
    p_rm.add_argument("skill")
    p_rm.add_argument("--yes", action="store_true", required=True)

    args = ap.parse_args()
    {"list": cmd_list, "push": cmd_push, "remove": cmd_remove}[args.cmd](args)


if __name__ == "__main__":
    main()

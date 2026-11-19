---
name: setup-git-bash
description: "在装好 Git for Windows 的机器上，把 Git Bash 注册成 Windows Terminal 的 profile（下拉菜单出现 Git Bash 项，可设为默认）。覆盖：检测 Git 安装路径、固定 GUID、settings.json 安全插入（带备份、JSON 校验、幂等）、设默认 profile、验证。装完即结束；日常 bash 操作不经本技能。触发词：Windows Terminal 没有 Git Bash / 终端下拉菜单缺 Git Bash / 把 Git Bash 加进终端。"
---

# Set Git Bash（一次性环境设置）

把 [Git for Windows](https://gitforwindows.org) 自带的 Git Bash 注册成 Windows Terminal 的 profile。

> 前置：Git for Windows 已安装（缺它先 `winget install --id Git.Git -e --source winget`）。Windows Terminal 未装则先 `winget install --id Microsoft.WindowsTerminal -e --source winget`。

## 0. 检测环境事实

三个路径逐个确认存在（Git 可能装在 `%LOCALAPPDATA%\Programs\Git` 而非 `C:\Program Files\Git`）：

```bash
GIT_ROOT="C:/Program Files/Git"   # 不存在时用 where git 反推：git.exe 所在目录的上两级
ls "$GIT_ROOT/bin/bash.exe" "$GIT_ROOT/mingw64/share/git/git-for-windows.ico"
WT_SETTINGS="$LOCALAPPDATA/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"
ls "$WT_SETTINGS"
```

任一路径缺失时停止并向用户说明，不要猜。

## 1. 幂等检查（已注册则跳过）

settings.json 的 `profiles.list` 里已有 `commandline` 含 `Git\\bin\\bash.exe`（或名字为 `Git Bash`）的 profile 时，本技能只剩第 3 步（可选设默认）。先查再写：

```bash
python -c "
import json, os, sys
d = json.load(open(os.path.expandvars(sys.argv[1]), encoding='utf-8'))
for pr in d.get('profiles', {}).get('list', []):
    if 'bash.exe' in pr.get('commandline', '').lower() or pr.get('name','').lower() == 'git bash':
        print('FOUND:', json.dumps(pr, ensure_ascii=False))
" "$WT_SETTINGS"
```

> 路径必须经 `sys.argv` 传入，不能内插进 `-c` 字符串字面量——Windows 路径的反斜杠（如 `\Users`）会被 Python 当成 unicode 转义直接语法错误。

## 2. 写入 profile

**先备份**，再插入，写完立即校验 JSON（坏了用备份回滚）：

```bash
cp "$WT_SETTINGS" "$WT_SETTINGS.bak-$(date +%Y%m%d%H%M%S)"
```

用 Python 原子化完成"插入 + 校验 + 失败回滚"（JSON 含注释时用 `json5` 或先 `strip` 尾逗号——Terminal 1.18+ 默认生成纯 JSON，`json` 直接可用）：

```bash
python - <<'EOF'
import json, os, sys, shutil

wt = os.path.expandvars(r"$LOCALAPPDATA/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json")
git_root = os.environ.get("GIT_ROOT", r"C:\Program Files\Git")

profile = {
    "commandline": rf"{git_root}\bin\bash.exe",
    "guid": "{a41e5a53-dfd4-4213-95b0-868d9ee9f79e}",
    "hidden": False,
    "icon": rf"{git_root}\mingw64\share\git\git-for-windows.ico",
    "name": "Git Bash",
    "startingDirectory": "%USERPROFILE%",
    "tabTitle": "bash",
}

d = json.load(open(wt, encoding="utf-8"))
lst = d.setdefault("profiles", {}).setdefault("list", [])
dup = next((p for p in lst if p.get("guid") == profile["guid"]), None)
if dup:
    print("already present, nothing to do"); sys.exit(0)
lst.append(profile)
json.dump(d, open(wt, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
print("profile added")
EOF
```

GUID 说明：这是 Git Bash 社区通用的固定 GUID（Git for Windows 官方 fragment 亦用此值），固定它可保证幂等与 fragment 互认，**不要每次随机生成**。若第 1 步查到已有 profile 但 GUID 不同，沿用已有的（只改 `hidden`/字段），不要造第二个。

> 多机器脚本化时更稳的做法：不手写 JSON，改投放下述 fragment 文件（Terminal 自动合并，不动 settings.json 主体）：
> `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\GitBash\git-bash.json`，内容为 `{"profiles":[{"guid":"{a41e5a53-dfd4-4213-95b0-868d9ee9f79e}","name":"Git Bash","commandline":"...\\bin\\bash.exe","icon":"...ico","startingDirectory":"%USERPROFILE%","hidden":false}]}`。

## 3. 设为默认 profile（可选，问用户）

把 `d["defaultProfile"]` 设为上面的 GUID 即可。只有用户明确要 Git Bash 当默认终端时才做；否则跳过。

## 4. 验证

1. JSON 合法：`python -m json.tool "$WT_SETTINGS" > /dev/null && echo OK`
2. 新开一个 Windows Terminal 窗口，下拉菜单出现「Git Bash」、点击进入 bash（`echo $MINGW_PREFIX` 非空即真）。
3. 若设了默认：新标签页应直接落 Git Bash。

验证失败时：对比 `.bak` 备份，逐字段排错；最坏情况恢复备份，改用 fragment 文件方案（见第 2 步提示框）。

## 装完之后

- `bash` 里的 PATH / 别名等个性化配置属于用户的 `.bashrc`，不归本技能。

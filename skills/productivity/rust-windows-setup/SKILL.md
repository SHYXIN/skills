---
name: rust-windows-setup
description: "Windows 上安装 Rust 工具链（含需要 C 编译器的项目，如 rusqlite）。覆盖 rustup 国内镜像加速、Missing manifest 修复、MinGW/MSVC 选择、dlltool/ld 的 PATH 坑。在 Windows 配 Rust 环境或遇到 'Missing manifest' / 'dlltool not found' 报错时使用。"
---

# Windows 上稳健安装 Rust 工具链

## 这个 skill 解决什么

在 Windows 上配 Rust，真正的坑往往不是 Rust 本身，而是三件事：

1. **rustup 官方源下载慢/易断** → 安装被超时打断 → 工具链只装了一半 → 报
   `error: Missing manifest in toolchain 'stable-x86_64-pc-windows-gnu'`。
2. **需要 C 编译器**（rusqlite、openssl-sys 等 bundled 特性会编译 C 代码），
   而 Windows 上要么用 MinGW 的 gcc，要么用 MSVC 的 cl.exe，二者都有 PATH / 环境变量坑。
3. **镜像、PATH 没设成「全局」**（只写在 `~/.bashrc`），导致换 PowerShell / cmd /
   VS Code 终端就失效。

本 skill 给出一次性到位的做法，避免反复重装。

## 何时使用

- 新机器（尤其是国内 Windows）要从零装 Rust。
- 编译报 `Missing manifest`。
- 编译含 C 依赖的 crate 时报 `dlltool.exe: program not found` 或找不到链接器。
- 你想把 Rust 环境做成「任意终端开箱即用」。

## 总原则

- **镜像和环境变量都设成 Windows 用户级（注册表），不要只写 `~/.bashrc`**——
  `~/.bashrc` 只在 git-bash 里生效，`rustup.exe` 是 Windows 程序，PowerShell/cmd
  读不到。
- **优先用 MSVC**（Rust 在 Windows 的默认 target），最省心；MinGW 是备选。

---

## 步骤一：设 rustup 国内镜像（防下载超时，关键）

用 PowerShell 写进 Windows 用户环境变量（用 .NET 写，避免 `setx` 的 1024 字符截断，
也避免 git-bash 把 `$` 当变量展开）：

```powershell
[Environment]::SetEnvironmentVariable("RUSTUP_DIST_SERVER", "https://rsproxy.cn", "User")
[Environment]::SetEnvironmentVariable("RUSTUP_UPDATE_ROOT", "https://rsproxy.cn/rustup", "User")
```

> 验证（新开任意终端后）：
> ```powershell
> (Get-ItemProperty 'HKCU:\Environment').RUSTUP_DIST_SERVER
> ```
> 应返回 `https://rsproxy.cn`。

## 步骤二：设 cargo crates 镜像（加速依赖下载）

新建 / 追加 `~/.cargo/config.toml`（cargo 直接读这个文件，与 shell 无关）：

```toml
[source.crates-io]
replace-with = "rsproxy-sparse"
[source.rsproxy-sparse]
registry = "sparse+https://rsproxy.cn/index/"
[registries.rsproxy]
index = "https://rsproxy.cn/crates.io-index"
```

## 步骤三：装 Rust

```powershell
# 用国内镜像后的 rustup-init（下载快）
# 推荐直接装 MSVC 默认 target，见步骤四
winget install -e --id Rust.Rustup
# 或手动：
#  curl -sSf https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe -o rustup-init.exe
#  ./rustup-init.exe -y
```

## 步骤四：选 C 工具链（二选一，推荐 A）

### 方案 A（推荐）：MSVC —— 最省心

一个 Visual Studio Build Tools 安装包同时给你 C 编译器 `cl.exe` 和链接器
`link.exe`，且 `rustc` 会通过 vswhere 自动定位 `link.exe`，**不需要手动配 PATH**。

```powershell
# 1. 装 VC++ Build Tools（含 MSVC v143 + Windows SDK，需管理员/UAC 弹窗）
winget install -e --id Microsoft.VisualStudio.2022.BuildTools `
  --override "--add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.26100 --includeRecommended --passive"

# 2. 装并切到 msvc target
rustup toolchain install stable-x86_64-pc-windows-msvc
rustup default stable-x86_64-pc-windows-msvc

# 3.（可选）卸掉 gnu，避免以后混淆
rustup toolchain uninstall stable-x86_64-pc-windows-gnu
```

之后 `cargo build` / `cargo install` **不用加 `--target`**，任意终端直接可用。

### 方案 B（备选）：MinGW gnu —— 必须处理 PATH

```powershell
# 1. 装 MSYS2
winget install -e --id MSYS2.MSYS2 --accept-package-agreements --accept-source-agreements --silent
# 2. 在 MSYS2 里装 mingw gcc + binutils（注意：第一次 pacman -Syu 会弹“关闭终端”确认，
#    非交互会杀掉进程；用 -Sy 只刷新再 -S 装，避开它）
#    C:\msys64\usr\bin\bash.exe -lc "pacman -Sy --noconfirm; pacman -S --needed --noconfirm mingw-w64-x86_64-gcc mingw-w64-x86_64-binutils"
# 3. 关键：把 C:\msys64\mingw64\bin 加进 Windows 用户 PATH（否则 dlltool/ld 找不到）
```

把 `C:\msys64\mingw64\bin` 加进 Windows 用户 PATH（PowerShell，避免截断）：

```powershell
$p = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $p.Contains("msys64\mingw64\bin")) {
  [Environment]::SetEnvironmentVariable("Path", ($p.TrimEnd(";") + ";C:\msys64\mingw64\bin"), "User")
  Write-Host "已添加 C:\msys64\mingw64\bin 到用户 PATH"
}
```

## 一键脚本（可选）

本 skill 附带 `scripts/setup-rust-windows.ps1`，管理员 PowerShell 下一键完成：设镜像、装 rustup、装 VC++ Build Tools、切 msvc target、验证。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-rust-windows.ps1
```

> VS Build Tools 安装会弹 UAC 要管理员权限；其余步骤普通用户即可。

## 步骤五：验证

新开任意终端（让环境变量生效）：

```bash
rustc --version
cargo --version
cargo build        # 或 cargo build --target x86_64-pc-windows-gnu（方案 B）
```

---

## 排错速查表

| 报错 / 现象 | 根因 | 解决办法 |
|---|---|---|
| `Missing manifest in toolchain 'stable-x86_64-pc-windows-gnu'` | 工具链下载被超时/中断，只装了一半 | 先设好 rustup 镜像（步骤一），再 `rustup toolchain uninstall <名字>` → `rustup toolchain install <名字> --profile minimal` 干净重装 |
| 在 `~` 敲 `cargo` 出帮助，进项目目录敲 `cargo` 就报 Missing manifest | **假象**：`cargo`（无参数）只打印帮助、不调 rustc，所以没暴露坏工具链；进项目才真去解析工具链才炸 | 直接看 `rustc --version`，坏就是坏，按上一条重装 |
| `error: error calling dlltool 'dlltool.exe': program not found` | MinGW 的 `dlltool` 不在 PATH（`cc` 链接阶段要显式调它） | 方案 B 时确认 `C:\msys64\mingw64\bin` 已在 Windows 用户 PATH（步骤四方案 B.3） |
| `cargo build` 卡在 `downloading N components` 很久 | rustup 官方源慢 | 一定是镜像没生效，复查步骤一（HKCU\Environment 里是否有 rsproxy 值） |
| git-bash 里跑 `reg query` / `powershell` 报语法错 | git-bash 把反斜杠、`$` 转义/展开了 | `powershell -Command` 的参数用**单引号**包住；正则里的 `\m` 非法，改用 `.Contains()` 做字面子串判断 |

## 备注

- 镜像环境变量（步骤一、二）**只需设一次**，写进注册表后所有新终端自动继承。
- 若机器在海外、官方源不慢，可跳过镜像步骤，但 PATH（方案 A 不用管 / 方案 B 必须）仍然关键。
-  motivating 案例：给 `mco-org/squad`（Rust + rusqlite bundled）加 pi 支持时，
  整条链就是按本 skill 踩坑并验证通过的。

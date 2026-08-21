# setup-rust-windows.ps1
# 一键在 Windows 上配置 Rust（MSVC 路线，最省心）。
# 用法（建议管理员 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File setup-rust-windows.ps1

$ErrorActionPreference = "Stop"

function Set-UserEnv {
    param($Name, $Value)
    $cur = [Environment]::GetEnvironmentVariable($Name, "User")
    if ($cur -ne $Value) {
        [Environment]::SetEnvironmentVariable($Name, $Value, "User")
        Write-Host "已设置用户环境变量 $Name = $Value"
    } else {
        Write-Host "用户环境变量 $Name 已是 $Value（跳过）"
    }
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

# 1. rustup 国内镜像（防下载超时）
Set-UserEnv "RUSTUP_DIST_SERVER" "https://rsproxy.cn"
Set-UserEnv "RUSTUP_UPDATE_ROOT" "https://rsproxy.cn/rustup"

# 2. cargo crates 镜像
$cargoCfg = "$env:USERPROFILE\.cargo\config.toml"
$toml = @"
[source.crates-io]
replace-with = "rsproxy-sparse"
[source.rsproxy-sparse]
registry = "sparse+https://rsproxy.cn/index/"
[registries.rsproxy]
index = "https://rsproxy.cn/crates.io-index"
"@
if (Test-Path $cargoCfg) {
    Write-Host "已存在 $cargoCfg，跳过写入（如需更新请手动合并上面的 [source] 段）"
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $cargoCfg) | Out-Null
    Set-Content -Path $cargoCfg -Value $toml -Encoding UTF8
    Write-Host "已写入 $cargoCfg"
}

# 3. 装 rustup（如未装）
if (-not (Get-Command rustup -ErrorAction SilentlyContinue)) {
    Write-Host "安装 rustup ..."
    winget install -e --id Rust.Rustup --accept-package-agreements --accept-source-agreements | Out-Null
    Refresh-Path
} else {
    Write-Host "rustup 已安装（跳过）"
}

# 4. 装 VC++ Build Tools（MSVC + Windows SDK，需管理员/UAC）
if (-not (Get-Command cl -ErrorAction SilentlyContinue)) {
    Write-Host "安装 Visual Studio Build Tools (MSVC + Windows SDK) ... 可能弹 UAC"
    winget install -e --id Microsoft.VisualStudio.2022.BuildTools `
        --override "--add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.26100 --includeRecommended --passive"
    Refresh-Path
} else {
    Write-Host "cl.exe 已存在，跳过 VS Build Tools 安装"
}

# 5. rust 工具链切到 MSVC
rustup toolchain install stable-x86_64-pc-windows-msvc
rustup default stable-x86_64-pc-windows-msvc
rustup toolchain uninstall stable-x86_64-pc-windows-gnu 2>$null

# 6. 验证
Write-Host "=== 验证 ==="
rustc --version
cargo --version
Write-Host "完成。请新开一个终端使环境变量生效。"

#!/usr/bin/env pwsh
<#
.SYNOPSIS
  webshot - render HTML (file/string) or URL to PNG with the system browser
  (Edge/Chrome/Chromium/Brave auto-detected). Zero dependencies.

.EXAMPLE
  ./webshot.ps1 -Html C:\path\to\page.html -Out page.png
  ./webshot.ps1 -Url https://example.com -Out site.png -Width 1280 -Height 800
  ./webshot.ps1 -HtmlString '<html><body><h1>hi</h1></body></html>' -Out hi.png -Scale 2
  ./webshot.ps1 -Html chart.html -WaitMs 3000 -Width 1024 -Height 640   # wait for JS charts

.PARAMETER Html       path to an .html file (one of -Html/-Url/-HtmlString)
.PARAMETER Url        http(s) URL
.PARAMETER HtmlString raw HTML (written to a temp file)
.PARAMETER Out        output PNG path (default webshot.png)
.PARAMETER Width      viewport width (default 760)
.PARAMETER Height     viewport height (default 470)
.PARAMETER Scale      device scale factor (default 2; use 1 for quick previews)
.PARAMETER WaitMs     virtual time budget in ms, for JS-rendered charts
#>
param(
  [string]$Html,
  [string]$Url,
  [string]$HtmlString,
  [string]$Out = 'webshot.png',
  [int]$Width = 760,
  [int]$Height = 470,
  [double]$Scale = 2,
  [int]$WaitMs = 0
)

$ErrorActionPreference = 'Stop'

# ---- browser probe chain: Edge -> Chrome -> Chromium -> Brave -> PATH ----
$pf = $env:ProgramFiles
$pf86 = ${env:ProgramFiles(x86)}
$local = $env:LOCALAPPDATA
$candidates = @(
  "$pf86\Microsoft\Edge\Application\msedge.exe",
  "$pf\Microsoft\Edge\Application\msedge.exe",
  "$local\Microsoft\Edge\Application\msedge.exe",
  "$pf\Google\Chrome\Application\chrome.exe",
  "$pf86\Google\Chrome\Application\chrome.exe",
  "$local\Google\Chrome\Application\chrome.exe",
  "$local\Chromium\Application\chrome.exe",
  "$pf\BraveSoftware\Brave-Browser\Application\brave.exe",
  "$pf86\BraveSoftware\Brave-Browser\Application\brave.exe"
)
$browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) {
  foreach ($name in 'msedge', 'chrome', 'chromium', 'brave') {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $browser = $cmd.Source; break }
  }
}
if (-not $browser) {
  throw "webshot: no usable browser found (probed Edge/Chrome/Chromium/Brave paths and PATH).`nInstall one: winget install --id Microsoft.Edge  or  winget install --id Google.Chrome"
}

# ---- input: exactly one of -Html / -Url / -HtmlString ----
$sources = @($Html, $Url, $HtmlString) | Where-Object { $_ }
if ($sources.Count -eq 0) { throw 'webshot: one of -Html / -Url / -HtmlString is required' }
if ($sources.Count -gt 1) { throw 'webshot: -Html / -Url / -HtmlString are mutually exclusive' }

$source = $null
if ($HtmlString) {
  $tmp = Join-Path ([IO.Path]::GetTempPath()) ("webshot-" + [Guid]::NewGuid().ToString('N') + ".html")
  [IO.File]::WriteAllText($tmp, $HtmlString, [Text.UTF8Encoding]::new($false))
  $source = "file:///" + ($tmp -replace '\\', '/')
} elseif ($Html) {
  $full = (Resolve-Path $Html).Path -replace '\\', '/'
  $source = "file:///" + $full
} else {
  if ($Url -notmatch '^https?://') { throw 'webshot: -Url must start with http(s)://' }
  $source = $Url
}

# ---- build and run ----
$outAbs = if ([IO.Path]::IsPathRooted($Out)) { $Out } else { Join-Path (Get-Location) $Out }
$argList = @(
  '--headless=new', '--disable-gpu', '--hide-scrollbars',
  "--force-device-scale-factor=$Scale",
  "--window-size=$Width,$Height"
)
if ($WaitMs -gt 0) { $argList += "--virtual-time-budget=$WaitMs" }
$argList += @("--screenshot=$outAbs", $source)

# Chromium writes benign notices to stderr; never let stderr traffic kill
# the run under ErrorActionPreference=Stop.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $browser @argList 2>&1 | Out-Null
$ErrorActionPreference = $prevEap

# ---- verify output ----
if (-not (Test-Path $outAbs) -or (Get-Item $outAbs).Length -eq 0) {
  throw "webshot: screenshot failed (browser: $browser) - check the input path and parameters"
}
$size = (Get-Item $outAbs).Length
$waited = if ($WaitMs -gt 0) { ", waited ${WaitMs}ms" } else { '' }
Write-Host "webshot: $browser"
Write-Host "webshot: $outAbs ($size bytes, ${Width}x${Height} @${Scale}x$waited)"
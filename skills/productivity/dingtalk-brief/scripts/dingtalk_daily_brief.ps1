# DingTalk daily brief via dws CLI.
# Aggregates: unread mail, @me messages, unread chats, today agenda, today todos.
# Output: one Markdown file per run, prints its path to stdout.

$ErrorActionPreference = 'Continue'
# dws outputs UTF-8; without this PowerShell decodes it as the system codepage and
# Chinese turns to mojibake (which also breaks JSON quoting).
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$outDir = Join-Path $env:TEMP 'dingtalk-brief'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$file = Join-Path $outDir "brief_$stamp.md"

function Add-Line($text) {
    Add-Content -Path $file -Value $text -Encoding utf8
}

function Truncate($s, $n = 120) {
    if (-not $s) { return '' }
    $s = ($s -replace "`n", ' ').Trim()
    if ($s.Length -gt $n) { return $s.Substring(0, $n) + '...' }
    return $s
}

function Section($title, $cmd) {
    Add-Line "`n## $title`n"
    $out = & dws @cmd 2>&1 | Out-String
    try {
        $json = $out | ConvertFrom-Json
    } catch {
        Add-Line "(parse failed, raw output kept at $($file).raw)"
        $out | Set-Content -Path "$file.raw" -Encoding utf8
        return
    }
    # mail: unread-mail / recent-mail -> .mails[]
    if ($json.mails) {
        foreach ($m in $json.mails) {
            Add-Line "- $($m.date) | $(Truncate ($m.from -join ', ') 40) | $(Truncate $m.subject 60)"
        }
        if ($json.mails.Count -eq 0) { Add-Line '- (none)' }
        return
    }
    # chat: at-me -> .items[]
    if ($json.items) {
        foreach ($i in $json.items) {
            Add-Line "- $($i.time) | $($i.conversation.name) | $($i.sender) | $(Truncate $i.text 100)"
        }
        if ($json.items.Count -eq 0) { Add-Line '- (none)' }
        return
    }
    # chat: unread-chats -> .conversations[]
    if ($json.conversations) {
        foreach ($c in $json.conversations) {
            Add-Line "- $(Truncate $c.name 60)"
        }
        if ($json.conversations.Count -eq 0) { Add-Line '- (none)' }
        return
    }
    # calendar +agenda -> .data.events[] ; todo +due-today -> .data.tasks[]
    $list = $json.data.events
    if (-not $list) { $list = $json.data.tasks }
    if ($list -and $list.Count -gt 0) {
        foreach ($e in $list) {
            $title2 = $e.subject; if (-not $title2) { $title2 = $e.title; if (-not $title2) { $title2 = $e.summary } }
            Add-Line "- $(Truncate $title2 80)"
        }
    } else {
        Add-Line '- (none)'
    }
}

Set-Content -Path $file -Value "# DingTalk Daily Brief - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -Encoding utf8

Section 'Unread Mail' @('mail', '+unread-mail')
Section 'Recent Inbox' @('mail', '+recent-mail')
Section 'Mentioned Me' @('chat', '+at-me')
Section 'Unread Chats' @('chat', '+unread-chats')
Section "Today's Agenda" @('calendar', '+agenda')
Section "Today's Todos" @('todo', '+due-today')

Write-Output $file

#!/usr/bin/env node
// machine-snap — agent 工具箱快照（白名单制）
// manifest = whitelist.json（随 skill 走，手工维护）+ ~/.machine-snap/ 下的 mcp/path 本机快照
// 用法: node snap.mjs <snap-mcp|doctor|restore|redact> [--dry-run]

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';

const HOME = os.homedir();
const SNAP_DIR = path.join(HOME, '.machine-snap');
const MCP_CACHE = path.join(SNAP_DIR, 'mcp-snapshot.json');
const REDACTED = path.join(SNAP_DIR, 'manifest.redacted.json');

const SECRET_KEY_RE = /token|secret|password|passwd|authorization|api_?key|private_?token|credential|bearer/i;

const MANAGER_HINTS = {
  winget: 'Windows 11 自带；若缺失请在 Microsoft Store 更新「应用安装程序 (App Installer)」',
  choco: '管理员 PowerShell 执行: Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))',
  pip: '先装 Python: winget install Python.Python.3.12',
  npm: 'node 走 nvm4w: choco install nvm → nvm install 22 → nvm use 22',
  manual: 'manual 条目 restore 不代装，按 note 里的命令手工执行',
};

function run(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { encoding: 'utf8', shell: process.platform === 'win32', ...opts });
}

// 在位探测不能只信当前 shell 的 PATH（Git Bash 会话常持陈旧 PATH，winget/pip
// 刚装完的命令会被误判 MISSING）。合并「用户注册表 PATH」一起找。
function userPathDirs() {
  const r = run('powershell.exe', ['-NoProfile', '-Command', "[Environment]::GetEnvironmentVariable('Path','User')"]);
  if (r.status !== 0 || !r.stdout) return [];
  return r.stdout.trim().split(';').map(s => s.trim()).filter(Boolean);
}

let _whereDirs = null;
function whereDirs() {
  if (!_whereDirs) _whereDirs = [...(process.env.PATH || '').split(path.delimiter), ...userPathDirs()];
  return _whereDirs;
}

function has(cmd) {
  if (cmd.includes('/')) cmd = cmd.split('/')[0]; // "uv/uvx" 这类复合命令取第一个
  if (process.platform !== 'win32') return spawnSync(cmd, ['--version'], { encoding: 'utf8' }).status === 0;
  if (cmd.includes('.')) return whereDirs().some(d => fs.existsSync(path.join(d, cmd))); // 带扩展名直接找文件
  return whereDirs().some(d => fs.existsSync(path.join(d, cmd + '.exe')) || fs.existsSync(path.join(d, cmd + '.cmd')) || fs.existsSync(path.join(d, cmd)))
    || run('where.exe', [cmd]).status === 0;
}

function ensureDir() { fs.mkdirSync(SNAP_DIR, { recursive: true }); }

// skill 自带的白名单：scripts/../whitelist.json（装到 ~/.agents/skills 后仍在包内）
function whitelistPath() {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'whitelist.json');
}
import { fileURLToPath } from 'node:url';

// ---------- 现状探测（按管理器各走各的准路） ----------

// winget 已装集合：export 没有版本号但 ID 全，批量一次最省
let _wingetSet = null;
function wingetInstalledSet() {
  if (_wingetSet) return _wingetSet;
  _wingetSet = new Set();
  const tmp = path.join(SNAP_DIR, '.tmp-winget.json');
  const r = run('winget', ['export', '-o', tmp, '--accept-source-agreements']);
  try {
    if (r.status === 0 && fs.existsSync(tmp)) {
      const data = JSON.parse(fs.readFileSync(tmp, 'utf8'));
      for (const src of data.Sources || [])
        for (const p of src.Packages || []) _wingetSet.add(p.PackageIdentifier || '');
    }
  } catch {} finally { try { fs.unlinkSync(tmp); } catch {} }
  return _wingetSet;
}

// pip 顶层包版本表（只查白名单里的包）
let _pipVer = null;
function pipVersions() {
  if (_pipVer) return _pipVer;
  _pipVer = {};
  const r = run('python', ['-m', 'pip', 'list', '--format', 'json']);
  if (r.status === 0) {
    try { for (const p of JSON.parse(r.stdout)) _pipVer[p.name.toLowerCase()] = p.version; } catch {}
  }
  return _pipVer;
}

function commandVersion(cmd) {
  const r = spawnSync(cmd, ['--version'], { encoding: 'utf8', shell: process.platform === 'win32' });
  if (r.status !== 0) return null;
  return (r.stdout || r.stderr || '').split(/\r?\n/)[0].trim().slice(0, 40) || null;
}

function entryPresent(e) {
  if (!has(e.command)) return false;
  switch (e.manager) {
    case 'winget': return wingetInstalledSet().has(e.packageId);
    case 'choco': return fs.existsSync('C:\\ProgramData\\chocolatey\\lib\\' + e.packageId.toLowerCase());
    case 'pip': return pipVersions()[e.packageId.toLowerCase()] !== undefined;
    case 'npm': return true; // 命令在 PATH 即算 npm 装到位（npm 包与命令同名不同包的情形极罕见）
    case 'manual': return true;
    default: return true;
  }
}

// ---------- MCP 本机快照（从 live 配置采集，存 ~/.machine-snap/mcp-snapshot.json） ----------

function captureCodebuddy() {
  const p = path.join(HOME, '.codebuddy', 'mcp.json');
  if (!fs.existsSync(p)) return null;
  try { return { file: p, servers: JSON.parse(fs.readFileSync(p, 'utf8')).mcpServers || {} }; } catch { return null; }
}

function captureClaude() {
  const p = path.join(HOME, '.claude.json');
  if (!fs.existsSync(p)) return null;
  try {
    const d = JSON.parse(fs.readFileSync(p, 'utf8'));
    return { file: p, servers: d.mcpServers || {} };
  } catch { return null; }
}

// codex config.toml：按 [mcp_servers.*] 切块（含 .env 等子表，遇到其他顶级节即停）
function sliceCodexMcp(text) {
  const lines = text.split(/\r?\n/);
  const anyHeader = /^\s*\[\[?\s*([^\]]+?)\s*\]]?\s*$/;
  const blocks = []; let cur = null;
  for (const line of lines) {
    const h = line.match(anyHeader);
    if (h) {
      if (cur) { blocks.push(cur); cur = null; }
      if (/^mcp_servers\b/.test(h[1])) cur = { name: h[1].split('.')[1] || h[1], text: line };
      continue;
    }
    if (cur) cur.text += '\n' + line;
  }
  if (cur) blocks.push(cur);
  const merged = [];
  for (const b of blocks) {
    const t = merged.find(x => x.name === b.name);
    if (t) t.text += '\n' + b.text; else merged.push({ ...b });
  }
  return merged.map(b => ({ name: b.name, block: b.text }));
}

function captureCodex() {
  const p = path.join(HOME, '.codex', 'config.toml');
  if (!fs.existsSync(p)) return null;
  const text = fs.readFileSync(p, 'utf8');
  return { file: p, servers: sliceCodexMcp(text), format: 'toml-blocks' };
}

function captureUserPath() {
  const r = run('powershell.exe', ['-NoProfile', '-Command', "[Environment]::GetEnvironmentVariable('Path','User')"]);
  if (r.status !== 0 || !r.stdout) return [];
  return [...new Set(r.stdout.trim().split(';').map(s => s.trim()).filter(Boolean))];
}

function saveMcpSnapshot() {
  const mcp = { codebuddy: captureCodebuddy(), claude: captureClaude(), codex: captureCodex() };
  fs.writeFileSync(MCP_CACHE, JSON.stringify({ mcp, pathAdditions: captureUserPath() }, null, 2));
  return mcp;
}

// ---------- doctor ----------

function liveMcpServerNames(client, m) {
  if (!m) return null;
  try {
    if (client === 'codebuddy') return Object.keys(JSON.parse(fs.readFileSync(m.file, 'utf8')).mcpServers || {});
    if (client === 'claude') return Object.keys(JSON.parse(fs.readFileSync(m.file, 'utf8')).mcpServers || {});
    if (client === 'codex') {
      const text = fs.readFileSync(m.file, 'utf8');
      return [...text.matchAll(/^\s*\[\[?\s*mcp_servers\.([^.\\\]]+)/gm)].map(x => x[1]);
    }
  } catch {}
  return null;
}

function doctor(wl, mcpBlock) {
  mcpBlock = mcpBlock || {};
  const lines = [];
  const missing = [];

  lines.push('-- coreRuntimes（runtime/基础设施）--');
  for (const e of wl.coreRuntimes || []) {
    const present = entryPresent(e);
    let tag = present ? 'ok      ' : 'MISSING ';
    if (!present) missing.push({ ...e, section: 'coreRuntimes' });
    const ver = present ? commandVersion(e.command.split('/')[0]) : '';
    lines.push(`  [${tag}] ${e.manager}:${e.packageId}  (${e.command})  ${ver || ''}`);
  }

  lines.push('-- core（agent 直接用）--');
  for (const e of wl.core || wl.tools || []) {
    const present = entryPresent(e);
    let tag = present ? 'ok      ' : 'MISSING ';
    if (!present) missing.push({ ...e, section: 'core' });
    const ver = present ? commandVersion(e.command) : '';
    lines.push(`  [${tag}] ${e.manager}:${e.packageId}  (${e.command})  ${ver || ''}`);
  }

  for (const [client, m] of Object.entries(mcpBlock.mcp || {})) {
    if (!m) { lines.push(`  [MCP ${client}] （本快照无此客户端）`); continue; }
    const live = liveMcpServerNames(client, m);
    if (live === null) { lines.push(`  [MCP ${client}] 目标文件不存在或不可读: ${m.file}`); continue; }
    const want = Array.isArray(m.servers) ? m.servers.map(s => s.name) : Object.keys(m.servers);
    const lack = want.filter(n => !live.includes(n));
    const extra = live.filter(n => !want.includes(n));
    lines.push(`  [MCP ${client}] ${lack.length ? '缺: ' + lack.join(', ') : '齐全'}${extra.length ? `  (机器上多出: ${extra.join(', ')})` : ''}`);
  }
  const livePath = captureUserPath();
  const wantPath = mcpBlock.pathAdditions || [];
  if (!wantPath.length) {
    lines.push('  [PATH] 快照为空（首次用先跑 snap-mcp 采集）');
  } else {
    const lackPath = wantPath.filter(p => !livePath.includes(p));
    lines.push(`  [PATH] ${lackPath.length ? '缺 ' + lackPath.length + ' 条（restore 补）' : wantPath.length + ' 条全部在位'}`);
  }
  return { lines, missingClis: missing };
}

// ---------- restore ----------

function installCli(e, dryRun) {
  if (e.manager === 'manual') {
    return console.log(`  [manual] ${e.packageId}: 不代装，按 note 执行 —— ${e.note || '见 whitelist.json'}`);
  }
  if (dryRun) return console.log(`  [dry-run] ${e.manager} install ${e.packageId}`);
  let r;
  switch (e.manager) {
    case 'winget':
      r = run('winget', ['install', '--id', e.packageId, '-e', '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity'], { stdio: 'inherit' });
      break;
    case 'choco':
      console.log('  (choco 需要管理员 shell，失败请用管理员终端重跑)');
      r = run('choco', ['install', e.packageId, '-y'], { stdio: 'inherit' });
      break;
    case 'pip':
      r = run('python', ['-m', 'pip', 'install', '--user', e.packageId], { stdio: 'inherit' });
      break;
    case 'npm':
      r = run('npm', ['install', '-g', e.packageId], { stdio: 'inherit' });
      break;
    default:
      return console.log(`  未知管理器 ${e.manager}，跳过`);
  }
  console.log(`  ${e.packageId}: ${r.status === 0 ? '完成' : '失败(exit ' + r.status + ')'}`);
}

function restoreMcp(mcpBlock, dryRun) {
  for (const [client, m] of Object.entries(mcpBlock || {})) {
    if (!m) continue;
    if (client === 'codex') { restoreCodex(m, dryRun); continue; }
    if (!fs.existsSync(m.file)) {
      if (dryRun) { console.log(`  [dry-run] 将创建 ${m.file}`); continue; }
      fs.mkdirSync(path.dirname(m.file), { recursive: true });
      const servers = Array.isArray(m.servers) ? Object.fromEntries(m.servers.map(s => [s.name, s.def || {}])) : m.servers;
      fs.writeFileSync(m.file, JSON.stringify({ mcpServers: servers }, null, 2));
      console.log(`  ${client}: 已写入 ${m.file}`);
      continue;
    }
    if (dryRun) { console.log(`  [dry-run] 合并写入 ${m.file}`); continue; }
    const live = JSON.parse(fs.readFileSync(m.file, 'utf8'));
    const incoming = Array.isArray(m.servers) ? Object.fromEntries(m.servers.map(s => [s.name, s.def || {}])) : m.servers;
    live.mcpServers = { ...(live.mcpServers || {}), ...incoming };
    fs.writeFileSync(m.file, JSON.stringify(live, null, 2));
    console.log(`  ${client}: 已合并 ${Object.keys(incoming).length} 个 server → ${m.file}`);
  }
}

function restoreCodex(m, dryRun) {
  const file = m.file;
  const existing = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : '';
  const blocks = Array.isArray(m.servers) ? m.servers : [];
  const todo = blocks.filter(b => !existing.includes(`mcp_servers.${b.name}]`));
  if (!todo.length) return console.log('  codex: MCP 块已齐全，跳过');
  if (dryRun) return console.log(`  [dry-run] 将追加 ${todo.map(b => b.name).join(', ')} 到 ${file}`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, '\n' + todo.map(b => b.block).join('\n') + '\n');
  console.log(`  codex: 追加 ${todo.map(b => b.name).join(', ')} → ${file}`);
}

function restorePath(entries, dryRun) {
  if (!entries || !entries.length) return console.log('  PATH: 快照为空，跳过');
  const live = new Set(captureUserPath());
  const todo = entries.filter(p => !live.has(p));
  if (!todo.length) return console.log('  PATH: 增量已齐全，跳过');
  if (dryRun) return console.log(`  [dry-run] 将追加到用户 PATH: ${todo.join(' ; ')}`);
  const script = `$p=[Environment]::GetEnvironmentVariable('Path','User');$add=@(${entries.map(p => JSON.stringify(p)).join(',')});foreach($d in $add){if((";$p;") -notlike "*;$d;*"){$p="$p;$d"}};[Environment]::SetEnvironmentVariable('Path',$p,'User');Write-Output done`;
  const r = run('powershell.exe', ['-NoProfile', '-Command', script]);
  console.log(`  PATH: ${r.status === 0 && /done/.test(r.stdout) ? '已追加 ' + todo.length + ' 条' : '失败，请手工追加: ' + todo.join(' ; ')}`);
}

function restore(wl, mcpBlock, flags) {
  const dryRun = flags.has('--dry-run');
  console.log(`== restore ${dryRun ? '(dry-run)' : ''} ==`);

  // 0. mcp/path 快照文件存在性
  if (!mcpBlock || (!mcpBlock.mcp && !mcpBlock.pathAdditions)) {
    console.log(`!! 没有本机 MCP/PATH 快照（${MCP_CACHE}）。旧电脑上跑过 "node snap.mjs snap-mcp" 的产物拷过来再 restore；本次只还原 CLI。`);
    mcpBlock = {};
  }

  // 1. 包管理器体检（manual 不算管理器）
  const absent = new Set();
  for (const mgr of new Set([...(wl.coreRuntimes || []), ...(wl.core || [])].map(e => e.manager))) {
    if (mgr === 'manual') continue;
    const checker = { winget: 'winget', choco: 'choco', pip: 'python', npm: 'npm' }[mgr];
    if (!checker || !has(checker)) {
      absent.add(mgr);
      console.log(`!! 包管理器缺失: ${mgr}\n   ${MANAGER_HINTS[mgr] || '请先安装'}`);
    }
  }

  // 2. 先装 coreRuntimes，再装 tools（core 先行为 MCP/skills 铺 runtime）
  const all = [...(wl.coreRuntimes || []), ...(wl.core || [])];
  const todo = all.filter(e => !entryPresent(e) && !absent.has(e.manager));
  console.log(`待安装 ${todo.length} 个（core 先行）:`);
  for (const e of todo) installCli(e, dryRun);
  if (absent.size) console.log(`(跳过 ${absent.size} 个管理器下的条目，装好管理器后重跑)`);

  // 3. MCP
  console.log('MCP 配置:');
  restoreMcp(mcpBlock.mcp || {}, dryRun);

  // 4. PATH
  console.log('PATH 增量:');
  restorePath(mcpBlock.pathAdditions || [], dryRun);

  // 5. 收尾对账
  if (!dryRun) {
    console.log('\n== 收尾对账 ==');
    const { lines } = doctor(wl, mcpBlock);
    for (const l of lines) console.log(l);
  }
}

// ---------- redact ----------

function deepRedact(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    out[k] = SECRET_KEY_RE.test(k) ? '[REDACTED]'
      : (v && typeof v === 'object' && !Array.isArray(v)) ? deepRedact(v)
      : Array.isArray(v) ? v.map(x => (x && typeof x === 'object') ? deepRedact(x) : x)
      : v;
  }
  return out;
}

function redactCodexBlocks(servers) {
  return servers.map(s => ({
    ...s,
    block: s.block.split('\n').map(line => {
      const mm = line.match(/^(\s*)([A-Za-z0-9_]+)\s*=\s*(.+)$/);
      return mm && SECRET_KEY_RE.test(mm[2]) ? `${mm[1]}${mm[2]} = '[REDACTED]'` : line;
    }).join('\n'),
  }));
}

function redact(mcpBlock) {
  const out = JSON.parse(JSON.stringify(mcpBlock || {}));
  for (const [client, m] of Object.entries(out.mcp || {})) {
    if (!m) continue;
    if (client === 'codex') { m.servers = redactCodexBlocks(m.servers); continue; }
    m.servers = Array.isArray(m.servers)
      ? m.servers.map(s => ({ ...s, def: deepRedact(s.def || {}) }))
      : deepRedact(m.servers);
  }
  fs.writeFileSync(REDACTED, JSON.stringify(out, null, 2));
  console.log(`脱敏版已写入: ${REDACTED}`);
  console.log('注意: 仍可能含内网 URL/主机名/路径，外传前请再过目一遍。');
}

// ---------- main ----------

const [, , cmd, ...rest] = process.argv;
const flags = new Set(rest.filter(a => a.startsWith('--')));
ensureDir();

switch (cmd) {
  case 'snap-mcp': {
    // 在旧电脑/日常机上采集 MCP 三客户端 + PATH 到 ~/.machine-snap/mcp-snapshot.json（含 token，不进 git）
    const mcp = saveMcpSnapshot();
    const cnt = m => m ? (Array.isArray(m.servers) ? m.servers.length : Object.keys(m.servers || {}).length) : 0;
    console.log(`快照已写入: ${MCP_CACHE}`);
    console.log(`  MCP: codebuddy ${cnt(mcp.codebuddy)} / claude ${cnt(mcp.claude)} / codex ${cnt(mcp.codex)} 个 server`);
    console.log(`  PATH 条目: ${captureUserPath().length}`);
    console.log('  （含 token 明文，备份/外传请用 redact）');
    break;
  }
  case 'doctor': {
    const wl = JSON.parse(fs.readFileSync(whitelistPath(), 'utf8'));
    let mcpBlock = null;
    if (fs.existsSync(MCP_CACHE)) mcpBlock = JSON.parse(fs.readFileSync(MCP_CACHE, 'utf8'));
    console.log('== doctor: whitelist.json vs 本机 ==');
    const { lines } = doctor(wl, mcpBlock);
    for (const l of lines) console.log(l);
    break;
  }
  case 'restore': {
    const wl = JSON.parse(fs.readFileSync(whitelistPath(), 'utf8'));
    const mcpBlock = fs.existsSync(MCP_CACHE) ? JSON.parse(fs.readFileSync(MCP_CACHE, 'utf8')) : null;
    restore(wl, mcpBlock, flags);
    break;
  }
  case 'redact': {
    const mcpBlock = fs.existsSync(MCP_CACHE) ? JSON.parse(fs.readFileSync(MCP_CACHE, 'utf8')) : null;
    if (!mcpBlock) { console.error(`找不到 ${MCP_CACHE}，先跑 node snap.mjs snap-mcp`); break; }
    redact(mcpBlock);
    break;
  }
  default:
    console.log('用法: node snap.mjs <snap-mcp|doctor|restore|redact> [--dry-run]');
    console.log('  snap-mcp  采集本机 MCP 三客户端 + 用户 PATH → ~/.machine-snap/mcp-snapshot.json（含 token）');
    console.log('  doctor    whitelist.json（agent 工具箱白名单）vs 本机，逐条对账');
    console.log('  restore   照白名单还原（coreRuntimes 先装 → tools → MCP → PATH；管理器缺失只提示；收尾对账）');
    console.log('  redact    生成脱敏版 manifest.redacted.json（可外传）');
    console.log('\n白名单维护：直接改 skill 目录下的 whitelist.json（加条目 = manager+packageId+command+note）');
}

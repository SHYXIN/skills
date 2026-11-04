#!/usr/bin/env node
// machine-snap — 机器级环境快照（CLI + MCP + PATH 增量）
// 用法: node snap.mjs <capture|doctor|restore|redact> [文件] [--dry-run]
// manifest 存 ~/.machine-snap/：capture 生成 manifest.draft.json，人工修剪后另存 manifest.json。

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';

const HOME = os.homedir();
const SNAP_DIR = path.join(HOME, '.machine-snap');
const DRAFT = path.join(SNAP_DIR, 'manifest.draft.json');
const MANIFEST = path.join(SNAP_DIR, 'manifest.json');
const REDACTED = path.join(SNAP_DIR, 'manifest.redacted.json');

const SECRET_KEY_RE = /token|secret|password|passwd|authorization|api_?key|private_?token|credential|bearer/i;

const MANAGER_HINTS = {
  winget: 'Windows 11 自带；若缺失请在 Microsoft Store 更新「应用安装程序 (App Installer)」',
  choco: '管理员 PowerShell 执行: Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))',
  pip: '先装 Python: winget install Python.Python.3',
  npm: '先装 Node.js: winget install OpenJS.NodeJS.LTS',
};

function run(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { encoding: 'utf8', shell: process.platform === 'win32', ...opts });
}

function has(cmd) {
  if (process.platform !== 'win32') return spawnSync(cmd, ['--version'], { encoding: 'utf8' }).status === 0;
  return run('where.exe', [cmd]).status === 0;
}

function ensureDir() { fs.mkdirSync(SNAP_DIR, { recursive: true }); }

// ---------- 采集：CLI ----------

function captureWinget() {
  const tmp = path.join(SNAP_DIR, '.tmp-winget.json');
  const r = run('winget', ['export', '-o', tmp, '--accept-source-agreements']);
  if (r.status !== 0 && !fs.existsSync(tmp)) return [];
  try {
    const data = JSON.parse(fs.readFileSync(tmp, 'utf8'));
    const ids = [];
    for (const src of data.Sources || []) {
      for (const p of src.Packages || []) {
        const id = p.PackageIdentifier || '';
        if (!id || /^(ARP|MSIX)\\/.test(id)) continue; // 跳过系统 ARP/MSIX 噪音条目
        ids.push({ name: id.split('.').pop().toLowerCase(), manager: 'winget', packageId: id, version: null, note: '' });
      }
    }
    return ids;
  } finally { try { fs.unlinkSync(tmp); } catch {} }
}

function captureChoco() {
  const r = run('choco', ['list']);
  if (r.status !== 0) return [];
  const out = [];
  for (const line of (r.stdout || '').split(/\r?\n/)) {
    const m = line.match(/^([A-Za-z0-9._-]+)\s+(\S+)\s*$/);
    if (!m || /^(name|-----)/i.test(m[1])) continue;
    // 剔除解析噪音（"Validation Warnings"等提示行）与 chocolatey 自身
    if (!/^[0-9]+\s/.test(line) && /\s(warnings?|errors?|performed|success)/i.test(line)) continue;
    if (/^chocolatey/i.test(m[1])) continue;
    out.push({ name: m[1], manager: 'choco', packageId: m[1], version: m[2], note: '' });
  }
  return out;
}

function capturePip() {
  const r = run('python', ['-m', 'pip', 'list', '--format', 'json']);
  if (r.status !== 0) return [];
  try {
    return JSON.parse(r.stdout).map(p => ({ name: p.name.toLowerCase(), manager: 'pip', packageId: p.name, version: p.version, note: '' }));
  } catch { return []; }
}

function captureNpm() {
  const r = run('npm', ['ls', '-g', '--depth', '0', '--json']);
  if (r.status !== 0) return [];
  try {
    const deps = JSON.parse(r.stdout).dependencies || {};
    return Object.entries(deps).map(([k, v]) => ({ name: k, manager: 'npm', packageId: k, version: (v && v.version) || null, note: '' }));
  } catch { return []; }
}

// ---------- 采集：MCP ----------

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

// ---------- 采集：用户 PATH ----------

function captureUserPath() {
  const r = run('powershell.exe', ['-NoProfile', '-Command', "[Environment]::GetEnvironmentVariable('Path','User')"]);
  if (r.status !== 0 || !r.stdout) return [];
  return [...new Set(r.stdout.trim().split(';').map(s => s.trim()).filter(Boolean))];
}

// ---------- capture ----------

function capture() {
  ensureDir();
  const clis = [
    ...captureWinget(), ...captureChoco(), ...capturePip(), ...captureNpm(),
  ];
  const manifest = {
    schema: 'machine-snap/1',
    capturedAt: new Date().toISOString(),
    machine: os.hostname(),
    clis,
    mcp: {
      codebuddy: captureCodebuddy(),
      claude: captureClaude(),
      codex: captureCodex(),
    },
    pathAdditions: captureUserPath(),
  };
  fs.writeFileSync(DRAFT, JSON.stringify(manifest, null, 2));
  const cnt = m => m ? (Array.isArray(m.servers) ? m.servers.length : Object.keys(m.servers || {}).length) : 0;
  console.log(`草稿已写入: ${DRAFT}`);
  console.log(`  CLI 条目: ${clis.length} (winget ${captureWingetName(manifest)} / 完整清单见文件)`);
  console.log(`  MCP: codebuddy ${cnt(manifest.mcp.codebuddy)} / claude ${cnt(manifest.mcp.claude)} / codex ${cnt(manifest.mcp.codex)} 个 server`);
  console.log(`  PATH 条目: ${manifest.pathAdditions.length}`);
  console.log('\n下一步: 修剪草稿（删除不要的条目、补 note 备注）→ 另存为 ~/.machine-snap/manifest.json 定稿');
}

function captureWingetName(m) { return (m.clis.filter(c => c.manager === 'winget').length); }

// ---------- 读取 manifest ----------

function loadManifest(argFile) {
  const file = argFile && !argFile.startsWith('--') ? argFile : MANIFEST;
  if (!fs.existsSync(file)) {
    console.error(`找不到 ${file}。先跑 capture 生成草稿，修剪后另存为 manifest.json。`);
    process.exit(1);
  }
  return { manifest: JSON.parse(fs.readFileSync(file, 'utf8')), file };
}

// ---------- 现状对比 ----------

function currentCliVersions() {
  const map = {};
  for (const p of capturePip()) map[`pip:${p.name}`] = p.version;
  for (const p of captureNpm()) map[`npm:${p.name}`] = p.version;
  return map;
}

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

// winget 已装集合：export 没有版本号但 ID 全，批量一次最省
let _wingetSet = null;
function wingetInstalledSet() {
  if (_wingetSet) return _wingetSet;
  _wingetSet = new Set(captureWinget().map(c => c.packageId));
  return _wingetSet;
}

// 存在性判定按管理器各走各的准路：winget 看导出 ID 集，choco 看 lib 目录，pip/npm 看版本表
function cliPresent(c, curVer) {
  switch (c.manager) {
    case 'winget': return wingetInstalledSet().has(c.packageId);
    case 'choco': return fs.existsSync('C:\\ProgramData\\chocolatey\\lib\\' + c.packageId.toLowerCase());
    case 'pip': return curVer[`pip:${c.name}`] !== undefined;
    case 'npm': return curVer[`npm:${c.name}`] !== undefined;
    default: return has(c.name);
  }
}

function doctor(manifest) {
  const lines = [];
  const curVer = currentCliVersions();
  const missing = [];
  for (const c of manifest.clis) {
    const present = cliPresent(c, curVer);
    let tag = present ? 'ok      ' : 'MISSING ';
    let ver = '';
    const key = `${c.manager}:${c.name}`;
    if (present && c.version && curVer[key] && curVer[key] !== c.version) {
      tag = 'VERDIFF ';
      ver = `(manifest ${c.version} → 实际 ${curVer[key]})`;
    }
    if (!present) missing.push(c);
    lines.push(`  [${tag}] ${c.manager}:${c.packageId} ${ver}`);
  }
  for (const [client, m] of Object.entries(manifest.mcp || {})) {
    if (!m) continue;
    const live = liveMcpServerNames(client, m);
    if (live === null) { lines.push(`  [MCP ${client}] 目标文件不存在或不可读: ${m.file}`); continue; }
    const want = Array.isArray(m.servers) ? m.servers.map(s => s.name) : Object.keys(m.servers);
    const lack = want.filter(n => !live.includes(n));
    const extra = live.filter(n => !want.includes(n));
    lines.push(`  [MCP ${client}] ${lack.length ? '缺: ' + lack.join(', ') : '齐全'}${extra.length ? `  (机器上多出: ${extra.join(', ')})` : ''}`);
  }
  const livePath = captureUserPath();
  const lackPath = (manifest.pathAdditions || []).filter(p => !livePath.includes(p));
  lines.push(`  [PATH] ${lackPath.length ? '缺: ' + lackPath.join(' ; ') : '齐全'}`);
  return { lines, missingClis: missing, lackPath };
}

// ---------- restore ----------

function installCli(c, dryRun) {
  if (dryRun) return console.log(`  [dry-run] ${c.manager} install ${c.packageId}`);
  let r;
  switch (c.manager) {
    case 'winget':
      r = run('winget', ['install', '--id', c.packageId, '-e', '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity'], { stdio: 'inherit' });
      break;
    case 'choco':
      console.log('  (choco 需要管理员 shell，失败请用管理员终端重跑)');
      r = run('choco', ['install', c.packageId, '-y'], { stdio: 'inherit' });
      break;
    case 'pip':
      r = run('python', ['-m', 'pip', 'install', '--user', c.packageId], { stdio: 'inherit' });
      break;
    case 'npm':
      r = run('npm', ['install', '-g', c.packageId], { stdio: 'inherit' });
      break;
    default:
      return console.log(`  未知管理器 ${c.manager}，跳过`);
  }
  console.log(`  ${c.packageId}: ${r.status === 0 ? '完成' : '失败(exit ' + r.status + ')'}`);
}

function restoreMcp(manifest, dryRun) {
  for (const [client, m] of Object.entries(manifest.mcp || {})) {
    if (!m) continue;
    if (client === 'codex') { restoreCodex(m, dryRun); continue; }
    if (!fs.existsSync(m.file)) {
      if (dryRun) { console.log(`  [dry-run] 将创建 ${m.file}`); continue; }
      fs.mkdirSync(path.dirname(m.file), { recursive: true });
      const servers = Array.isArray(m.servers) ? Object.fromEntries(m.servers.map(s => [s.name, s.def || {}])) : m.servers;
      fs.writeFileSync(m.file, JSON.stringify(client === 'codebuddy' ? { mcpServers: servers } : { mcpServers: servers }, null, 2));
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
  const live = new Set(captureUserPath());
  const todo = entries.filter(p => !live.has(p));
  if (!todo.length) return console.log('  PATH: 增量已齐全，跳过');
  if (dryRun) return console.log(`  [dry-run] 将追加到用户 PATH: ${todo.join(' ; ')}`);
  const script = `$p=[Environment]::GetEnvironmentVariable('Path','User');$add=@(${todo.map(p => JSON.stringify(p)).join(',')});foreach($d in $add){if((";$p;") -notlike "*;$d;*"){$p="$p;$d"}};[Environment]::SetEnvironmentVariable('Path',$p,'User');Write-Output done`;
  const r = run('powershell.exe', ['-NoProfile', '-Command', script]);
  console.log(`  PATH: ${r.status === 0 && /done/.test(r.stdout) ? '已追加 ' + todo.length + ' 条' : '失败，请手工追加: ' + todo.join(' ; ')}`);
}

function restore(argFile, flags) {
  const { manifest } = loadManifest(argFile);
  const dryRun = flags.has('--dry-run');
  console.log(`== restore ${dryRun ? '(dry-run)' : ''} ==`);

  // 1. 包管理器体检
  const absent = new Set();
  for (const mgr of new Set(manifest.clis.map(c => c.manager))) {
    const checker = { winget: 'winget', choco: 'choco', pip: 'python', npm: 'npm' }[mgr];
    if (!checker || !has(checker)) {
      absent.add(mgr);
      console.log(`!! 包管理器缺失: ${mgr}\n   ${MANAGER_HINTS[mgr] || '请先安装'}`);
    }
  }

  // 2. 装缺失 CLI
  const todo = doctor(manifest).missingClis.filter(c => !absent.has(c.manager));
  console.log(`待安装 ${todo.length} 个 CLI:`);
  for (const c of todo) installCli(c, dryRun);
  if (absent.size) console.log(`(跳过 ${absent.size} 个管理器下的条目，装好管理器后重跑)`);

  // 3. MCP
  console.log('MCP 配置:');
  restoreMcp(manifest, dryRun);

  // 4. PATH
  console.log('PATH 增量:');
  restorePath(manifest.pathAdditions || [], dryRun);

  // 5. 收尾对账
  if (!dryRun) {
    console.log('\n== 收尾对账 ==');
    const { lines } = doctor(manifest);
    for (const l of lines) console.log(l);
  }
}

// ---------- redact ----------

function redactValue(v) {
  if (typeof v === 'string') return '[REDACTED]';
  if (v && typeof v === 'object') return JSON.parse(JSON.stringify(v, (k, x) => SECRET_KEY_RE.test(k) ? '[REDACTED]' : x));
  return v;
}

function deepRedact(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    out[k] = SECRET_KEY_RE.test(k) ? redactValue(v)
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

function redact(argFile) {
  const { manifest } = loadManifest(argFile);
  const out = JSON.parse(JSON.stringify(manifest));
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
  case 'capture': capture(); break;
  case 'doctor': { const { manifest } = loadManifest(rest.find(a => !a.startsWith('--'))); const { lines } = doctor(manifest); console.log(`== doctor: ${rest.find(a => !a.startsWith('--')) || MANIFEST} ==`); for (const l of lines) console.log(l); break; }
  case 'restore': restore(rest.find(a => !a.startsWith('--')), flags); break;
  case 'redact': redact(rest.find(a => !a.startsWith('--'))); break;
  default:
    console.log('用法: node snap.mjs <capture|doctor|restore|redact> [manifest路径] [--dry-run]');
    console.log('  capture  扫描本机（winget/choco/pip/npm + 三客户端 MCP + 用户 PATH）→ manifest.draft.json');
    console.log('  doctor   manifest vs 实际装机 双向对账');
    console.log('  restore  照单还原（管理器缺失只提示；默认装最新版，收尾打版本差异报告）');
    console.log('  redact   生成脱敏版 manifest.redacted.json');
}

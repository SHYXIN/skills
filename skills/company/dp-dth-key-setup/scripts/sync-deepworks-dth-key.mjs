#!/usr/bin/env node
// 从 DeepWorks 桌面端 localStorage (leveldb) 提取当前登录账号的
// modelPlatformApiKey（TokenHub 积分计费 key），同步进 pi agent 的
// auth.json / models.json。手动运行，幂等，带时间戳备份。
//
// 用法: node sync-deepworks-dth-key.mjs [--dry-run] [--gateway test|prod]
//       [--pi-dir <dir>]

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const GATEWAYS = {
  test: "https://tokenhub-test.deepexios.cn/gateway/api/v1",
  prod: "https://tokenhub.deepexios.cn/gateway/api/v1",
};

const DTH_MODELS = [
  { id: "DeepSeek-V4-Flash", name: "DeepSeek V4 Flash", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "DeepSeek-V4-Pro", name: "DeepSeek V4 Pro", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "DeepSeek-V4.1-Flash", name: "DeepSeek V4.1 Flash", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "GLM-5.2", name: "GLM-5.2", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "GLM-5.3", name: "GLM-5.3", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "GLM-5.3-Flash", name: "GLM-5.3 Flash", reasoning: false, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "Kimi-K3", name: "Kimi K3", reasoning: true, input: ["text"], contextWindow: 256000, maxTokens: 16384 },
  { id: "Kimi-K2.6", name: "Kimi K2.6", reasoning: false, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "Qwen-3.8-Max", name: "Qwen 3.8 Max", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "Qwen3.8-27B", name: "Qwen3.8 27B", reasoning: false, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "Deepexi-E-Max-2.0", name: "Deepexi E Max 2.0", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
  { id: "Deepexi-E-Pro-2.0", name: "Deepexi E Pro 2.0", reasoning: true, input: ["text"], contextWindow: 128000, maxTokens: 16384 },
];

// TokenHub 网关背后的模型不认 OpenAI 新式 developer 角色（400 invalid_parameter_error）
const DTH_COMPAT = { supportsDeveloperRole: false };

// ---------- CLI ----------
const args = process.argv.slice(2);
function flag(name) {
  const i = args.indexOf(name);
  if (i === -1) return undefined;
  const v = args[i + 1];
  if (!v || v.startsWith("--")) return true;
  args.splice(i, 2);
  return v;
}
const dryRun = args.includes("--dry-run");
if (dryRun) args.splice(args.indexOf("--dry-run"), 1);
let gatewayOverride = flag("--gateway");
let piDir = flag("--pi-dir") || path.join(os.homedir(), ".pi", "agent");
let dwOverride = flag("--deepworks-dir");

if (gatewayOverride && !GATEWAYS[gatewayOverride]) {
  console.error(`未知 gateway: ${gatewayOverride}（可选 test | prod）`);
  process.exit(1);
}

// ---------- snappy (pure js block decoder) ----------
function readVarint(buf, pos) {
  let shift = 0, result = 0;
  for (;;) {
    const b = buf[pos++];
    result |= (b & 0x7f) << shift;
    if (!(b & 0x80)) return [result, pos];
    shift += 7;
  }
}

function snappyDecompress(data) {
  let [fullLen, pos] = readVarint(data, 0);
  const out = Buffer.alloc(fullLen);
  let outPos = 0;
  while (pos < data.length) {
    const tag = data[pos++];
    const t = tag & 3;
    if (t === 0) {
      let ln = tag >> 2;
      if (ln < 60) ln += 1;
      else {
        const nbytes = ln - 59;
        ln = data.readUIntLE(pos, nbytes) + 1;
        pos += nbytes;
      }
      data.copy(out, outPos, pos, pos + ln);
      outPos += ln;
      pos += ln;
    } else {
      let length, offset;
      if (t === 1) {
        length = ((tag >> 2) & 7) + 4;
        offset = ((tag >> 5) << 8) | data[pos++];
      } else if (t === 2) {
        length = (tag >> 2) + 1;
        offset = data.readUInt16LE(pos); pos += 2;
      } else {
        length = (tag >> 2) + 1;
        offset = data.readUInt32LE(pos); pos += 4;
      }
      let src = outPos - offset;
      for (let i = 0; i < length; i++) out[outPos++] = out[src++];
    }
  }
  if (outPos !== fullLen) throw new Error(`snappy length mismatch ${outPos} != ${fullLen}`);
  return out;
}

// ---------- ldb table ----------
function readBlock(fd, handleBuf) {
  let [off, pos] = readVarint(handleBuf, 0);
  const [size] = readVarint(handleBuf, pos);
  const buf = Buffer.alloc(size + 5);
  fs.readSync(fd, buf, 0, size + 5, off);
  const comp = buf[size];
  const payload = buf.subarray(0, size);
  if (comp === 0) return payload;
  if (comp === 1) return snappyDecompress(payload);
  throw new Error(`unknown compression ${comp}`);
}

function* blockEntries(block) {
  const nRestarts = block.readUInt32LE(block.length - 4);
  const dataEnd = block.length - 4 - 4 * nRestarts;
  let pos = 0;
  let key = Buffer.alloc(0);
  while (pos < dataEnd) {
    let shared, nonShared, vlen;
    [shared, pos] = readVarint(block, pos);
    [nonShared, pos] = readVarint(block, pos);
    [vlen, pos] = readVarint(block, pos);
    key = Buffer.concat([key.subarray(0, shared), block.subarray(pos, pos + nonShared)]);
    pos += nonShared;
    const value = block.subarray(pos, pos + vlen);
    pos += vlen;
    yield [key, value];
  }
}

function* parseTable(file) {
  const fd = fs.openSync(file, "r");
  try {
    const fsize = fs.fstatSync(fd).size;
    const footer = Buffer.alloc(48);
    fs.readSync(fd, footer, 0, 48, fsize - 48);
    const magic = footer.readBigUInt64LE(40);
    if (magic !== 0xdb4775248b80fb57n) throw new Error("bad magic");
    let [, p1] = readVarint(footer, 0); // metaindex offset
    let [metaSize, p2] = readVarint(footer, p1); // metaindex size
    let [idxOff, p3] = readVarint(footer, p2); // index offset
    const [idxSize] = readVarint(footer, p3); // index size
    const handle = Buffer.alloc(20);
    let hlen = 0;
    for (const num0 of [idxOff, idxSize]) {
      let num = num0;
      do {
        let b7 = num & 0x7f;
        num >>>= 7;
        handle[hlen++] = num ? (b7 | 0x80) : b7;
      } while (num);
    }
    const index = readBlock(fd, handle.subarray(0, hlen));
    for (const [, value] of blockEntries(index)) {
      let block;
      try { block = readBlock(fd, value); } catch { continue; }
      yield* blockEntries(block);
    }
  } finally {
    fs.closeSync(fd);
  }
}

// ---------- WAL log (uncompressed records, UTF-16 scan) ----------
function* parseLog(file) {
  const buf = fs.readFileSync(file);
  const u16needle = Buffer.from('"modelPlatformApiKey":"', "utf16le");
  let i = 0;
  while ((i = buf.indexOf(u16needle, i)) !== -1) {
    let start = i;
    while (start > 0 && buf[start - 2] !== 0x7b) start -= 2; // find '{' utf16
    const parts = [];
    let j = start;
    for (; j + 1 < buf.length; j += 2) {
      const ch = buf.readUInt16LE(j);
      if (ch === 0x22) break; // closing quote
      parts.push(ch);
    }
    try {
      const text = Buffer.from(parts.flatMap((c) => [c & 0xff, c >> 8])).toString("utf16le", 0, parts.length * 2);
      yield ["log-extract", Buffer.from(text, "utf16le")];
    } catch {}
    i = j;
  }
}

// ---------- extraction ----------
function userInfoFromValue(value) {
  const body = value[0] === 0 && value[1] === 0x7b ? value.subarray(1) : value;
  const text = body.toString("utf16le");
  const email = text.match(/"email":\s*"([^"]+)"/)?.[1] ?? null;
  const key = text.match(/"modelPlatformApiKey":\s*"([^"]+)"/)?.[1] ?? null;
  const updatedAt = text.match(/"updated_at":\s*"([^"]+)"/)?.[1] ?? null;
  const tenant = text.match(/"tenantId":\s*"([^"]+)"/)?.[1] ?? null;
  if (!key) return null;
  return { email, key, updatedAt, tenant };
}

function collectCandidates() {
  const appData = process.env.APPDATA;
  const roots = dwOverride
    ? [dwOverride]
    : [path.join(appData, "com.deepexi.deepworks"), path.join(appData, "com.deepexi.deepworks.test")];
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "dws-ls-"));
  const candidates = [];
  try {
    for (const root of roots) {
      const lsDir = path.join(root, "Local Storage", "leveldb");
      if (!fs.existsSync(lsDir)) continue;
      const copyDir = path.join(tmpRoot, path.basename(root));
      fs.mkdirSync(copyDir, { recursive: true });
      for (const f of fs.readdirSync(lsDir)) {
        try { fs.copyFileSync(path.join(lsDir, f), path.join(copyDir, f)); } catch {}
      }
      const env = root.endsWith(".test") ? "test" : "prod";
      for (const f of fs.readdirSync(copyDir)) {
        const full = path.join(copyDir, f);
        try {
          if (f.endsWith(".ldb")) {
            for (const [k, v] of parseTable(full)) {
              if (k.includes("userInfo")) {
                const info = userInfoFromValue(v);
                if (info) candidates.push({ env, source: f, ...info });
              }
            }
          } else if (f.endsWith(".log")) {
            for (const [, v] of parseLog(full)) {
              const info = userInfoFromValue(v);
              if (info) candidates.push({ env, source: f, ...info });
            }
          }
        } catch {}
      }
    }
  } finally {
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
  return candidates;
}

function pickNewest(candidates) {
  const scored = candidates.map((c) => ({ c, t: c.updatedAt ? Date.parse(c.updatedAt) : 0 }));
  scored.sort((a, b) => b.t - a.t);
  return scored[0]?.c ?? null;
}

// ---------- pi config ----------
function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return fallback; }
}

function backup(file) {
  if (!fs.existsSync(file)) return;
  const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14);
  fs.copyFileSync(file, `${file}.bak-${stamp}`);
}

function fingerprint(key) {
  return `${key.slice(0, 6)}...${key.slice(-4)} (len ${key.length})`;
}

function printSummary(chosen, gateway, baseUrl, piDir) {
  const pool = gateway === "test"
    ? "Test 版 DeepWorks 桌面端的积分池"
    : "正式版 DeepWorks 桌面端的积分池";
  const settings = readJson(path.join(piDir, "settings.json"), {});
  const defaultModel = settings.defaultProvider === "dth" ? `dth/${settings.defaultModel}` : (settings.defaultModel ?? "?");
  console.log("");
  console.log("—— 当前 pi 生效配置 ——");
  console.log(`账号:     ${chosen.email ?? "?"}`);
  console.log(`Key:      ${fingerprint(chosen.key)}`);
  console.log(`网关:     ${baseUrl} (${gateway})`);
  console.log(`积分池:   ${pool}`);
  console.log(`默认模型: ${defaultModel}`);
}

function main() {
  const candidates = collectCandidates();
  if (candidates.length === 0) {
    console.error("未找到任何 DeepWorks 登录凭据（localStorage 中没有 userInfo）");
    process.exit(1);
  }
  const chosen = pickNewest(candidates);
  const gateway = gatewayOverride ?? chosen.env;
  const baseUrl = GATEWAYS[gateway];
  console.log(`账号:   ${chosen.email ?? "?"}`);
  console.log(`租户:   ${chosen.tenant ?? "?"}`);
  console.log(`更新于: ${chosen.updatedAt ?? "?"}`);
  console.log(`来源:   ${chosen.env} (${chosen.source})`);
  console.log(`Key:    ${fingerprint(chosen.key)}`);
  console.log(`网关:   ${baseUrl} (${gateway})`);
  console.log(`模式:   ${dryRun ? "dry-run" : "写入"}`);

  const authFile = path.join(piDir, "auth.json");
  const modelsFile = path.join(piDir, "models.json");
  const settingsFile = path.join(piDir, "settings.json");
  const auth = readJson(authFile, {});
  const models = readJson(modelsFile, { providers: {} });
  const settings = readJson(settingsFile, {});

  const authSame = auth.dth?.type === "api_key" && auth.dth?.key === chosen.key;
  const provider = (models.providers ??= {}).dth ??= {};
  const modelsSame = provider.baseUrl === baseUrl && JSON.stringify(provider.compat ?? null) === JSON.stringify(DTH_COMPAT);
  console.log(`auth.json: ${authSame ? "已是最新" : "需要更新"}`);
  console.log(`models.json: ${modelsSame ? "已是最新" : "需要更新"}`);

  if (dryRun) {
    printSummary(chosen, gateway, baseUrl, piDir);
    return;
  }
  if (!authSame) {
    backup(authFile);
    auth.dth = { type: "api_key", key: chosen.key };
    fs.writeFileSync(authFile, JSON.stringify(auth, null, 2) + "\n");
  }
  if (!modelsSame) {
    backup(modelsFile);
    provider.baseUrl = baseUrl;
    provider.api = "openai-completions";
    provider.compat = DTH_COMPAT;
    provider.models = DTH_MODELS;
    fs.writeFileSync(modelsFile, JSON.stringify(models, null, 2) + "\n");
  }
  if (settings.defaultProvider !== "dth") {
    backup(settingsFile);
    settings.defaultProvider = "dth";
    settings.defaultModel = "DeepSeek-V4-Flash";
    if (!settings.enabledModels) settings.enabledModels = [];
    for (const m of DTH_MODELS) {
      const ref = `dth/${m.id}`;
      if (!settings.enabledModels.includes(ref)) settings.enabledModels.push(ref);
    }
    fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2) + "\n");
  }
  console.log("完成。pi 现在默认走 dth/DeepSeek-V4-Flash（积分计费）。");
  printSummary(chosen, gateway, baseUrl, piDir);
}

main();

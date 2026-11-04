#!/usr/bin/env node
// alias.mjs — 通用短名登记表操作
// 表: ~/.alias-registry.json（厂商中立，任何 agent 可读写）
// 用法:
//   node alias.mjs list
//   node alias.mjs get <short>
//   node alias.mjs add <short> <name> --kind agent --context "..." [--key value ...]
//   node alias.mjs remove <short>
// 短名全局唯一：add 撞名即失败（顺延分配新字母）；--yes 显式覆盖（警告一次）

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";

const REGISTRY = join(homedir(), ".alias-registry.json");

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function load() {
  if (!existsSync(REGISTRY)) return {};
  try {
    return JSON.parse(readFileSync(REGISTRY, "utf-8"));
  } catch (e) {
    die(`registry parse failed: ${e.message}`);
  }
}

function save(reg) {
  mkdirSync(dirname(REGISTRY), { recursive: true });
  writeFileSync(REGISTRY, JSON.stringify(reg, null, 2) + "\n", "utf-8");
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

// 顺延分配：优先未占用的单个大写字母，再未占用的单个常用汉字
const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const HANZI = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥".split("");
function nextFree(reg) {
  for (const c of LETTERS) if (!reg[c]) return c;
  for (const c of HANZI) if (!reg[c]) return c;
  return null;
}

const [, , cmd, ...rest] = process.argv;

if (cmd === "list") {
  const reg = load();
  const keys = Object.keys(reg).sort();
  if (!keys.length) {
    console.log("(empty registry)");
    process.exit(0);
  }
  for (const k of keys) {
    const e = reg[k];
    console.log(`${k} = ${e.name}  [${e.kind || "?"}]  ${e.context || ""}`);
  }
  process.exit(0);
}

if (cmd === "get") {
  const short = rest[0];
  if (!short) die("usage: get <short>");
  const e = load()[short];
  if (!e) die(`not found: ${short}`);
  console.log(JSON.stringify(e, null, 2));
  process.exit(0);
}

// next：推荐下一个可用短名（顺延分配）
if (cmd === "next") {
  const reg = load();
  const n = nextFree(reg);
  if (!n) die("registry exhausted");
  console.log(n);
  process.exit(0);
}

if (cmd === "add") {
  const short = rest[0];
  const name = rest[1];
  if (!short || !name) die("usage: add <short> <name> [--kind <kind>] --context <text> [--key value ...]");
  const reg = load();
  const yes = rest.includes("--yes");
  if (reg[short] && !yes) {
    const old = reg[short];
    console.error(`⚠️  短名已被占用: ${short} = ${old.name} (${old.context || ""})`);
    console.error(`   顺延推荐: ${nextFree(reg) ?? "(无可用)"}`);
    console.error(`   确认覆盖: node alias.mjs add ${short} "${name}" --yes ...`);
    process.exit(1);
  }
  const entry = { name, kind: "other", context: "", registered: today() };
  if (reg[short]) entry.registered = reg[short].registered; // 覆盖保留原登记时间
  const args = rest.slice(2).filter((a) => a !== "--yes");
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--kind") { entry.kind = args[++i]; continue; }
    if (args[i] === "--context") { entry.context = args[++i]; continue; }
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      const val = args[i + 1];
      if (val === undefined || val.startsWith("--")) die(`missing value for ${args[i]}`);
      entry[key] = val;
      i++;
      continue;
    }
    die(`unknown arg: ${args[i]}`);
  }
  if (!entry.context) die("--context is required (one-line scene, guards against cross-domain name clashes)");
  reg[short] = entry;
  save(reg);
  console.log(`registered: ${short} = ${entry.name} (${entry.kind}) — ${entry.context}`);
  process.exit(0);
}

if (cmd === "remove") {
  const short = rest[0];
  if (!short) die("usage: remove <short>");
  const reg = load();
  if (!reg[short]) die(`not found: ${short}`);
  delete reg[short];
  save(reg);
  console.log(`removed: ${short}`);
  process.exit(0);
}

die(`usage: alias.mjs <list|get|next|add|remove> ...`);

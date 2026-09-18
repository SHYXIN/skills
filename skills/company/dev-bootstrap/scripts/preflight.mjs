#!/usr/bin/env node
// dev-bootstrap preflight engine
// Usage:
//   node preflight.mjs --repo <repoPath> [--fix] [--json] [--profile <name>]
// Reads profiles/<name>.json (auto-matched via package.json name if --profile omitted),
// runs checks, prints report. --fix executes fixCmd for failed "fix" severity items.

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const profilesDir = resolve(scriptDir, "..", "profiles");

const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : undefined;
};
const repo = resolve(getArg("--repo") || process.cwd());
const doFix = args.includes("--fix");
const asJson = args.includes("--json");
const profileArg = getArg("--profile");

function loadProfile() {
  if (profileArg) {
    return JSON.parse(readFileSync(join(profilesDir, `${profileArg}.json`), "utf8"));
  }
  // auto-match via root package.json name
  const pkgPath = join(repo, "package.json");
  if (existsSync(pkgPath)) {
    const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
    const names = [pkg.name].filter(Boolean);
    const files = existsSync(profilesDir) ? readdirSync(profilesDir) : [];
    for (const file of files) {
      if (!file.endsWith(".json")) continue;
      const p = JSON.parse(readFileSync(join(profilesDir, file), "utf8"));
      const matchNames = p.match?.packageJsonNames || [];
      if (names.some((n) => matchNames.includes(n))) {
        return { ...p, __profile: file.replace(/\.json$/, "") };
      }
    }
  }
  return null;
}

function runCheck(check) {
  const c = check.check;
  switch (c.type) {
    case "pathExists": {
      // absolute paths (e.g. vswhere) are used as-is; relative resolved from repo root
      const absPath = /^[A-Za-z]:[\\/]/.test(c.path) ? c.path : join(repo, c.path);
      return existsSync(absPath);
    }
    case "fileContains": {
      const absPath = /^[A-Za-z]:[\\/]/.test(c.path) ? c.path : join(repo, c.path);
      if (!existsSync(absPath)) return false;
      if (!c.needle) return true; // presence-only check
      return readFileSync(absPath, "utf8").includes(c.needle);
    }
    case "commandSucceeds": {
      // Run a command; exit 0 (and optional combined-output needle) = pass.
      const r = spawnSync(c.cmd, {
        cwd: repo,
        shell: process.platform === "win32",
        encoding: "utf8",
        timeout: c.timeoutMs || 30_000,
        windowsHide: true,
      });
      const out = `${r.stdout || ""}${r.stderr || ""}`;
      if (r.status !== 0) return false;
      if (c.needle && !out.includes(c.needle)) return false;
      return true;
    }
    default:
      return null; // unknown check type -> treated as skip
  }
}

function runFix(cmd) {
  console.log(`\n[fix] $ ${cmd}`);
  const r = spawnSync(cmd, {
    cwd: repo,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: process.env,
  });
  return r.status === 0;
}

function main() {
  const profile = loadProfile();
  if (!profile) {
    console.error(
      `No profile matched for ${repo}. Available: ${existsSync(profilesDir) ? readdirSync(profilesDir).join(", ") : "(none)"}\n` +
        `Pass --profile <name> or add a profile JSON under profiles/.`
    );
    process.exit(2);
  }
  console.log(`[preflight] repo=${repo} profile=${profile.__profile || profileArg} fix=${doFix}`);

  const results = [];
  for (const check of profile.checks) {
    const pass = runCheck(check);
    results.push({ id: check.id, severity: check.severity, label: check.label, pass });
  }

  const failed = results.filter((r) => r.pass === false);
  const report = { repo, profile: profile.__profile || profileArg, results };

  if (asJson) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log("");
    for (const r of results) {
      const mark = r.pass === true ? "PASS" : r.pass === false ? "FAIL" : "SKIP";
      console.log(`[${mark}] (${r.severity}) ${r.id} — ${r.label}`);
    }
  }

  // handle failures
  for (const r of failed) {
    const check = profile.checks.find((c) => c.id === r.id);
    if (!check?.fixCmd) continue;
    if (check.severity === "fix" && doFix) {
      const ok = runFix(check.fixCmd);
      r.fixed = ok;
      if (ok) r.pass = runCheck(check); // re-verify
    } else if (check.severity === "prompt" || (check.severity === "fix" && !doFix)) {
      console.log(`\n[ACTION REQUIRED] ${r.id}: ${check.checkHint || ""}`);
      console.log(`  fix: ${check.fixCmd}`);
    }
  }

  const stillFailing = results.filter((r) => r.pass === false);
  if (!asJson) {
    console.log(
      stillFailing.length === 0
        ? "\n[preflight] all checks passed"
        : `\n[preflight] ${stillFailing.length} check(s) still failing: ${stillFailing.map((r) => r.id).join(", ")}`
    );
  }
  process.exit(stillFailing.length === 0 ? 0 : 1);
}

main();

#!/usr/bin/env node
// Three-layer validation for a compiled knowledge workspace.
// Usage: node validate.mjs <project-root> [--deepworks <repo-path>]
// Layer 1: ontology-spec.yaml passes deepworks Zod parse
// Layer 2: instances pass validateOntologyInstances (objects.json + links.json vs spec)
// Layer 3: list-outputs.mjs reads entities/relations with zero issues
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';

const require = createRequire(import.meta.url);
const root = resolve(process.argv[2] || '.');
const dwArgIdx = process.argv.indexOf('--deepworks');
const DEEPWORKS = dwArgIdx > -1 ? resolve(process.argv[dwArgIdx + 1])
  : (process.env.DEEPWORKS_REPO || 'C:/code_proj/deepworks');

let failures = 0;
const fail = (msg) => { console.error('FAIL:', msg); failures++; };
const ok = (msg) => console.log('OK:', msg);

// ---- Layer 1: spec parse ----
const schemaMod = await import(`file:///${join(DEEPWORKS, 'packages/types/dist/deepworks/knowledge/ontology-schema.js').replace(/\\/g, '/')}`);
const yaml = require(join(DEEPWORKS, 'packages/types/node_modules/yaml'));
const specRaw = readFileSync(join(root, 'reference/ontology-spec.yaml'), 'utf8');
const parsed = schemaMod.parseOntologySchemaYaml(specRaw);
if (!parsed.success) {
  const issues = JSON.parse(parsed.error.message);
  fail(`ontology-spec.yaml Zod 校验失败，${issues.length} 个问题（前 5 个）：`);
  for (const i of issues.slice(0, 5)) console.error('  ', i.path.join('.'), '::', i.code);
} else {
  ok(`ontology-spec.yaml 通过 Zod 校验（${parsed.data.object_types.length} 对象类型, ${parsed.data.link_types.length} 关系类型）`);
}

// ---- Layer 2: instance validation ----
const spec = yaml.parse(specRaw);
const objects = JSON.parse(readFileSync(join(root, 'foil/ontology/objects.json'), 'utf8'));
const links = JSON.parse(readFileSync(join(root, 'foil/ontology/links.json'), 'utf8'));
const typeByName = Object.fromEntries(spec.object_types.map(t => [t.name, t]));
const linkByName = Object.fromEntries(spec.link_types.map(t => [t.name, t]));
const mapObjs = objects.map(o => ({
  object_type_id: typeByName[o.object_type]?.id,
  primary_key: o.primary_key, properties: o.properties, deepworks: o.deepworks,
}));
const mapLinks = links.map(l => ({
  link_type_id: linkByName[l.link_type]?.id,
  source_primary_key: l.source_primary_key,
  target_primary_key: l.target_primary_key,
  properties: l.properties ?? {}, deepworks: l.deepworks,
}));
const instMod = await import(`file:///${join(DEEPWORKS, 'packages/types/dist/deepworks/knowledge/ontology-instance-validation.js').replace(/\\/g, '/')}`);
const result = instMod.validateOntologyInstances({ schema: spec, objects: mapObjs, links: mapLinks });
if (!result.success) {
  const codes = {};
  for (const i of result.issues) codes[i.code] = (codes[i.code] ?? 0) + 1;
  fail(`实例校验失败: ${JSON.stringify(codes)}`);
  for (const i of result.issues.slice(0, 5)) console.error('  ', i.code, i.path.join('.'), i.message);
} else {
  ok(`实例校验通过（${result.data.objects.length} 对象, ${result.data.links.length} 关系）`);
}

// ---- Layer 3: official list-outputs ----
const lo = join(DEEPWORKS, '.opencode/skills/deepworks-knowledge-center/scripts/list-outputs.mjs');
if (existsSync(lo)) {
  const out = JSON.parse(execFileSync('node', [lo], { cwd: root, encoding: 'utf8' }));
  if (out.counts.issueCount > 0) fail(`list-outputs 报告 ${out.counts.issueCount} 个 issue`);
  else if (out.counts.entityCount === 0 && out.counts.relationCount === 0) fail('list-outputs 读到 0 实体 0 关系');
  else ok(`list-outputs: ${out.counts.entityCount} 实体, ${out.counts.relationCount} 关系, 0 issue`);
} else {
  console.log('SKIP: list-outputs.mjs 不存在（deepworks 仓库未找到）');
}

if (failures > 0) { console.error(`\n${failures} 层校验失败`); process.exit(1); }
console.log('\n全部校验通过');

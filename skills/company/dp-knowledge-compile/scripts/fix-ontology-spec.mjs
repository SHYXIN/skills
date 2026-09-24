// Fix ontology-spec.yaml to pass deepworks Zod validation (schema v3).
// Usage: node fix-ontology-spec.mjs <path-to-ontology-spec.yaml>
// Loads the spec, fills all fields required by DeepWorksOntologySchema,
// validates with deepworks' own parser, writes back only when clean.
import { readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const DEEPWORKS = 'C:/code_proj/deepworks';
const yaml = require(`${DEEPWORKS}/packages/types/node_modules/yaml`); // same yaml lib deepworks uses
const { parseOntologySchemaYaml, stringifyOntologySchemaYaml } = await import(
  'file:///C:/code_proj/deepworks/packages/types/dist/deepworks/knowledge/ontology-schema.js'
);
const { validateOntologySemantics: validateOntologySchema } = await import(
  'file:///C:/code_proj/deepworks/packages/types/dist/deepworks/knowledge/ontology-schema-validation.js'
);

const target = process.argv[2];
if (!target) {
  console.error('usage: node fix-ontology-spec.mjs <ontology-spec.yaml>');
  process.exit(1);
}

const raw = readFileSync(target, 'utf8');
const doc = yaml.parse(raw);

// ---- top level ----
doc.icon ??= null;
doc.color ??= null;
doc.labels ??= [];

// ---- object_types ----
for (const ot of doc.object_types ?? []) {
  ot.category = ot.category && ot.category.length > 0 ? ot.category : null;
  ot.icon = ot.icon && ot.icon.length > 0 ? ot.icon : null;
  // color must match ^#[0-9A-Fa-f]{6}$ or be null
  if (typeof ot.color !== 'string' || !/^#[0-9A-Fa-f]{6}$/.test(ot.color)) ot.color = null;
  ot.is_abstract ??= false;
  ot.extends_object_type_id ??= null;
  ot.type_version ??= '1.0.0';
  ot.related_dataset_id ??= null;
  ot.related_dataset_metadata ??= null;
  ot.related_database ??= null;
  ot.related_table_name ??= null;
  ot.derived_properties ??= [];
}

// ---- link_types ----
for (const lt of doc.link_types ?? []) {
  lt.reverse_showname ??= null;
  lt.cardinality ??= 'MANY_TO_MANY';
  lt.source_property_ids ??= [];
  lt.target_property_ids ??= [];
  lt.is_both_direct ??= false;
  lt.related_dataset_id ??= null;
  lt.related_resource_name ??= null;
  lt.related_table_name ??= null;
  lt.related_source_column_names ??= [];
  lt.related_target_column_names ??= [];
  lt.properties ??= [];
  lt.derived_properties ??= [];
}

// ---- deepworks block ----
if (!doc.deepworks) {
  doc.deepworks = {
    schema_version: 3,
    workspace_id: '11111111-1111-4111-8111-111111111111',
    goals: ['从 Wiki 提取可追溯的知识对象和关系'],
    object_mappings: (doc.object_types ?? []).map((ot) => ({
      object_type_id: ot.id,
      source_selector: { topic_ids: [], page_type_ids: [], local_directory_hint: null },
      property_mappings: [],
      update_strategy: 'identity',
      projection: { kind: 'object', index: 'foil/ontology/ontology.sqlite' },
    })),
    link_mappings: (doc.link_types ?? []).map((lt) => ({
      link_type_id: lt.id,
      extract_from: ['frontmatter.related'],
      property_mappings: [],
    })),
    source_types: [],
    governance: {
      publish_statuses: ['accepted', 'published'],
      review_on_low_evidence: true,
    },
  };
}

// ---- serialize with official stringifier ----
const nextYaml = stringifyOntologySchemaYaml(doc);

// ---- verify with deepworks own parser before writing ----
const reparsed = parseOntologySchemaYaml(nextYaml);
if (!reparsed.success) {
  const issues = JSON.parse(reparsed.error.message);
  console.error('STILL INVALID after fix,', issues.length, 'issues:');
  const seen = new Set();
  for (const i of issues) {
    const key = i.path.join('.') + '|' + i.code;
    if (seen.has(key)) continue;
    seen.add(key);
    console.error(' ', i.path.join('.'), '::', i.code);
  }
  process.exit(2);
}
const issues = validateOntologySchema(reparsed.data);
if (issues.length > 0) {
  console.error('SEMANTIC issues:', JSON.stringify(issues, null, 2).slice(0, 4000));
  process.exit(3);
}

copyFileSync(target, `${target}.bak`);
writeFileSync(target, nextYaml, 'utf8');
console.log('OK: fixed and validated. backup at', `${target}.bak`);

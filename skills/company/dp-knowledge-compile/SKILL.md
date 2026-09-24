---
name: dp-knowledge-compile
description: 把 xmind 诊断树/知识树一键编译成 deepworks 知识中心可加载的本地知识库。自动生成项目骨架、拉取线上 foil schema（或用本地基准）、编译实体与关系、三层校验（spec Zod / 实例 / list-outputs）全绿才交付。业务无关，换领域只改 mappings.yaml。用户手动调用（/dp-knowledge-compile）。
---

# dp-knowledge-compile

把"手工在 deepworks 里搭知识库"压缩成一条命令。像食品加工机：丢进 xmind 原料和 schema 配方，产出 deepworks 直接可加载的标准知识库。

## 前置条件

- 本地 deepworks 仓库（默认探测 `C:/code_proj/deepworks`，可用 `--deepworks` 或环境变量 `DEEPWORKS_REPO` 覆盖）——提供官方校验器
- Python3（编译器）+ Node22（校验器）
- 拉线上 schema 时需要环境变量（**skill 不内置任何地址与凭据，缺失即失败**）：
  - `FOIL_BASE_URL`：如 `https://foil-test.deepexi.com`
  - `FOIL_KNOWLEDGE_CENTER_TARGET`：`test` 或 `production`
  - `DEEPWORKS_AGENT_FOIL_ACCOUNT` / `DEEPWORKS_AGENT_FOIL_PASSWORD`（或 `_TEST` 后缀对）

## 全流程（一键）

```bash
# 第 0 步：拉 schema（已有 reference/foil-schema-online.json 或 ontology-spec.yaml 则跳过）
python <skill_dir>/scripts/fetch_schema.py --project-id <foil项目uuid> --out <项目>/reference/foil-schema-online.json

# 第 1 步：生成项目骨架（json schema 会自动转成过校验的 ontology-spec.yaml）
python <skill_dir>/scripts/scaffold.py --project-root <项目目录> --project-name <英文短名> \
    --display-name <中文名> --schema <schema.json 或现成 spec.yaml>

# 第 2 步：放 mappings.yaml（从 <skill_dir>/templates/mappings.yaml 复制后按业务改）

# 第 3 步：编译 xmind（产物：objects.json / links.json / ontology.sqlite）
cd <项目目录> && python scripts/compile_xmind.py <xmind路径>

# 第 4 步：三层校验（spec Zod → 实例 → list-outputs），全绿才算成功
node <skill_dir>/scripts/validate.mjs <项目目录>
```

## 工作方式

1. **骨架**：`scaffold.py` 生成 SKILL.md / wiki-spec.yaml / 目录结构 / 编译脚本副本 / knowledge-center skill 副本
2. **编译**：`compile_xmind.py` 按 `reference/mappings.yaml` 识别节点类型、属性、关系：
   - 节点第一个 label = 对象类型（如 `设备`）；其余 label 按 `前缀:值` 解析为属性
   - `关系：X` label 声明"本节点→子节点"的边，方向按线上 schema 硬校验，错方向的边剔除并告警
   - 确定性 ID：`{前缀}{sha1(类型|路径)[:12]}`，重编译 ID 稳定
   - 编译后自动按 schema 声明剔除未声明属性（防 unknown_property）
3. **校验**：`validate.mjs` 三层——
   - Layer1 spec 过 deepworks Zod（失败给前 5 个 issue 路径）
   - Layer2 实例过 `validateOntologyInstances`（与 server 同函数）
   - Layer3 官方 `list-outputs.mjs` 读出实体/关系且 0 issue

## 失败速查

| 报错 | 根因 | 修复 |
| --- | --- | --- |
| 409 invalid_knowledge_schema | spec 未过 Zod | 跑 `fix-ontology-spec.mjs <spec路径>`（deepworks 仓库环境下） |
| 500 no such table | sqlite 缺表 | 重跑编译器（DDL 已内置 15 表） |
| 409 对象数据无法合并 | deepworks 块缺键/端点不存在/属性未声明 | 看 validate.mjs Layer2 输出对症修 |
| FOIL_BASE_URL 未设置 | 凭据环境变量缺失 | 按"前置条件"注入，skill 绝不内置地址 |

## 换领域

只改 `reference/mappings.yaml`：label→类型映射、属性前缀表、关系 label 表、ID 前缀。编译器和校验器零改动。

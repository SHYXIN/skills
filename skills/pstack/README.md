# pstack

从 [pstack](https://github.com/backnotprop/pstack)（作者 Lauren Tan / poteto）挑选过来的技能副本，用于和推荐搭配 `mattpocock/skills` 里的同名技能**并存**。

## 为什么有这个 bucket

推荐搭配之间只有两个技能重名：`tdd` 和 `teach`，都发生在 pstack 与 `mattpocock/skills` 之间。`npx skills` / `cn-skills` 把技能平铺到同一目录（`~/.agents/skills/<name>`），**同名后装者胜、无冲突提示**。本仓库的安装脚本把 matt 放在 pstack 之后，于是 `tdd` / `teach` 默认采用 matt 版。

但有时仍想用 pstack 的那两个版本，所以在这里放两份**改名副本**：

| 本 bucket 目录 | frontmatter `name` | 来源 | 对应 matt 版的 `tdd` / `teach` |
| --- | --- | --- | --- |
| `tdd-pstack/` | `tdd-pstack` | pstack `skills/tdd` | 与 matt `tdd` 并存 |
| `teach-pstack/` | `teach-pstack` | pstack `skills/teach` | 与 matt `teach` 并存 |

安装后效果：`tdd` / `teach` = matt 版，`tdd-pstack` / `teach-pstack` = pstack 版，四者互不覆盖。

## 维护约定

- 内容为 pstack 原样复制，**仅改 frontmatter `name`**（加 `-pstack` 后缀），其余不动。
- 复制源为 pstack 权威仓 `backnotprop/pstack` 的冻结版 `v0.15.15`（commit `3a60467`）。升级时从新冻结版重新复制对应目录，再改回 `name`。
- 这是**改名副本**，不是镜像：上游 pstack 更新不会自动流入这里，需按上面规则手工同步。
- 两个技能都是「锦上添花」性质的自洽副本：`tdd-pstack` 单文件无内部引用；`teach-pstack` 引用 pstack 自有的 `how` / `why`，整包 pstack 仍会装着，引用不断。

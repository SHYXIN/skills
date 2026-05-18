# 想法炼金师 (Idea Alchemist)

> 把模糊想法变成清晰需求文档的引导式对话产品

通过苏格拉底式追问，帮普通人有想法但没有技术背景的人，把脑子里的模糊想法变成：
- **B（产品蓝图）** — 自己能看懂、能拿去跟人讲的产品说明书
- **C（技术规格）** — 可以直接交给 AI 编码工具去实现的结构化文档

## 工作方式

1. 用户输入一句话想法
2. 系统通过 5 轮引导式追问逐步澄清（每轮带推荐答案）
3. 生成产品蓝图（B），用户确认/修改
4. 生成技术规格（C）

## 文件结构

- `SKILL.md` — Skill 定义文件，可在 Claude Code / 扣子等平台上安装使用
- `PRODUCT_BLUEPRINT.md` — 产品设计文档（用想法炼金师自己生成的）

## 安装

### Claude Code

```bash
npx skills add https://github.com/你的用户名/idea-alchemist
```

## License

MIT

---
name: skill-bundler
description: 把用户的 agent skills 逐个打成独立 zip，方便上传到平台。默认源是当前用户 ~/.agents/skills，每个 skill 一个 <name>.zip（zip 内保留 <name>/ 顶层目录），并附 MANIFEST.txt。user-invoked，模型不自动触发。
disable-model-invocation: true
---

# 技能打包上传（Skill Bundler）

把 `~/.agents/skills` 下的 skill **逐个**打成独立 zip，方便你一个一个上传到平台。每个 skill 产出 `<name>.zip`，zip 内保留 `<name>/` 顶层目录（解压即得 skill 目录，和 `agent-package-sync` 一致），并附一份 `MANIFEST.txt` 列出每个 zip 与来源。

默认源：`~/.agents/skills`（Windows 也认 `~/.codebuddy/skills` 作回退）。默认打包**全部** skill，也支持按名字筛选。

## 用法

```bash
# 打包全部 skill，输出到当前目录的 skills-zips/（每个 skill 一个 zip）
python <skill>/scripts/bundle_skills.py

# 指定源目录
python <skill>/scripts/bundle_skills.py --root /path/to/skills

# 只打包某几个
python <skill>/scripts/bundle_skills.py --skill writing-for-agents-wx --skill wait-what-wx

# 排除某几个
python <skill>/scripts/bundle_skills.py --exclude grill-one

# 指定输出目录
python <skill>/scripts/bundle_skills.py --output-dir ~/Desktop/my-skills
```

参数：
- `--root`：skills 根目录（默认 `~/.agents/skills`）
- `--output-dir`：输出目录（默认 `./skills-zips`）
- `--skill <name>`：只打包指定 skill，可多次；默认全部
- `--exclude <name>`：排除指定 skill，可多次
- `--all`：显式打包全部（默认就是全部，可省略）

## 打包规则

- 每个 skill → `<output-dir>/<name>.zip`；zip 内顶层为 `<name>/`，保留该 skill 自己的目录结构。
- 同名 skill 出现在不同分类时，zip 名退回 `<category>-<name>.zip` 以避免覆盖。
- 自动排除：`__pycache__/`、`*.pyc`、`node_modules/`、`.git/`、`venv/`、`*.cache` 类目录、`.DS_Store`、`Thumbs.db`、以及已存在的 `*.zip`，避免把缓存和旧包打进去。
- 每个空 skill 写一个 `.keep` 占位，避免平台认为目录缺失。
- 生成 `MANIFEST.txt`：列出源根目录、生成时间、skill 数量、输出目录，以及每个 zip 对应的来源路径与文件数。

## 注意

- 输出目录里若已有上一次跑出来的 zip，本脚本不会自动清理——重新打包前按需手动清空，避免残留旧 zip 混进上传。
- 不执行 `git add` / `commit` / `push`，也不删除或改动源 skill 目录，只产出 zip。

## 禁止事项

- 不自动上传——只产出 zip，上传由你手动完成。

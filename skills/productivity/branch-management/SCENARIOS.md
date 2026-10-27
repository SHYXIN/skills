# 场景手册

五个场景的完整流程与异常处理。场景互斥，按用户意图进入对应场景。身份配置、操作边界、进入技能后的前置检查见 SKILL.md。

## 场景 1：新建 feature 分支

触发语义：
- "新建分支"
- "开一个 feature"
- "开始新任务"
- "帮我切分支"

流程：

1. 读取 `skill.initials`（未配置则按 SKILL.md「用户身份」一节先完成设置）。
2. 询问或提取任务名，将其转成 kebab-case 英文短语，3-6 个词以内。
3. 生成当天日期 `YYYYMMDD`。
4. 生成分支名：
   ```text
   feature/<initials>-YYYYMMDD-<task>
   ```
5. 拉取远端：
   ```bash
   git fetch --all --prune
   ```
6. 切到基线分支并更新：
   ```bash
   git checkout develop
   git pull origin develop
   ```
7. 创建 feature 分支：
   ```bash
   git checkout -b feature/<initials>-YYYYMMDD-<task>
   ```
8. 推送并设置 upstream：
   ```bash
   git push -u origin feature/<initials>-YYYYMMDD-<task>
   ```
9. 汇报当前分支名和下一步建议。

命名禁忌：
- 不使用 `test`、`temp`、`patch`、`new` 等无意义名
- 不使用中文、空格、大写、特殊字符
- 一个 feature 分支只承载一件事

## 场景 2：同步集成分支到当前 feature

触发语义：
- "同步 develop"
- "更新当前分支"
- "把 develop 合进来"
- "rebase develop"

流程：

1. 确认当前分支是 feature 分支。
2. 执行：
   ```bash
   git fetch origin
   git rebase origin/develop
   ```
3. 如果 rebase 成功，询问用户是否推送重写后的远端历史。
4. 用户确认后执行：
   ```bash
   git push --force-with-lease
   ```

如果发生冲突：
- 停下来汇报冲突文件。
- 指导用户或直接协助解决冲突。
- 冲突解决后继续：
  ```bash
  git add <resolved-files>
  git rebase --continue
  ```

## 场景 3：提交并 push

触发语义：
- "提交一下"
- "commit"
- "提交并推送"
- "push 当前改动"

流程：

1. 查看改动：
   ```bash
   git status --short
   git diff --stat
   ```
2. 根据改动内容建议 Conventional Commits 消息。`type` 和 `scope` 使用英文，冒号后的 summary 使用中文：
   ```text
   <type>(<scope>): <中文摘要>
   ```
3. 常用 type：
   - `feat`：新功能，例如 `feat(chat): 添加消息时间显示`
   - `fix`：修复 bug，例如 `fix(login): 处理空的 OAuth 回调地址`
   - `docs`：文档改动，例如 `docs(readme): 更新部署说明`
   - `style`：代码风格，不影响逻辑，例如 `style(frontend): 使用 Prettier 格式化`
   - `refactor`：重构，不加功能不修 bug，例如 `refactor(api): 抽取 token 中间件`
   - `perf`：性能优化，例如 `perf(query): 增加看板数据缓存`
   - `chore`：构建、工具、依赖，例如 `chore(deps): 升级 vite 到 6.0`
   - `test`：测试相关，例如 `test(unit): 添加认证服务 mock`
   - `hotfix`：紧急线上修复，例如 `hotfix: 回滚聊天面板异常部署`
4. 只 add 与本次任务相关的文件。
5. 提交身份护栏（commit 前必做）：
   - 读取 `git config --get skill.email`：
     - 未配置 → 跳过校验，直接提交。
     - 已配置 → 与 `git config --get user.email` 比对：
       - 一致 → 正常提交。
       - **不一致 → 拒绝 commit**，报错说明两者不一致，提示用户修正本机 git 配置后再试。错误身份的 commit 事后要靠历史重写来补救，代价远高于提交前拦一下，所以这里没有"继续提交"的选项。
6. 护栏通过后执行 commit 和 push：
   ```bash
   git add <files>
   git commit -m "<type>(<scope>): <中文摘要>"
   git push
   ```

如果当前分支没有 upstream：
```bash
git push -u origin <current-branch>
```

## 场景 4：MR 前检查

触发语义：
- "MR 前检查"
- "准备提 MR"
- "检查能不能合"
- "发起 merge request"

流程：

1. 确认当前分支不是 `develop` / `main` / `master`。
2. 检查状态：
   ```bash
   git status --short
   git log --oneline --decorate -n 10
   git fetch origin
   ```
3. 确认当前 feature 已同步基线：
   ```bash
   git rebase origin/develop
   ```
4. rebase 后如需强推，必须先确认，再执行：
   ```bash
   git push --force-with-lease
   ```
5. 输出 MR 信息：
   - 源分支：当前 feature 分支
   - 目标分支：`develop` 或用户确认的基线分支
   - 标题：使用 Conventional Commits 风格
   - Reviewer：至少 1 人

MR 描述模板：

```markdown
## 改动内容
<!-- 一两句话说清楚做了什么 -->

## 相关 Issue / 任务
<!-- 例如：close #42、ref #38 -->

## 测试方式
<!-- 怎么验证这个改动是对的 -->
- [ ] Step 1: ...
- [ ] Step 2: ...

## Checklist
- [ ] 代码自测通过
- [ ] 没有误改无关文件
- [ ] 已处理 feature 分支与基线分支的冲突
- [ ] commit 历史整洁
```

## 场景 5：合并后清理 feature 分支

触发语义：
- "清理分支"
- "MR 合了，删分支"
- "删除 feature 分支"

流程：

1. 确认 feature 分支已合并。
2. 核对分支前缀：目标分支的 `<initials>` 不是本人前缀时，按 SKILL.md「分支归属防线」先向用户确认归属，确认是别人的分支就停手。
3. 切回基线分支并更新：
   ```bash
   git checkout develop
   git pull origin develop
   ```
4. 删除本地 feature 分支前先确认。
5. 用户确认后：
   ```bash
   git branch -d feature/<initials>-YYYYMMDD-<task>
   ```
6. 删除远端 feature 分支前再次确认。
7. 用户确认后：
   ```bash
   git push origin --delete feature/<initials>-YYYYMMDD-<task>
   ```

如果 `git branch -d` 拒绝删除，说明 Git 认为未合并。此时先调查合并状态，改用 `-D` 前必须查明原因并向用户说明。

## 异常处理

### 当前仓库没有 develop

询问用户本仓库的集成分支是哪一个。得到答案后，本轮都使用该分支作为基线。

### 当前分支不是 feature

如果用户要提交或同步，先说明当前分支名，并确认是否继续。`main` / `master` 上不直接提交或推送。

### 有未提交改动且需要切分支

提供两个选项：
- 在当前分支直接创建 feature，保留工作区改动
- stash 后切到基线分支，再创建干净 feature

用户确认后再执行 stash。

### rebase 冲突

停下并汇报冲突文件。冲突解决前保持本地状态，push 留到解决之后。

### 误删未 push 的本地分支

指导恢复：
```bash
git reflog
git checkout -b feature/<initials>-YYYYMMDD-<task> <reflog-hash>
```

## 完成报告

每次操作结束后，用简短报告说明：
- 当前仓库
- 当前分支
- 已执行的关键命令
- 是否已推送远端
- 还需要用户手动完成的事项，例如创建 MR 或指定 Reviewer

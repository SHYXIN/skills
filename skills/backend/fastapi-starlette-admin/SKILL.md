---
name: fastapi-starlette-admin
description: 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。当用户说"加 admin"、"加管理后台"、"集成 starlette-admin"、"admin panel"、"后台管理"时触发。
---

# FastAPI + Starlette-Admin 快速集成

给 FastAPI 项目快速加入基于 starlette-admin 的 CRUD 管理面板。

## 前置依赖

```bash
pip install starlette-admin itsdangerous jinja2
# 如果项目用 async 数据库驱动，还需要同步驱动：
pip install pymysql        # MySQL (对应 aiomysql)
# pip install psycopg2-binary  # PostgreSQL (对应 asyncpg)
```

## 工作流

### Phase 1: 检测项目状态（2-3 个问题）

**必须先问用户以下问题，再生成代码：**

1. **项目状态**：从零开始 or 已有 FastAPI 项目？
   - 已有项目：读取 `config.py`/`settings.py`、`database.py`、`main.py`、`models/` 检测现有结构
   - 新项目：生成完整骨架

2. **数据库类型**？
   - A) Async 主引擎（aiomysql / asyncpg / aiosqlite）→ 需要生成同步引擎适配
   - B) 纯同步（pymysql / psycopg2 / sqlite）→ 直接用同一引擎
   - C) SQLite 快速启动 → 简化配置

3. **需要认证吗**？
   - A) 需要（默认）→ 生成 Session-based AuthProvider
   - B) 不需要（内部工具/开发）→ 跳过 auth，`auth_provider=None`

### Phase 2: 生成代码

按 [TEMPLATES.md](./TEMPLATES.md) 的模板逐文件生成：`app/admin/__init__.py`、`auth.py`（仅需要认证时）、`views.py`、`templates/dashboard.html`，并标注 `database.py`（sync 引擎适配）和 `main.py`（SessionMiddleware + mount）的修改点。模板中所有 `TODO` 按用户实际模型替换。

### Phase 3: 验证

生成代码后，告诉用户验证步骤：

1. **启动后端**：`uvicorn app.main:app --reload`
2. **访问 admin**：`http://localhost:8000/admin`
3. **登录**：使用管理员账号密码
4. **检查**：
   - 侧边栏菜单正常显示
   - 语言切换按钮出现在右上角（头像旁）
   - 列表页有 Export / Filter / Show/Hide columns 按钮
   - 选中行后 batch actions 下拉菜单出现
   - Dashboard 显示统计卡片

## 踩坑记录

本 skill 基于实际项目经验整理，以下是已解决的坑：

| 坑 | 原因 | 解决方案 |
|----|------|----------|
| 侧边栏/菜单不渲染 | Dashboard 模板用了 `{% block body %}` 覆盖了 layout.html 的整个页面结构 | 改用 `{% block content %}` 和 `{% block header %}` |
| Export/Filter 按钮不显示 | DataTables i18n 文件 404（如 `dt/zh.json`）导致 JS 初始化失败 | 确保 `default_locale` 对应的 i18n 文件存在，或用 `en` |
| `momentjs/zh.js` 404 | `default_locale="zh"` 但 starlette-admin 没有简体中文语言包 | 用 `en` 或 `zh_Hant`（繁体中文） |
| `Admin()` 报 TypeError | Admin 构造函数第一个参数是 engine，不是 app | `Admin(engine, ...)` |
| 404 Not Found | `base_url` 和 `app.mount` 路径重复 | `base_url="/admin"`，`admin.mount_to(app)` |
| 无限重定向到登录页 | SessionMiddleware 未添加或添加位置错误 | 在 FastAPI app 上、create_admin 之前添加 SessionMiddleware |
| `No module named 'itsdangerous'` | starlette session 中间件依赖缺失 | `pip install itsdangerous` |
| AuthProvider 连接池泄漏 | 手动创建的 sync session 未关闭 | 用 `try/finally: db.close()` 确保关闭 |
| batch actions 不显示 | actions 默认 `display: none`，选中行后才显示 | 正常行为，选中行即可看到 |
| 自定义模板找不到 layout.html | templates_dir 只包含本地目录，不包含 starlette_admin 包模板 | 使用 `templates_dir` 参数，Jinja2 ChoiceLoader 会自动合并 |
| i18n 翻译不生效 | Admin.__init__ 会覆盖 Jinja2 的 gettext | 在 Admin.__init__ 之后调用 `patch_admin_templates()` 重新安装（高级用法） |

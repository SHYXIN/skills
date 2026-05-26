---
name: fastapi-starlette-admin
description: 给 FastAPI 项目快速集成 starlette-admin 管理面板。自动检测项目结构（从零开始 or 已有项目），处理 async/sync 引擎双轨制，生成完整的 admin 配置（含 AuthProvider、ModelView、batch actions、自定义 Dashboard、i18n 语言切换），标注 database.py 和 main.py 的修改点。当用户说"加 admin"、"加管理后台"、"集成 starlette-admin"、"admin panel"、"后台管理"时触发。
---

# FastAPI + Starlette-Admin 快速集成

给 FastAPI 项目快速加入基于 starlette-admin 的 CRUD 管理面板。

## 触发条件

当用户说"加 admin"、"加管理后台"、"集成 starlette-admin"、"admin panel"、"后台管理"时触发。

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

根据 Phase 1 的答案，生成以下文件。

---

#### 文件 1：`app/admin/__init__.py`（新建）

核心工厂函数。**以下模板按"已有 async 项目 + 需要认证"生成，其他场景按需裁剪。**

```python
"""Starlette-Admin 管理面板配置。"""
import os

from starlette_admin.contrib.sqla import Admin
from starlette_admin import I18nConfig
from app.admin.views import DashboardView, YourModel1View, YourModel2View  # TODO
from app.admin.auth import AdminAuthProvider
from app.core.database import db_manager  # TODO: 替换为你的数据库管理器


def create_admin(app):
    """创建并配置 starlette-admin，挂载到 FastAPI app。

    ⚠️ 关键：
    1. Admin 构造函数第一个参数是 sync_engine（不是 app）
    2. starlette-admin 需要同步引擎，不能直接用 async 引擎
    3. 调用 admin.mount_to(app) 挂载
    4. templates_dir 必须存在（os.makedirs）
    """
    # 获取同步引擎（starlette-admin 不支持 async 引擎）
    engine = db_manager.get_sync_engine()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    admin = Admin(
        engine=engine,
        title="管理后台",  # TODO: 修改为你的标题
        base_url="/admin",
        route_name="admin",
        templates_dir=templates_dir,
        index_view=DashboardView(),
        auth_provider=AdminAuthProvider(),
        i18n_config=I18nConfig(
            default_locale="en",
            language_switcher=["en", "zh_Hant"],  # 语言切换按钮，按需调整
        ),
    )

    # 注册视图
    admin.add_view(YourModel1View(YourModel1, engine))  # TODO
    admin.add_view(YourModel2View(YourModel2, engine))  # TODO

    # 挂载到 FastAPI
    admin.mount_to(app)

    return admin
```

**⚠️ 如果用户选择"不需要认证"：**
```python
    admin = Admin(
        engine=engine,
        title="管理后台",
        base_url="/admin",
        route_name="admin",
        templates_dir=templates_dir,
        index_view=DashboardView(),
        auth_provider=None,  # 无认证
        i18n_config=I18nConfig(default_locale="en"),
    )
```

---

#### 文件 2：`app/admin/auth.py`（新建，仅需要认证时）

```python
"""Starlette-Admin 认证提供者。"""
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from sqlalchemy.orm import sessionmaker
from app.core.database import db_manager  # TODO
from app.models.user import User  # TODO: 替换为你的用户模型
from app.core.security import pwd_context  # TODO: 替换为你的密码验证工具


class AdminAuthProvider(AuthProvider):
    """Session-based 认证，仅允许管理员登录。"""

    def __init__(self):
        super().__init__()
        engine = db_manager.get_sync_engine()
        self.SessionLocal = sessionmaker(engine)

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user or not pwd_context.verify(password, user.password_hash):
                raise ValueError("用户名或密码错误")
            # TODO: 根据你的角色字段调整
            if user.role.value != "admin":
                raise ValueError("仅管理员可登录后台")
            request.session["admin_user_id"] = user.id
            request.session["admin_username"] = user.username
            return response
        finally:
            db.close()  # ⚠️ 必须手动关闭，防止连接池泄漏

    async def is_authenticated(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if not user_id:
            return False
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            # TODO: 根据你的角色字段调整
            return user is not None and user.role.value == "admin"
        finally:
            db.close()

    def get_admin_config(self, request: Request) -> AdminConfig:
        username = request.session.get("admin_username", "Admin")
        return AdminConfig(app_title=f"管理后台 — {username}")

    def get_admin_user(self, request: Request) -> AdminUser:
        username = request.session.get("admin_username", "Admin")
        return AdminUser(username=username)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
```

---

#### 文件 3：`app/admin/views.py`（新建）

包含 DashboardView + ModelView + batch actions 的完整模板。

```python
"""Starlette-Admin 视图定义。"""
import csv
import io
from typing import List, Any

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import CustomView, action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, YourModel1, YourModel2  # TODO


class DashboardView(CustomView):
    """管理后台首页仪表盘。

    ⚠️ 关键：模板必须 extends "layout.html"，用 {% block content %} 和 {% block header %}
    不要用 {% block body %} —— 会覆盖整个页面结构（侧边栏、导航栏全部丢失）
    """

    def __init__(self):
        super().__init__(
            label="仪表盘",
            icon="fa fa-dashboard",
            path="/",
            template_path="dashboard.html",
            add_to_menu=True,
        )

    async def render(self, request: Request, templates) -> Response:
        session: Session = request.state.session
        stats = self._collect_stats(session)
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"title": "仪表盘", "stats": stats},
        )

    def _collect_stats(self, session: Session) -> dict:
        # TODO: 替换为你自己的统计查询
        return {
            "user_count": session.query(func.count(User.id)).scalar(),
            "model1_count": session.query(func.count(YourModel1.id)).scalar(),
        }


class UserModelView(ModelView):
    """用户管理视图。"""
    # TODO: 替换为你的模型
    model = User
    label = "用户"
    icon = "fa fa-users"

    fields = [User.id, User.username, User.email, User.role, User.is_active,
              User.is_verified, User.created_at]
    search_fields = [User.username, User.email]
    exclude_fields_from_create = ["role", "password_hash"]
    exclude_fields_from_edit = ["role", "password_hash"]
    actions = ["delete", "toggle_active", "export_csv"]

    @action(
        name="toggle_active",
        text="切换激活状态",
        confirmation="确定要切换选中用户的激活状态吗？",
        submit_btn_text="确定",
        submit_btn_class="btn-warning",
        icon_class="fa fa-toggle-on",
    )
    async def toggle_active_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        users = session.query(User).filter(User.id.in_(pks)).all()
        count = 0
        for user in users:
            user.is_active = not user.is_active
            count += 1
        session.commit()
        return f"已切换 {count} 个用户的激活状态"

    @action(
        name="export_csv",
        text="导出 CSV",
        confirmation="确定要导出选中的数据吗？",
        submit_btn_text="导出",
        submit_btn_class="btn-success",
        icon_class="fa fa-download",
        custom_response=True,  # ⚠️ 返回文件下载时必须设为 True
    )
    async def export_csv_action(self, request: Request, pks: List[Any]) -> Response:
        session: Session = request.state.session
        items = session.query(User).filter(User.id.in_(pks)).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "用户名", "邮箱", "角色"])
        for item in items:
            writer.writerow([item.id, item.username, item.email, item.role.value])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )


class YourModel1View(ModelView):
    """TODO: 替换为你的模型管理视图。"""
    model = YourModel1
    label = "模型1"
    icon = "fa fa-table"

    fields = [YourModel1.id, YourModel1.title]  # TODO
    search_fields = [YourModel1.title]  # TODO
    actions = ["delete", "export_csv"]

    @action(
        name="export_csv",
        text="导出 CSV",
        confirmation="确定要导出选中的数据吗？",
        submit_btn_text="导出",
        submit_btn_class="btn-success",
        icon_class="fa fa-download",
        custom_response=True,
    )
    async def export_csv_action(self, request: Request, pks: List[Any]) -> Response:
        session: Session = request.state.session
        items = session.query(YourModel1).filter(YourModel1.id.in_(pks)).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "标题"])  # TODO
        for item in items:
            writer.writerow([item.id, item.title])  # TODO
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )


# 只读视图示例（如审计日志）
class AuditLogModelView(ModelView):
    """审计日志（只读）。"""
    # model = AuditLog  # TODO
    label = "审计日志"
    icon = "fa fa-history"

    # fields = [AuditLog.id, ...]  # TODO

    def can_create(self, request):
        return False

    def can_edit(self, request):
        return False

    def can_delete(self, request):
        return False
```

---

#### 文件 4：`app/admin/templates/dashboard.html`（新建）

```html
{% extends "layout.html" %}

{% block header %}
<div class="page-header">
    <div class="container-xl">
        <h2 class="page-title">仪表盘</h2>
    </div>
</div>
{% endblock %}

{% block content %}
<div class="page-body">
    <div class="container-xl">
        <div class="row row-cards">
            <div class="col-sm-6 col-lg-3">
                <div class="card card-sm">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <span class="bg-blue text-white avatar">
                                    <i class="fa fa-users"></i>
                                </span>
                            </div>
                            <div class="col">
                                <div class="font-weight-medium">{{ stats.user_count }}</div>
                                <div class="text-muted">用户数</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- 更多统计卡片... -->
        </div>
    </div>
</div>
{% endblock %}
```

---

#### 文件 5：`app/core/database.py`（修改）

在已有 async 引擎的基础上添加同步引擎。**标注修改位置**：

```python
# ============ 已有 async 引擎（保持不变） ============
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(settings.DATABASE_URL, ...)
async_session = async_sessionmaker(engine, class_=AsyncSession, ...)

# ============ 新增：starlette-admin 同步引擎 ============
# ⚠️ starlette-admin 需要同步数据库引擎，不能直接用 async 引擎
# 通过替换 dialect 驱动名来创建同步版本
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker as sync_sessionmaker

def get_sync_engine():
    """获取同步引擎，供 starlette-admin 使用。"""
    sync_url = settings.DATABASE_URL
    # 自动检测并转换异步驱动为同步驱动
    if "+aiomysql://" in sync_url:
        sync_url = sync_url.replace("+aiomysql://", "+pymysql://")
    elif "+asyncpg://" in sync_url:
        sync_url = sync_url.replace("+asyncpg://", "postgresql://")
    elif "+aiosqlite://" in sync_url:
        sync_url = sync_url.replace("+aiosqlite://", "")

    return create_engine(sync_url, pool_size=5, max_overflow=10, pool_recycle=1800)
# ============ 新增结束 ============
```

**⚠️ 如果是纯同步项目**，直接用同一引擎，不需要 `get_sync_engine()`。

---

#### 文件 6：`app/main.py`（修改）

**SessionMiddleware 必须在 create_admin 之前添加，且加在 FastAPI app 上（不是 admin.middlewares）。**

```python
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware  # 新增

from app.core.config import settings
from app.api.xxx import router as xxx_router
from app.admin import create_admin  # 新增

app = FastAPI(title="your-app", debug=True)

# ============ 新增：Session 中间件（必须在 create_admin 之前） ============
# ⚠️ starlette-admin 的登录系统依赖 session，没有它会导致无限重定向
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,  # 复用 JWT secret 或单独配置
    session_cookie="admin_session",
    max_age=3600,  # 1 小时
)
# ============ 新增结束 ============

# 路由注册
app.include_router(xxx_router)

# ============ 新增：挂载管理面板 ============
# ⚠️ 必须在路由注册之后、app 运行之前调用
admin = create_admin(app)
# ============ 新增结束 ============
```

---

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

## 认证扩展

默认模板使用 session + 账号密码认证。如需 JWT 认证：

1. 将 `AdminAuthProvider.login()` 改为调用你的 JWT 登录接口
2. 将 `is_authenticated()` 改为验证 Bearer token
3. 前端需要配置 CORS 允许 `/admin` 路径

## 语言切换

`I18nConfig(language_switcher=[...])` 会在顶部导航栏右侧（用户头像旁）显示语言下拉菜单。starlette-admin 内置支持的语言：

| 代码 | 语言 |
|------|------|
| `en` | English |
| `de` | Deutsch |
| `fr` | Français |
| `pt` | Português |
| `ru` | Русский |
| `tr` | Türkçe |
| `zh_Hant` | 繁體中文 |

切换后通过 cookie（默认名 `language`）保存偏好，`LocaleMiddleware` 自动读取。

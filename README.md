# Django Startup Kit

在官方 `django-admin startproject` 基础上的**可组合增强模板**。

每个改动被拆成独立模块：有明确的文件边界、依赖声明和接入/移除步骤。你可以只拿其中一项（例如只要 Unfold Admin），也可以全部组合使用。

> **使用方式**：本仓库不是「克隆即运行」的完整项目，而是**变更清单 + 参考实现**。推荐流程：先用官方命令初始化项目，再按需复制对应模块的文件与配置。

---

## 设计原则：可组合

| 原则 | 说明 |
|------|------|
| **模块独立** | 每个能力对应一组文件；尽量不把无关逻辑耦在一起 |
| **配置分层** | `base.py` 放 Django 核心；各能力拆到独立 settings 文件，通过 `__init__.py` 按需 `import` |
| **依赖显式** | 每个模块在文档中列出 PyPI 包、Redis/OSS 等外部依赖，以及依赖的其他模块 |
| **可单独移除** | 每个模块附带「如何卸载」，避免「全有或全无」 |
| **约定优于魔法** | 基类、Mixin、Widget 用少量约定（如 `file_fields`）代替隐式行为 |

### 模块依赖关系

```
                    ┌─────────────┐
                    │  M0 工具链   │  uv / Docker / Tailwind
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │ M1 配置层  │    │ M2 异步    │    │ M3 静态资源│
   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
         │                │                │
         └────────┬───────┴────────┬───────┘
                  ▼                ▼
           ┌───────────┐    ┌───────────┐
           │ M4 Admin  │◄───│ M5 模型基类│
           └─────┬─────┘    └─────┬─────┘
                 │                │
     ┌───────────┼────────┬───────┴───────┐
     ▼           ▼        ▼               ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ M6 API  │ │ M7 Celery│ │M8 Constance│ │M9 Widget│
└─────────┘ └─────────┘ └─────────┘ └─────────┘
                 │
                 ▼
           ┌───────────┐
           │M10 文件/OSS│  依赖 M5；OSS 可选
           └───────────┘
```

实线依赖：后项通常需要前项。例如 `M10 asset` 继承 `M5 BaseModel`；`M4 Admin` 与 `M5 simple_history` 配合最佳，但 Admin 基类本身可单独使用。

---

## 目录结构

```
django-startup-kit/
├── pyproject.toml          # Python 依赖（uv）
├── uv.lock                 # 锁文件
├── package.json            # Tailwind CSS 构建
├── manage.py
├── project_name/           # 主项目包（使用时替换为实际项目名）
│   ├── settings/
│   │   ├── __init__.py     # 聚合各 settings 模块
│   │   ├── base.py         # Django 核心配置
│   │   ├── CONFIG.py       # 开发环境变量
│   │   ├── CONFIG.prod.py  # 生产环境变量
│   │   ├── celery.py
│   │   ├── constance.py
│   │   ├── rest_framework.py
│   │   ├── simplejwt.py
│   │   └── unfold.py
│   ├── models.py           # BaseModel
│   ├── admin.py            # Admin 基类 + 第三方 Admin 换肤
│   ├── apps.py             # AppConfig（侧栏中文名补丁）
│   ├── widgets.py          # MultipleSelectWidget
│   ├── storages.py         # OSS 存储后端
│   ├── api_urls.py         # DRF 路由
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py / wsgi.py
│   └── static/router/js/   # Widget 静态资源
├── asset/                  # 文件资源 Mixin 应用
├── templates/              # 全局模板
├── static/                 # 全局静态资源
├── deploy/                 # Docker 部署
│   ├── entrypoint.sh
│   ├── nginx/nginx.conf
│   └── sources.list
└── Dockerfile
```

---

## 快速开始（全量接入）

```bash
# 1. 初始化官方 Django 项目
uv init myproject && cd myproject
uv add django
uv run django-admin startproject myproject .

# 2. 将本模板中 project_name/、asset/、static/、templates/、deploy/ 等
#    复制进项目，并把 project_name 全局替换为你的项目名

# 3. 安装依赖
uv sync --extra dev

# 4. 编译 Admin 用 Tailwind CSS（修改 styles.srccss 时需要）
npm install && npm run build:css

# 5. 启动
uv run python manage.py migrate
uv run python manage.py runserver
```

按需接入时，跳过不需要的模块，并参照下文各节的「单独接入 / 移除」说明。

---

## 模块详解

以下每一节结构一致：**官方默认 → 本模板改动 → 涉及文件 → 依赖 → 单独接入 → 移除**。

---

### M0 · 工具链（uv / Docker / Tailwind）

**官方默认**

- 无内置包管理约定；`settings.py` 单文件；静态 CSS 无构建流程。
- 部署方式自行选择。

**本模板改动**

| 能力 | 说明 |
|------|------|
| **uv + hatchling** | `pyproject.toml` + `uv.lock` 管理 Python 依赖；Docker 内 `uv export` 安装 |
| **Tailwind v4** | Admin 自定义样式走 `static/css/styles.srccss` → `npm run build:css` → `styles.min.css` |
| **Docker** | Nginx 反代 + Daphne；入口脚本支持 migrate、superuser、Celery 子命令 |

**涉及文件**

- `pyproject.toml`、`uv.lock`
- `package.json`
- `Dockerfile`、`deploy/`

**依赖**

- 无其他模块依赖；M0 可独立使用。

**单独接入**

1. 复制 `pyproject.toml` 中需要的依赖条目（不必全拷）。
2. 运行 `uv lock && uv sync`。
3. 若用 Docker，复制 `Dockerfile` 与 `deploy/`。

**移除**

- 删 `uv.lock`，改回 pip/poetry 均可；删 `package.json` 则保留预编译的 `styles.min.css` 即可；删 `Dockerfile` 不影响本地开发。

---

### M1 · 配置分层与环境变量

**官方默认**

- 单个 `settings.py`，开发/生产配置混在一起。
- 环境变量需自行封装。

**本模板改动**

```
settings/
├── __init__.py      # from .base import *; from .CONFIG import *; ...
├── base.py          # INSTALLED_APPS、MIDDLEWARE、模板、静态文件、i18n
├── CONFIG.py        # 开发：SQLite、Redis cache、CORS、OSS 开关
├── CONFIG.prod.py   # 生产：PostgreSQL、DEBUG 来自 env
├── celery.py        # Celery 路由与时区
├── constance.py     # 运行时动态配置
├── rest_framework.py
├── simplejwt.py
└── unfold.py        # Admin UI 配置
```

`get_env()` 支持两种读取方式：

```python
# 直接读环境变量
DATABASE_URL=postgres://...

# 从文件读（Docker/K8s Secret 常用）
POSTGRES_PASSWORD_FILE=/run/secrets/db_password
```

**涉及文件**

- `project_name/settings/` 整个目录

**依赖**

- 无；这是其他模块的挂载点。

**单独接入**

1. 将 `settings.py` 改为 `settings/` 包。
2. 先只复制 `base.py` + `CONFIG.py`，在 `__init__.py` 中按需追加其他文件的 `import`。
3. 设置 `DJANGO_SETTINGS_MODULE=yourproject.settings`。

**移除某个子配置**

- 从 `__init__.py` 删除对应 `from .xxx import *` 即可，例如不用 Celery 则去掉 `from .celery import *`。

**`CONFIG.py` vs `CONFIG.prod.py`**

| 配置项 | 开发 (CONFIG.py) | 生产 (CONFIG.prod.py) |
|--------|------------------|------------------------|
| 数据库 | SQLite | PostgreSQL（需 env 齐全） |
| Celery Result | django-db | Redis（可 env 覆盖） |
| DEBUG | 固定 True | 由 `DEBUG` env 控制 |

Docker 构建时会执行 `mv CONFIG.prod.py CONFIG.py`。

---

### M2 · ASGI 异步支持

**官方默认**

- 生成 `asgi.py` / `wsgi.py`，但 `runserver` 默认走 WSGI。
- 无异步视图生态预置。

**本模板改动**

| 改动 | 位置 |
|------|------|
| `daphne` 置于 `INSTALLED_APPS` 首位 | `base.py` |
| `ASGI_APPLICATION` 显式配置 | `base.py` |
| `adrf` 加入 INSTALLED_APPS | `base.py`（配合 M6 API 异步视图） |

启用后 `runserver` 以 ASGI 模式运行，可编写 `async def` 视图。

**涉及文件**

- `project_name/settings/base.py`
- `project_name/asgi.py`

**依赖**

- PyPI：`daphne`；若用异步 DRF 视图，另需 `adrf`。

**单独接入**

```python
# settings.py
INSTALLED_APPS = ["daphne", ...]  # 必须在最前
ASGI_APPLICATION = "myproject.asgi.application"
```

**移除**

- 从 `INSTALLED_APPS` 去掉 `daphne`、`adrf`；保留 `wsgi.py` 即可回到纯 WSGI。

---

### M3 · Admin 静态资源

**官方默认**

- Admin 样式由 Django 内置提供，无自定义 CSS/JS 管线。
- 无 jQuery、Flatpickr 等第三方前端库。

**本模板改动**

`static/` 目录包含 Admin 增强所需的完整静态文件：

```
static/
├── css/
│   ├── styles.srccss      # Tailwind 源文件（需编译）
│   ├── styles.min.css     # 编译产物（可直接使用）
│   └── flatpickr.min.css
├── js/
│   ├── script.js          # 全局通知、click_to_copy 等
│   ├── flatpickr.js
│   └── flatpickr.zh.js
├── jquery/
│   └── jquery-3.7.1.min.js
├── jquery-ui/             # 含 images/
├── favicon.svg
└── sample/
    └── login-bg.jpg       # Unfold 登录页背景
```

`project_name/static/router/js/multiple_select_widget.js` 属于 M9 Widget，与 Unfold 样式配合。

**涉及文件**

- `static/` 全部
- `package.json`（仅修改 CSS 时需要）

**依赖**

- 与 M4 Unfold 配合最佳，但静态文件本身可被任意 Admin 主题引用。

**单独接入**

1. 复制 `static/` 到项目根。
2. 确认 `STATICFILES_DIRS = [BASE_DIR / "static"]`。
3. 修改 CSS 时：`npm install && npm run build:css`。

**移除**

- 删 `static/` 中不需要的子目录；若不用 Unfold，可只保留业务所需的 JS/CSS。

---

### M4 · Unfold Admin 增强

**官方默认**

- 使用 Django 内置 Admin 主题。
- 第三方 Admin（Celery Beat、Constance 等）各自为政，风格不统一。

**本模板改动**

**4a. Unfold UI**

- `unfold` 及 contrib 插件置于 `django.contrib.admin` 之前。
- `unfold.py` 配置站点标题、侧边栏导航、主题色、登录页、注入 CSS/JS。

**4b. Admin 基类**

```python
# project_name/admin.py
class BaseModelAdmin(SimpleHistoryAdmin, ModelAdmin): ...
class BaseTabularInline(UnfoldTabularInline): ...
class BaseStackedInline(UnfoldStackedInline): ...
```

内置行为：

- 集成 SimpleHistory 历史记录页
- 「保存并继续编辑」改为「保存并添加另一个」
- `not_change_related_fields`：禁止 inline 中增删改关联对象
- `override_field_name`：自定义字段标签

**4c. 第三方 Admin 换肤**

统一将以下模型重新注册为 Unfold 风格：

- User / Group
- Constance Config
- Celery Beat（PeriodicTask、CrontabSchedule 等）

**4d. 侧栏中文名**

`apps.py` 在 `ready()` 中 patch 第三方模型的 `verbose_name`，与 Unfold 侧栏文案对齐。

**涉及文件**

- `project_name/settings/base.py`（INSTALLED_APPS）
- `project_name/settings/unfold.py`
- `project_name/admin.py`
- `project_name/apps.py`

**依赖**

- PyPI：`django-unfold`
- 推荐配合：M3 静态资源、M5 SimpleHistory、M8 Constance、M7 Celery
- SimpleHistory 是 `BaseModelAdmin` 的基类之一；若不要历史记录，可改为只继承 `ModelAdmin`

**单独接入**

1. `uv add django-unfold`
2. 按 `base.py` 顺序加入 `unfold` 相关 app。
3. 复制 `unfold.py`、`admin.py`（可删减 Celery/Constance 部分）。
4. 复制 M3 静态资源并在 `unfold.py` 的 `STYLES`/`SCRIPTS` 中引用。

**移除**

- 从 `INSTALLED_APPS` 去掉 `unfold*`；业务 Admin 改回 `django.contrib.admin.ModelAdmin`。
- 删 `unfold.py`；`admin.py` 中只保留业务相关注册。

---

### M5 · 模型基类（BaseModel）

**官方默认**

- 模型各自定义主键，通常用 Django 默认的 `BigAutoField`。
- 无统一时间戳、无变更历史。

**本模板改动**

```python
class BaseModel(models.Model):
    uuid = ShortUUIDField(primary_key=True, ...)  # 16 位 ShortUUID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(inherit=True)      # django-simple-history
```

**涉及文件**

- `project_name/models.py`
- `project_name/settings/base.py`（`simple_history` app + middleware）

**依赖**

- PyPI：`shortuuid`、`django-simple-history`
- 被 M10 asset 模块继承

**单独接入**

1. 复制 `models.py`。
2. 加入 `simple_history` 到 `INSTALLED_APPS` 和 `HistoryRequestMiddleware`。
3. 业务模型 `class Foo(BaseModel): ...`。

**移除**

- 业务模型改回普通 `models.Model`；去掉 `history` 字段和 simple_history 配置。
- 若只想保留 UUID 主键而不要历史，删掉 `history = HistoricalRecords(...)` 即可。

**与官方 `DEFAULT_AUTO_FIELD` 的关系**

- `BaseModel` 子类用 `uuid` 作主键，不受 `DEFAULT_AUTO_FIELD = BigAutoField` 影响。
- 未继承 `BaseModel` 的模型仍走 BigAutoField。

---

### M6 · REST API（DRF + JWT）

**官方默认**

- 无 API 框架；需自行集成 DRF、认证、路由。

**本模板改动**

**路由分离**

```python
# urls.py
path('api/v1/', include(api_urlpatterns)),

# api_urls.py — 使用 nested router，便于资源嵌套
router = routers.DefaultRouter()
# router.register(r'examples', ExampleViewSet)
```

**DRF 默认策略**（`rest_framework.py`）

| 配置 | 值 |
|------|-----|
| 认证 | Token + JWT + Session |
| 权限 | `IsAuthenticated` |
| 过滤 | django-filter + Search + Ordering |

**JWT**（`simplejwt.py`）

- Access 1 天 / Refresh 7 天
- 开启 rotation + blacklist

**涉及文件**

- `project_name/api_urls.py`
- `project_name/urls.py`
- `project_name/settings/rest_framework.py`
- `project_name/settings/simplejwt.py`
- `project_name/settings/base.py`（INSTALLED_APPS、CORS middleware）

**依赖**

- PyPI：`djangorestframework`、`djangorestframework-simplejwt`、`django-filter`、`django-cors-headers`、`drf-nested-routers`
- 可选：`adrf`（M2 异步视图）
- 可选：`django-cors-headers` 配置在 M1 `CONFIG.py`

**单独接入**

1. 安装上述 PyPI 包。
2. 复制 `rest_framework.py`、`simplejwt.py`，在 `__init__.py` 中 import。
3. 复制 `api_urls.py`，在 `urls.py` 挂载。
4. 按需配置 CORS（`CONFIG.py`）。

**移除**

- 删 `api_urls.py` 及 `urls.py` 中的 `api/v1/` 路由。
- 从 `INSTALLED_APPS` 去掉 `rest_framework*`、`django_filters`、`corsheaders`。
- 删 `rest_framework.py`、`simplejwt.py`。

---

### M7 · Celery 异步任务

**官方默认**

- 无任务队列；定时任务需自行选型。

**本模板改动**

| 能力 | 说明 |
|------|------|
| Broker | Redis（`CELERY_BROKER_URL`） |
| Result | 默认 `django-db`（`django_celery_results`） |
| Beat | 数据库调度器（`django_celery_beat`） |
| Admin | Celery Beat 模型已 Unfold 换肤（见 M4） |
| Docker | `entrypoint.sh celery worker/beat/flower` |

```python
# project_name/celery.py + __init__.py
from .celery import app as celery_app
```

**涉及文件**

- `project_name/celery.py`
- `project_name/__init__.py`
- `project_name/settings/celery.py`
- `project_name/settings/CONFIG.py`（`CELERY_BROKER_URL`）
- `project_name/admin.py`（Beat Admin 部分）
- `deploy/entrypoint.sh`

**依赖**

- PyPI：`celery[redis]`、`django-celery-beat`、`django-celery-results`、`flower`
- 外部：Redis
- 推荐配合 M4（Beat Admin 换肤）

**单独接入**

1. 安装 PyPI 包，配置 Redis URL。
2. 复制 `celery.py`、`settings/celery.py`。
3. `migrate` 创建 beat/results 表。
4. 启动：`celery -A project_name worker` / `beat`。

**移除**

- 删 celery 相关文件；从 `INSTALLED_APPS` 去掉三个 celery app。
- 从 `__init__.py` 去掉 `celery_app` 导出。
- `admin.py` 中删 Beat 注册代码。

---

### M8 · Constance 运行时配置

**官方默认**

- 配置变更需改代码或环境变量并重启。

**本模板改动**

- 数据库存储（`constance.backends.database`）。
- Admin 中可视化编辑；Unfold 换肤 + 侧边栏入口。
- `constance.py` 预留 `CONSTANCE_CONFIG` 扩展点。

**涉及文件**

- `project_name/settings/constance.py`
- `project_name/settings/base.py`
- `project_name/admin.py`（Constance Admin 部分）

**依赖**

- PyPI：`django-constance[redis]`
- 推荐配合 M4 Unfold

**单独接入**

1. `uv add "django-constance[redis]"`
2. 复制 `constance.py`，加入 `INSTALLED_APPS`。
3. 在 `CONSTANCE_CONFIG` 中添加键值。

**移除**

- 从 `INSTALLED_APPS` 去掉 `constance`；删 `constance.py` 和 Admin 注册。

---

### M9 · MultipleSelectWidget（JSON 多选）

**官方默认**

- JSONField 在 Admin 中显示为原始文本框。

**本模板改动**

- `MultipleSelectWidget`：Admin 中点击标签多选，底层存 JSON 数组。
- 支持选项校验、`min_selected` 下限、只读模式。
- 模板 + JS 分离，样式与 Unfold/Tailwind 一致。

**涉及文件**

- `project_name/widgets.py`
- `templates/router/widgets/multiple_select_widget.html`
- `project_name/static/router/js/multiple_select_widget.js`

**依赖**

- 无 PyPI 额外依赖
- 样式依赖 M3（Tailwind CSS）

**单独接入**

1. 复制上述三个文件。
2. 在 Admin 或 Form 中使用：

```python
from project_name.widgets import MultipleSelectWidget

class MyForm(forms.ModelForm):
    class Meta:
        widgets = {
            'tags': MultipleSelectWidget(choices=[('a', 'A'), ('b', 'B')], min_selected=1),
        }
```

**移除**

- 删三个文件；Form 改回默认 Widget。

---

### M10 · 文件资源（asset + OSS）

**官方默认**

- `FileField` / `ImageField` 存本地 `MEDIA_ROOT`。
- 无统一的公共 URL 生成、无对象存储抽象。

**本模板改动**

**10a. S3FileMixin**

```python
class Image(S3FileMixin):
    file_fields = ['image']
    image = models.ImageField(upload_to='images/')

# 自动生成 image_public_url
# OSS 开启 → CDN 域名；否则 → FileField.url
# save/delete 时自动清理旧文件
```

**10b. OSS 存储**

- `storages.py`：`MyOssMediaStorage`（阿里云 OSS，含 Django 4+ 兼容补丁）。
- `CONFIG.py` 中设置 `OSS_BUCKET_NAME` 等 env 即自动切换，**不设则走本地存储**。

**涉及文件**

- `asset/models.py`（及 `asset/` app 骨架）
- `project_name/storages.py`
- `project_name/settings/CONFIG.py`（OSS 段）

**依赖**

- PyPI：`django-oss-storage`（仅 OSS 时需要）
- 模块：M5 BaseModel（`S3FileMixin` 继承它）
- 外部：阿里云 OSS（可选）

**单独接入**

1. 复制 `asset/` app 和 `storages.py`。
2. 本地模式：无需 OSS env，正常使用 `FileField`。
3. OSS 模式：设置 `OSS_BUCKET_NAME`、`OSS_ENDPOINT`、`OSS_CDN_DOMAIN` 等。

**移除**

- 删 `asset` app；业务模型直接用 `FileField`。
- 删 `storages.py` 和 CONFIG 中 OSS 段。

---

### M11 · 系统日志（system）

**官方默认**

- 无结构化业务日志落库；通常只用 Python logging。

**本模板改动**

- `system.models.Log`：独立事务写入（`system.log.Log` 门面），按模块/级别检索。
- Admin 列表优化（InfinitePaginator、content 延迟加载）。

**涉及文件**

- `system/models.py`、`system/log.py`、`system/admin.py`

**依赖**

- 模块：M5 BaseModel
- 被 M12/M14 支付链路用于错误追踪

**单独接入**

1. 复制 `system/` app，加入 `INSTALLED_APPS`。
2. `migrate` 后可在任意代码中 `Log.error("标题", "内容", LogModel.Module.ORDER)`。

**移除**

- 从 `INSTALLED_APPS` 去掉 `system`；支付模块需改 `wechat/api.py` 等处 logging 策略。

---

### M12 · 订单与支付抽象（order）

**官方默认**

- 无统一订单/支付平台抽象。

**本模板改动**

- `Order` / `OrderItem` / `Refund` 状态机。
- `PaymentPlatformOrder` 抽象类；`Order.platform_order` 懒加载微信实现。
- DRF `OrderViewSet`：`wechat_prepay`、`check_payment`。
- Celery `auto_close_expired_orders`（超时关单，依赖 M7 Beat）。

**涉及文件**

- `order/models.py`、`order/views.py`、`order/serializers.py`、`order/tasks.py`、`order/admin.py`

**依赖**

- M5 BaseModel、M6 DRF、M7 Celery Beat、M11 system
- M14 wechat 提供具体 `WechatOrder`

**API 端点**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/orders/` | 创建订单 |
| POST | `/api/v1/orders/{uuid}/pay/wechat/prepay/` | 微信预下单 |
| POST | `/api/v1/orders/{uuid}/check_payment/` | 主动查单 |

**移除**

- 删 `order/` app；同时需移除 M14 或改写 `platform_order` 钩子。

---

### M13 · 微信用户（account · WeixinUser）

**官方默认**

- 无 OpenID 绑定模型。

**本模板改动**

- `WeixinUser`：存 `openid`，JSAPI 预下单时从 `request.user` 读取。

**涉及文件**

- `account/models.py`、`account/admin.py`

**依赖**

- M5 BaseModel
- M12/M14 JSAPI 场景必需；Native 支付可不启用

**移除**

- 删 `account` app；JSAPI 预下单需自行提供 openid 来源。

---

### M14 · 微信支付 V3（wechat）

**官方默认**

- 无微信支付集成。

**本模板改动**（与 `free3dkit-backend` 对齐）

| 能力 | 实现 |
|------|------|
| JSAPI / Native 预下单 | `WechatOrder.create_prepay()` |
| 支付回调 | `POST /api/v1/payments/wechat/pay/notify/` |
| 退款 API | `WechatAPI.create_refund()` |
| 退款回调 | `POST /api/v1/payments/wechat/refund/notify/`（验签解密，业务流待扩展） |
| 主动查单 / 关单 | `query_and_sync_pay_result()` / `close_pay_transaction()` |
| Admin | 查单、重新预下单、Native 二维码 JS |

**涉及文件**

- `wechat/models.py`、`wechat/api.py`、`wechat/views.py`、`wechat/urls.py`、`wechat/admin.py`
- `wechat/static/wechat/js/wechatorder_change_native_qr.js`
- `docs/payment_wechat.md`

**Constance 配置**（M8）

- `WECHAT_PAY_*` 全套密钥与回调 URL；详见 `settings/constance.py`。

**依赖**

- PyPI：`cryptography`、`requests`
- 模块：M5、M8、M11、M12；JSAPI 另需 M13
- 外部：微信商户平台 APIv3

**单独接入**

1. 复制 `wechat/` + 依赖的 M11/M12（及可选 M13）。
2. `api_urls.py` 加 `path('payments/wechat/', include('wechat.urls'))`。
3. 在 Constance 填写商户号、证书、V3 密钥。
4. 配置 `BASE_URL` 供回调 URL 自动拼接。

**移除**

- 删 `wechat` app 及 `api_urls` 中 payments 路由；`order.models.platform_order` 改回 `None`。

---

## 组合示例

### 只要现代化 Admin

```
M0 (uv) + M1 (配置) + M3 (静态) + M4 (Unfold)
```

不需要 API、Celery、BaseModel。

### API 项目，不要 Admin 增强

```
M0 + M1 + M2 (ASGI) + M6 (DRF/JWT)
```

去掉 M3/M4/M9；`INSTALLED_APPS` 中可移除 `unfold*`。

### 微信支付全栈

```
M0 + M1 + M4 + M5 + M6 + M7 + M8 + M11 + M12 + M14
```

JSAPI 另加 M13（WeixinUser）。

### 全栈后台 + 任务队列 + 支付

```
M0 ~ M14 全部
```

与当前模板默认一致。

### 在已有 Django 项目里加一个能力

以 Celery 为例：

1. `uv add celery[redis] django-celery-beat django-celery-results`
2. 复制 `celery.py`、`settings/celery.py`
3. `__init__.py` 加 `from .celery import app as celery_app`
4. `CONFIG.py` 加 `CELERY_BROKER_URL`
5. 若需 Admin 管理定时任务，额外复制 `admin.py` 中 Beat 部分（M4）

---

## 与官方 Django 差异总览

| 维度 | 官方 `startproject` | 本模板 |
|------|---------------------|--------|
| 包管理 | 无 | uv + hatchling |
| Settings | 单文件 `settings.py` | 分层目录 + env 文件 |
| 主键 | BigAutoField | ShortUUID（BaseModel） |
| 变更历史 | 无 | django-simple-history |
| Admin UI | Django 默认 | django-unfold + 基类 |
| API | 无 | DRF + JWT + nested router |
| 任务队列 | 无 | Celery + Beat + Results |
| 动态配置 | 无 | django-constance |
| 异步 | WSGI 为主 | ASGI（Daphne）+ adrf |
| 文件存储 | 本地 MEDIA | 本地 / 阿里云 OSS 可切换 |
| 静态资源 | 无自定义 | jQuery、Flatpickr、Tailwind |
| 国际化 | `en-us` | `zh-hans` + `Asia/Shanghai` |
| 部署 | 无 | Docker（Nginx + Daphne） |
| 微信支付 | 无 | 微信 APIv3（JSAPI/Native/退款 API） |
| 订单 | 无 | Order + PaymentPlatformOrder 抽象 |
| 业务日志 | 无 | system.Log 独立事务落库 |

---

## 本地开发

```bash
uv sync --extra dev
npm install              # 仅修改 Tailwind 时需要
npm run build:css
uv run python manage.py migrate
uv run python manage.py runserver
```

## Docker 部署

```bash
docker build -t django-startup-kit .
docker run -p 80:80 django-startup-kit

# Celery（另起容器）
docker run ... /app/deploy/entrypoint.sh celery worker
docker run ... /app/deploy/entrypoint.sh celery beat
docker run ... /app/deploy/entrypoint.sh celery flower
```

---

## 注意事项

1. **项目重命名**：使用前将 `project_name` 全局替换为实际项目名（包名、settings 路径、celery app 名等）。
2. **SECRET_KEY**：生产环境必须更换 `settings/base.py` 中的默认值。
3. **数据库**：开发默认 SQLite；生产通过 `CONFIG.prod.py` + 环境变量切 PostgreSQL。
4. **collectstatic**：生产部署前执行 `python manage.py collectstatic`（Docker 构建已包含）。
5. **模块可选**：不必全量接入；按上表逐项选用，并执行对应「移除」步骤清理不需要的依赖。

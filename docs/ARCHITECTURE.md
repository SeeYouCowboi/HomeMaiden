# HomeCentralMaid 架构文档

> **版本**: 2.0.0
> **最后更新**: 2026-01-16
> **面向读者**: 新接手的开发人员、维护者、贡献者

## 目录

1. [系统概述](#系统概述)
2. [核心架构](#核心架构)
3. [数据流](#数据流)
4. [核心组件详解](#核心组件详解)
5. [插件系统](#插件系统)
6. [提供者抽象层](#提供者抽象层)
7. [数据库设计](#数据库设计)
8. [配置系统](#配置系统)
9. [开发新功能](#开发新功能)
10. [常见问题](#常见问题)

---

## 系统概述

### 什么是 HomeCentralMaid？

HomeCentralMaid (代号: Catnip) 是一个**基于邮件和LLM的智能家庭管理系统**。用户通过发送自然语言邮件来控制家庭设备和服务，系统会：

1. **接收邮件** - 通过 IMAP 协议监听邮箱
2. **理解指令** - 使用 LLM（本地 Ollama）将自然语言转为结构化命令
3. **执行任务** - 通过插件系统调用对应的服务（如 Radarr 下载电影）
4. **反馈结果** - 通过 SMTP 发送执行结果邮件

### 设计理念

- **插件化架构** - 核心系统与具体功能解耦，易于扩展
- **提供者抽象** - 邮件和 LLM 服务可以轻松替换（IMAP/Gmail API, Ollama/OpenAI）
- **配置驱动** - 所有设置都通过 YAML 配置文件管理
- **完整审计** - 所有命令都记录到数据库，可追溯
- **零侵入部署** - 只需要一个邮箱账号，无需修改现有系统

---

## 核心架构

### 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户层                               │
│                     (发送邮件指令)                            │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    应用入口 (main.py)                         │
│                  - 初始化所有组件                             │
│                  - 主事件循环                                 │
│                  - 优雅关闭处理                               │
└──┬────────────────────────┬─────────────────────────────┬───┘
   │                        │                             │
┌──▼───────────┐   ┌────────▼──────────┐   ┌─────────────▼─────┐
│  邮件提供者   │   │  命令调度器        │   │  数据库层          │
│ (EmailProvider)│  │(CommandDispatcher) │   │  (Database)       │
│               │   │                    │   │                   │
│ - 接收邮件    │   │ - LLM 解析指令     │   │ - 命令历史         │
│ - 发送回复    │   │ - 路由到插件       │   │ - 任务队列         │
│ - 标记已读    │   │ - 收集执行结果     │   │ - 用户偏好         │
└───────────────┘   └──────┬─────────────┘   └───────────────────┘
                           │
                  ┌────────▼──────────┐
                  │  LLM 提供者        │
                  │ (LLMProvider)      │
                  │                    │
                  │ - 自然语言理解      │
                  │ - 结构化输出        │
                  └────────────────────┘
                           │
                  ┌────────▼──────────┐
                  │  插件注册表        │
                  │ (PluginRegistry)   │
                  │                    │
                  │ - 管理插件生命周期  │
                  │ - 命令→插件映射     │
                  │ - 健康检查          │
                  └──────┬─────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐    ┌─────▼──────┐   ┌────▼────────┐
   │ Plugin1 │    │  Plugin2   │   │  Plugin N   │
   │ (电影下载)│   │  (智能家居) │   │  (Git管理)  │
   └─────────┘    └────────────┘   └─────────────┘
```

### 目录结构说明

```
HomeCentralMaid/
│
├── main.py                    # 应用入口，主事件循环
│
├── core/                      # 核心框架代码
│   ├── config_manager.py      # 配置加载与管理
│   ├── logger.py              # 日志系统配置
│   ├── database.py            # SQLite 数据库封装
│   ├── plugin_base.py         # 插件基类和接口定义
│   ├── plugin_registry.py     # 插件注册与管理
│   ├── command_dispatcher.py  # 命令调度与路由
│   │
│   └── providers/             # 提供者抽象层
│       ├── email_provider.py       # 邮件提供者抽象基类
│       ├── imap_smtp_provider.py   # IMAP/SMTP 实现
│       ├── llm_provider.py         # LLM 提供者抽象基类
│       └── ollama_provider.py      # Ollama 本地 LLM 实现
│
├── plugins/                   # 插件目录
│   └── movie_download/        # 电影下载插件
│       ├── plugin.py          # 插件主类
│       └── radarr_client.py   # Radarr API 客户端
│
├── config/                    # 配置文件
│   ├── base.yaml              # 基础配置（默认值）
│   ├── development.yaml       # 开发环境配置
│   └── secrets.yaml           # 敏感信息（不提交到 Git）
│
├── data/                      # 运行时数据
│   └── catnip.db              # SQLite 数据库
│
├── logs/                      # 日志文件
│   └── homecentralmaid_YYYYMMDD.log
│
├── docs/                      # 文档
│   └── ARCHITECTURE.md        # 本文档
│
├── test_init.py               # 初始化测试脚本
├── test_components.py         # 组件测试脚本
├── requirements.txt           # Python 依赖
└── README.md                  # 项目 README
```

---

## 数据流

### 完整的命令执行流程

```
1. 用户发送邮件
   └─> teacatjazz@gmail.com 发送: "帮我下载电影《星际穿越》"

2. IMAPSMTPProvider 接收邮件
   └─> 连接 IMAP 服务器
   └─> 获取未读邮件 (UNSEEN flag)
   └─> 检查发件人白名单
   └─> 返回 EmailMessage 对象

3. CommandDispatcher 处理邮件
   └─> 提取邮件 body: "帮我下载电影《星际穿越》"
   └─> 调用 LLMProvider.parse_command()

4. OllamaProvider 解析自然语言
   └─> 构造系统提示词（system prompt）
   └─> 调用本地 Ollama 模型（qwen3:8b）
   └─> 解析 JSON 输出: [{"action": "download_movie", "title": "星际穿越"}]
   └─> 返回 LLMResponse

5. CommandDispatcher 路由命令
   └─> 根据 action="download_movie" 查找插件
   └─> 从 PluginRegistry 获取 MovieDownloadPlugin
   └─> 检查插件健康状态（health_check）
   └─> 构造 CommandContext

6. MovieDownloadPlugin 执行
   └─> 提取 title="星际穿越"
   └─> 调用 RadarrClient.search_movie("星际穿越")
   └─> Radarr 通过 TMDb 搜索电影
   └─> 获取搜索结果（包含 tmdbId, year 等）
   └─> 检查是否已在队列（避免重复）
   └─> 调用 RadarrClient.add_movie()
   └─> 返回 PluginResult

7. CommandDispatcher 收集结果
   └─> 记录到数据库（Database.log_command）
   └─> 返回 List[PluginResult]

8. main.py 发送回复邮件
   └─> 构造回复内容（成功/失败）
   └─> 调用 IMAPSMTPProvider.send_message()
   └─> 标记原邮件为已读

9. 用户收到回复
   └─> "主人好喵~ 电影《星际穿越》(2014) 已添加到下载队列喵~"
```

### 错误处理流程

每个层级都有错误处理机制：

```
[错误发生]
   │
   ├─> Plugin 层: 捕获异常，返回 PluginResult(success=False)
   │
   ├─> Dispatcher 层: 记录错误日志，返回失败结果
   │
   ├─> Database 层: 记录失败命令到 command_history
   │
   └─> main.py: 发送错误通知邮件给用户
```

---

## 核心组件详解

### 1. ConfigManager (配置管理器)

**文件**: `core/config_manager.py`

**职责**:
- 加载和合并多个 YAML 配置文件
- 支持环境变量替换 (`${ENV_VAR}`)
- 提供点号路径访问 (`config.get("email.smtp.server")`)

**加载顺序**:
```
1. base.yaml        (基础配置)
2. {env}.yaml       (环境配置，覆盖 base)
3. secrets.yaml     (密钥配置，覆盖所有)
```

**使用示例**:
```python
config = ConfigManager()
config.load(env="production")

# 获取配置
email_user = config.get("email.username")
plugin_cfg = config.get_plugin_config("movie_download")
```

**关键方法**:
- `load(env)` - 加载配置文件
- `get(key_path, default)` - 获取配置值
- `get_plugin_config(plugin_name)` - 获取插件配置
- `reload(env)` - 重新加载配置

---

### 2. Database (数据库层)

**文件**: `core/database.py`

**职责**:
- 管理 SQLite 连接
- 提供 CRUD 操作
- 维护四张核心表

**数据表结构**:

#### command_history (命令历史)
```sql
- id (主键)
- timestamp (时间戳)
- sender (发件人)
- subject (邮件主题)
- command_action (命令动作，如 download_movie)
- command_data (命令参数，JSON)
- plugin_name (执行的插件)
- success (是否成功)
- result_message (结果消息)
- result_data (结果数据，JSON)
- execution_time_ms (执行时间，毫秒)
```

#### task_queue (任务队列)
```sql
- id (主键)
- created_at, updated_at (创建/更新时间)
- task_type (任务类型)
- task_data (任务数据，JSON)
- status (pending/running/completed/failed)
- priority (优先级，数字越小优先级越高)
- retry_count, max_retries (重试次数)
- error_message (错误消息)
- scheduled_for (计划执行时间)
- completed_at (完成时间)
```

#### user_preferences (用户偏好)
```sql
- user_email (主键，用户邮箱)
- preferences (偏好设置，JSON)
- created_at, updated_at
```

#### plugin_state (插件状态)
```sql
- plugin_name (插件名)
- key (状态键)
- value (状态值，JSON)
- updated_at
- 复合主键: (plugin_name, key)
```

**使用示例**:
```python
# 记录命令
db.log_command(
    sender="user@example.com",
    subject="Download Movie",
    command_action="download_movie",
    command_data={"title": "Inception"},
    plugin_name="movie_download",
    success=True,
    result_message="Movie added",
    execution_time_ms=250
)

# 查询历史
history = db.get_command_history(limit=10, sender="user@example.com")

# 插件状态存储
db.set_plugin_state("movie_download", "last_movie", "Inception")
last_movie = db.get_plugin_state("movie_download", "last_movie")
```

---

### 3. PluginRegistry (插件注册表)

**文件**: `core/plugin_registry.py`

**职责**:
- 管理插件生命周期（注册、初始化、卸载）
- 维护命令到插件的映射
- 提供健康检查接口

**插件生命周期**:
```
UNLOADED → LOADED → INITIALIZED → FAILED
              ↓
           cleanup()
              ↓
           UNLOADED
```

**注册流程**:
```python
# 1. 实例化插件
plugin = MovieDownloadPlugin(config, logger)

# 2. 验证配置
if not plugin.validate_config():
    return False

# 3. 初始化资源
if not plugin.initialize():
    return False

# 4. 注册命令映射
for cmd in plugin.get_metadata().commands:
    command_map[cmd] = plugin_name

# 5. 标记为 INITIALIZED
plugin.status = PluginStatus.INITIALIZED
```

**使用示例**:
```python
registry = PluginRegistry(logger)

# 注册插件
registry.register(MovieDownloadPlugin, plugin_config)

# 获取插件
plugin = registry.get_plugin_for_command("download_movie")

# 健康检查
health = registry.health_check()  # {"movie_download": True}

# 卸载插件
registry.unload_plugin("movie_download")
```

---

### 4. CommandDispatcher (命令调度器)

**文件**: `core/command_dispatcher.py`

**职责**:
- 接收邮件数据
- 调用 LLM 解析自然语言
- 路由命令到对应插件
- 收集并返回执行结果

**核心工作流**:
```python
def process_email(email_data):
    # 1. LLM 解析
    llm_result = llm_provider.parse_command(email_data['body'])

    # 2. 检查解析成功
    if not llm_result.success:
        return [PluginResult(success=False, message=error)]

    # 3. 遍历命令
    results = []
    for cmd in llm_result.data:
        # 4. 查找插件
        plugin = registry.get_plugin_for_command(cmd['action'])

        # 5. 健康检查
        if not plugin.health_check():
            results.append(PluginResult(success=False, ...))
            continue

        # 6. 构造上下文
        context = CommandContext(
            sender=email_data['sender'],
            parsed_command=cmd,
            ...
        )

        # 7. 执行插件
        result = plugin.execute(context)
        results.append(result)

    return results
```

---

## 插件系统

### 插件架构

插件是系统扩展的核心机制。每个插件都是一个独立的模块，实现了 `BasePlugin` 接口。

### BasePlugin 接口

**文件**: `core/plugin_base.py`

**必须实现的方法**:

```python
class YourPlugin(BasePlugin):

    def get_metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        return PluginMetadata(
            name="your_plugin",
            version="1.0.0",
            author="Your Name",
            description="插件描述",
            commands=["command1", "command2"],  # 处理的命令
            config_schema={...}  # 配置模式
        )

    def initialize(self) -> bool:
        """初始化插件资源"""
        # 验证配置
        # 建立连接
        # 分配资源
        return True

    def execute(self, context: CommandContext) -> PluginResult:
        """执行命令"""
        action = context.parsed_command.get('action')

        if action == "command1":
            return self._handle_command1(context)

        # ...

    def cleanup(self):
        """清理资源"""
        # 关闭连接
        # 释放资源
        pass
```

### CommandContext (命令上下文)

插件执行时收到的上下文对象：

```python
@dataclass
class CommandContext:
    sender: str                    # 发件人邮箱
    subject: str                   # 邮件主题
    body: str                      # 邮件正文
    parsed_command: Dict[str, Any] # LLM 解析的结构化命令
    timestamp: datetime            # 时间戳
    config: Dict[str, Any]         # 插件配置
    logger: logging.Logger         # 日志器
```

### PluginResult (执行结果)

插件执行后返回的结果对象：

```python
class PluginResult:
    success: bool              # 是否成功
    message: str               # 结果消息（用户可读）
    data: Dict[str, Any]       # 结果数据
    timestamp: datetime        # 时间戳
```

### 开发新插件

**步骤 1**: 创建插件目录
```bash
mkdir -p plugins/your_plugin
```

**步骤 2**: 实现插件类

`plugins/your_plugin/plugin.py`:
```python
from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult

class YourPlugin(BasePlugin):

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="your_plugin",
            version="1.0.0",
            author="Your Name",
            description="你的插件描述",
            commands=["your_command"],
            config_schema={
                "api_key": {"type": "string", "required": True},
                "api_url": {"type": "string", "default": "http://localhost"}
            }
        )

    def initialize(self) -> bool:
        self.api_key = self.config.get('api_key')
        self.api_url = self.config.get('api_url')

        # 测试连接
        # ...

        return True

    def execute(self, context: CommandContext) -> PluginResult:
        command = context.parsed_command

        # 执行你的逻辑
        # ...

        return PluginResult(
            success=True,
            message="执行成功",
            data={"result": "..."}
        )

    def cleanup(self):
        pass
```

**步骤 3**: 配置插件

`config/base.yaml`:
```yaml
plugins:
  enabled:
    - "movie_download"
    - "your_plugin"      # 添加你的插件

  your_plugin:
    api_key: "${YOUR_API_KEY}"
    api_url: "http://localhost:8080"
```

**步骤 4**: 在 main.py 中注册

```python
# 在 HomeCentralMaid.initialize() 方法中
elif plugin_name == "your_plugin":
    from plugins.your_plugin.plugin import YourPlugin
    if self.plugin_registry.register(YourPlugin, plugin_config):
        registered_count += 1
```

**步骤 5**: 更新 LLM 提示词

`config/base.yaml`:
```yaml
llm:
  system_prompt: |
    你是 Catnip 女仆管家。
    将用户指令转为 JSON 数组：

    可用命令:
    - download_movie: {"action": "download_movie", "title": "电影名"}
    - your_command: {"action": "your_command", "param": "value"}

    只输出 JSON，不要解释。
```

---

## 提供者抽象层

### 为什么需要提供者抽象？

提供者抽象允许你替换底层实现而不影响核心逻辑。例如：
- 将 IMAP/SMTP 替换为 Gmail API
- 将 Ollama 替换为 OpenAI/Claude

### EmailProvider 接口

**文件**: `core/providers/email_provider.py`

```python
class EmailProvider(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """连接邮件服务"""

    @abstractmethod
    def get_unread_messages(self, limit: int) -> List[EmailMessage]:
        """获取未读邮件"""

    @abstractmethod
    def send_message(self, to: str, subject: str, body: str) -> bool:
        """发送邮件"""

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """标记为已读"""

    @abstractmethod
    def disconnect(self):
        """断开连接"""
```

### LLMProvider 接口

**文件**: `core/providers/llm_provider.py`

```python
class LLMProvider(ABC):
    @abstractmethod
    def parse_command(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        """解析自然语言为结构化命令"""

    @abstractmethod
    def test_connection(self) -> bool:
        """测试服务是否可用"""

    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
```

### 实现新的提供者

**示例：实现 Gmail API Provider**

`core/providers/gmail_api_provider.py`:
```python
from .email_provider import EmailProvider, EmailMessage

class GmailAPIProvider(EmailProvider):

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.service = None

    def connect(self) -> bool:
        # 使用 Google API 客户端
        # ...
        return True

    def get_unread_messages(self, limit: int) -> List[EmailMessage]:
        # 调用 Gmail API
        # ...
        return messages

    # 实现其他方法...
```

然后在配置和 main.py 中切换：

```yaml
email:
  provider: "gmail_api"  # 从 imap_smtp 改为 gmail_api
  # Gmail API 配置
```

---

## 配置系统

### 配置文件层级

```
base.yaml (基础配置)
    ↓ 被覆盖
development.yaml (开发环境)
    ↓ 被覆盖
secrets.yaml (密钥)
```

### 环境变量替换

配置中可以使用 `${ENV_VAR}` 引用环境变量：

```yaml
email:
  username: "${EMAIL_USER}"
  password: "${EMAIL_PASS}"
```

运行前设置环境变量：
```bash
export EMAIL_USER="your@email.com"
export EMAIL_PASS="your_password"
python main.py
```

### 配置最佳实践

1. **基础配置放 base.yaml**
   - 默认值
   - 结构定义
   - 不敏感的配置

2. **环境特定配置放 {env}.yaml**
   - 日志级别
   - 数据库路径
   - 轮询间隔

3. **密钥放 secrets.yaml**
   - API 密钥
   - 邮箱密码
   - 敏感URL
   - **永远不要提交到 Git！**

---

## 开发新功能

### 场景：添加一个智能家居控制插件

**需求**: 通过邮件控制 Home Assistant 的设备

#### 1. 设计命令格式

```json
[
  {"action": "turn_on_light", "entity_id": "light.living_room"},
  {"action": "set_temperature", "entity_id": "climate.bedroom", "temperature": 22}
]
```

#### 2. 创建插件

`plugins/home_assistant/plugin.py`:

```python
from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult
import requests

class HomeAssistantPlugin(BasePlugin):

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="home_assistant",
            version="1.0.0",
            author="Your Name",
            description="控制 Home Assistant 设备",
            commands=[
                "turn_on_light",
                "turn_off_light",
                "set_temperature"
            ],
            config_schema={
                "ha_url": {"type": "string", "required": True},
                "ha_token": {"type": "string", "required": True}
            }
        )

    def initialize(self) -> bool:
        self.ha_url = self.config['ha_url']
        self.ha_token = self.config['ha_token']
        self.headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json"
        }

        # 测试连接
        try:
            response = requests.get(
                f"{self.ha_url}/api/",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def execute(self, context: CommandContext) -> PluginResult:
        action = context.parsed_command.get('action')
        entity_id = context.parsed_command.get('entity_id')

        if not entity_id:
            return PluginResult(
                success=False,
                message="缺少设备 ID",
                data={}
            )

        if action == "turn_on_light":
            return self._turn_on(entity_id)
        elif action == "turn_off_light":
            return self._turn_off(entity_id)
        elif action == "set_temperature":
            temp = context.parsed_command.get('temperature')
            return self._set_temperature(entity_id, temp)

        return PluginResult(success=False, message="未知命令")

    def _turn_on(self, entity_id: str) -> PluginResult:
        try:
            response = requests.post(
                f"{self.ha_url}/api/services/homeassistant/turn_on",
                json={"entity_id": entity_id},
                headers=self.headers
            )

            if response.status_code == 200:
                return PluginResult(
                    success=True,
                    message=f"已打开 {entity_id}",
                    data={"entity_id": entity_id}
                )
            else:
                return PluginResult(
                    success=False,
                    message=f"操作失败: {response.status_code}"
                )
        except Exception as e:
            return PluginResult(
                success=False,
                message=f"错误: {str(e)}"
            )

    def _turn_off(self, entity_id: str) -> PluginResult:
        # 类似实现
        pass

    def _set_temperature(self, entity_id: str, temperature: float) -> PluginResult:
        # 类似实现
        pass

    def cleanup(self):
        pass
```

#### 3. 配置插件

`config/base.yaml`:
```yaml
plugins:
  enabled:
    - "movie_download"
    - "home_assistant"

  home_assistant:
    ha_url: "http://localhost:8123"
    ha_token: "${HA_TOKEN}"
```

`config/secrets.yaml`:
```yaml
plugins:
  home_assistant:
    ha_token: "eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### 4. 注册插件

`main.py` 的 `initialize()` 方法中：
```python
elif plugin_name == "home_assistant":
    from plugins.home_assistant.plugin import HomeAssistantPlugin
    if self.plugin_registry.register(HomeAssistantPlugin, plugin_config):
        registered_count += 1
```

#### 5. 更新 LLM 提示词

`config/base.yaml`:
```yaml
llm:
  system_prompt: |
    你是 Catnip 女仆管家。将用户指令转为 JSON 数组。

    支持的命令：
    - download_movie: {"action": "download_movie", "title": "电影名"}
    - turn_on_light: {"action": "turn_on_light", "entity_id": "light.xxx"}
    - turn_off_light: {"action": "turn_off_light", "entity_id": "light.xxx"}
    - set_temperature: {"action": "set_temperature", "entity_id": "climate.xxx", "temperature": 22}

    entity_id 是设备 ID，请从用户描述中推断。
    例如"客厅灯" → "light.living_room"

    只输出 JSON 数组，不要其他内容。
```

#### 6. 测试

发送邮件：
```
主题：控制灯光
内容：帮我打开客厅的灯
```

预期响应：
```
主人好喵~ (*^▽^*)

您的指令已经成功执行啦！

执行结果：
  ✓ 已打开 light.living_room

Catnip 会继续为您服务的喵~ 🐾
```

---

## 常见问题

### Q1: 如何调试 LLM 解析失败？

**A**: 查看日志文件 `logs/homecentralmaid_YYYYMMDD.log`

```bash
grep "LLM parsing" logs/homecentralmaid_20260116.log
```

LLM 的原始输出会记录在日志中。检查：
1. 是否输出了有效的 JSON？
2. JSON 格式是否正确？
3. action 字段是否存在？

可以在 `development.yaml` 中设置 `DEBUG` 级别查看更详细信息：

```yaml
system:
  log_level: "DEBUG"
```

### Q2: 如何添加新的邮件提供者（如 Gmail API）？

**A**:
1. 继承 `EmailProvider` 抽象类
2. 实现所有抽象方法
3. 在配置中指定 provider 类型
4. 在 main.py 中添加初始化逻辑

参考 `core/providers/imap_smtp_provider.py` 的实现。

### Q3: 插件之间如何共享数据？

**A**: 使用数据库的 `plugin_state` 表：

```python
# 插件 A 保存数据
db = self.context.database  # 如果你扩展了 CommandContext
db.set_plugin_state("pluginA", "shared_key", {"data": "value"})

# 插件 B 读取数据
data = db.get_plugin_state("pluginA", "shared_key")
```

### Q4: 如何实现定时任务？

**A**: 使用数据库的 `task_queue` 表：

```python
# 在插件中创建定时任务
db.enqueue_task(
    task_type="check_download",
    task_data={"movie_id": 123},
    scheduled_for=datetime.now() + timedelta(hours=1)
)
```

然后实现一个后台 worker 定期检查和执行任务（目前未实现，在 Roadmap 中）。

### Q5: 如何处理长时间运行的任务？

**A**: 当前版本在主循环中同步执行，可能阻塞邮件轮询。建议：

1. **短期方案**: 在插件中启动后台线程
2. **长期方案**: 实现任务队列 worker（v3.0 计划）

### Q6: 如何限制某个用户只能使用特定插件？

**A**: 在插件的 `execute()` 方法中检查 `context.sender`：

```python
def execute(self, context: CommandContext) -> PluginResult:
    allowed_users = self.config.get('allowed_users', [])

    if allowed_users and context.sender not in allowed_users:
        return PluginResult(
            success=False,
            message="您没有权限使用此功能"
        )

    # 正常执行
    ...
```

配置：
```yaml
plugins:
  your_plugin:
    allowed_users:
      - "admin@example.com"
      - "user@example.com"
```

### Q7: 数据库如何备份？

**A**: SQLite 数据库是单个文件，直接复制即可：

```bash
# 备份
cp data/catnip.db data/backups/catnip_20260116.db

# 恢复
cp data/backups/catnip_20260116.db data/catnip.db
```

建议使用 cron 定期备份：
```bash
# 每天凌晨 3 点备份
0 3 * * * cp /path/to/data/catnip.db /path/to/backups/catnip_$(date +\%Y\%m\%d).db
```

### Q8: 如何支持多个 LLM 模型？

**A**: Ollama 支持运行多个模型：

```bash
# 下载其他模型
ollama pull llama2
ollama pull mistral

# 配置中切换
llm:
  model: "llama2"  # 或 mistral
```

也可以在运行时通过 `OllamaProvider.set_model()` 切换。

### Q9: 邮件发送失败怎么办？

**A**: 检查以下几点：

1. **SMTP 配置正确？**
   ```yaml
   email:
     smtp_server: "smtp.qq.com"
     smtp_port: 587
   ```

2. **密码是授权码而不是登录密码？**
   - QQ 邮箱需要使用"授权码"
   - 在 QQ 邮箱设置 → 账户 → 开启 POP3/SMTP → 生成授权码

3. **防火墙阻止？**
   ```bash
   telnet smtp.qq.com 587
   ```

4. **查看日志**
   ```bash
   grep "send_message" logs/homecentralmaid_*.log
   ```

### Q10: 如何禁用某个插件？

**A**: 从配置中移除：

```yaml
plugins:
  enabled:
    - "movie_download"
    # - "home_assistant"  # 注释掉或删除这行
```

重启应用即可。

---

## 最佳实践

### 1. 日志记录

- 在所有关键操作处添加日志
- 使用合适的日志级别：
  - `DEBUG`: 详细调试信息
  - `INFO`: 一般信息
  - `WARNING`: 警告但不影响运行
  - `ERROR`: 错误但可恢复
  - `CRITICAL`: 严重错误，系统无法继续

```python
self.logger.debug(f"Parsed command: {parsed_command}")
self.logger.info(f"Adding movie: {title}")
self.logger.warning(f"Movie already exists: {title}")
self.logger.error(f"Failed to connect to Radarr: {e}")
```

### 2. 错误处理

- 所有外部调用（API、数据库、文件）都应该用 try-except 包裹
- 返回友好的错误消息给用户
- 记录详细的错误信息到日志

```python
try:
    result = external_api_call()
except TimeoutError:
    self.logger.error("API call timeout")
    return PluginResult(success=False, message="服务响应超时，请稍后重试")
except Exception as e:
    self.logger.error(f"Unexpected error: {e}", exc_info=True)
    return PluginResult(success=False, message="系统错误，请查看日志")
```

### 3. 配置验证

- 在 `initialize()` 中验证所有必需配置
- 提供清晰的错误提示

```python
def initialize(self) -> bool:
    required_keys = ["api_url", "api_key"]
    for key in required_keys:
        if key not in self.config:
            self.logger.error(f"Missing required config: {key}")
            return False

    # 验证 URL 格式
    if not self.config['api_url'].startswith('http'):
        self.logger.error("api_url must start with http:// or https://")
        return False

    return True
```

### 4. 测试

创建测试脚本验证插件功能：

```python
# test_your_plugin.py
from plugins.your_plugin.plugin import YourPlugin
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

config = {
    "api_url": "http://localhost:8080",
    "api_key": "test_key"
}

plugin = YourPlugin(config, logger)

if plugin.initialize():
    print("✓ Plugin initialized")

    # 测试健康检查
    if plugin.health_check():
        print("✓ Health check passed")

    # 测试命令执行
    # ...
else:
    print("✗ Plugin initialization failed")
```

### 5. 文档

为你的插件创建 README：

```markdown
# Your Plugin

## 功能
- 功能 1
- 功能 2

## 配置
\`\`\`yaml
plugins:
  your_plugin:
    api_url: "http://localhost:8080"
    api_key: "${YOUR_API_KEY}"
\`\`\`

## 命令
- `command1`: 描述
- `command2`: 描述

## 示例
...
```

---

## 未来规划

### v3.0 (计划中)

- [ ] **任务队列 Worker** - 后台处理长时间运行的任务
- [ ] **Web 管理界面** - 查看命令历史、管理插件、实时日志
- [ ] **更多 LLM 提供者** - OpenAI、Claude、Gemini
- [ ] **更多邮件提供者** - Gmail API、Outlook API
- [ ] **插件市场** - 社区贡献的插件
- [ ] **多用户支持** - 不同用户不同权限
- [ ] **通知系统** - Webhook、Telegram Bot、企业微信
- [ ] **规则引擎** - 基于条件的自动化（if-then-else）

---

## 贡献指南

欢迎贡献代码！请遵循以下流程：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add your feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8
- 添加类型提示
- 为所有公共方法添加文档字符串
- 编写单元测试（如果适用）

---

## 联系方式

- **问题反馈**: GitHub Issues
- **功能请求**: GitHub Discussions
- **邮件**: your@email.com

---

**最后更新**: 2026-01-16
**维护者**: HomeCentralMaid Team

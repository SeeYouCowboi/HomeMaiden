# HomeCentralMaid 快速入门指南

> 🚀 **5分钟快速理解整个项目**

## 核心概念

### 系统是如何工作的？

```
用户发邮件 → 系统收邮件 → LLM理解指令 → 插件执行任务 → 发邮件回复结果
```

**举个例子**：
```
1. 你发邮件："帮我下载电影《星际穿越》"
2. 系统收到邮件，用AI理解你的意图
3. AI输出：{"action": "download_movie", "title": "星际穿越"}
4. 电影下载插件执行，添加到Radarr下载队列
5. 系统回复邮件："电影《星际穿越》(2014) 已添加到下载队列喵~"
```

---

## 代码结构速览

### 最重要的3个文件

1. **`main.py`** - 程序入口
   - 初始化所有组件
   - 运行主事件循环（每30秒检查一次邮件）
   - 处理优雅关闭

2. **`core/command_dispatcher.py`** - 大脑
   - 用LLM解析邮件
   - 找到对应的插件
   - 执行并收集结果

3. **`core/plugin_registry.py`** - 插件管理器
   - 加载和管理所有插件
   - 维护"命令→插件"的映射表

### 目录速查

```
├── main.py                    # 从这里开始阅读！
│
├── core/                      # 核心框架，很稳定，一般不需要改
│   ├── config_manager.py      # 加载YAML配置
│   ├── database.py            # SQLite封装
│   ├── plugin_registry.py     # 插件管理（重要！）
│   ├── command_dispatcher.py  # 命令路由（重要！）
│   └── providers/             # 邮件和LLM的抽象层
│
├── plugins/                   # 插件目录，添加新功能就在这里
│   └── movie_download/        # 电影下载插件示例
│
├── config/                    # 配置文件
│   ├── base.yaml              # 基础配置
│   └── secrets.yaml           # 密钥配置（不要提交到Git！）
│
└── docs/                      # 文档
    ├── ARCHITECTURE.md        # 详细架构文档
    └── QUICKSTART.md          # 本文档
```

---

## 代码阅读路线

### 第一步：理解主流程（10分钟）

按顺序阅读这些文件：

1. **`main.py` (300行)**
   - 关注 `HomeCentralMaid.run()` 方法
   - 这是主事件循环，每30秒跑一次

2. **`core/command_dispatcher.py` (250行)**
   - 关注 `process_email()` 方法
   - 这是命令处理的核心流程

3. **`plugins/movie_download/plugin.py` (280行)**
   - 看一个完整的插件示例
   - 理解插件是如何工作的

### 第二步：理解核心组件（20分钟）

4. **`core/plugin_base.py` (170行)**
   - 插件的接口定义
   - 理解 `BasePlugin`、`CommandContext`、`PluginResult`

5. **`core/plugin_registry.py` (280行)**
   - 插件的注册和管理
   - 理解插件生命周期

6. **`core/config_manager.py` (220行)**
   - 配置系统的实现
   - 理解配置加载和合并

### 第三步：理解提供者抽象（10分钟）

7. **`core/providers/email_provider.py` (107行)**
8. **`core/providers/llm_provider.py` (79行)**
   - 理解抽象层的设计
   - 为什么要用抽象基类？

---

## 关键数据结构

### 1. EmailMessage（邮件消息）

```python
@dataclass
class EmailMessage:
    message_id: str       # "12345"
    sender: str           # "user@example.com"
    subject: str          # "下载电影"
    body: str             # "帮我下载《星际穿越》"
    timestamp: datetime
```

### 2. LLMResponse（LLM解析结果）

```python
@dataclass
class LLMResponse:
    success: bool         # True/False
    data: List[Dict]      # [{"action": "download_movie", "title": "Inception"}]
    error: str            # 错误信息
    raw: str              # LLM原始输出
```

### 3. CommandContext（命令上下文）

```python
@dataclass
class CommandContext:
    sender: str                    # 发件人
    parsed_command: Dict[str, Any] # {"action": "download_movie", "title": "..."}
    config: Dict[str, Any]         # 插件配置
    logger: logging.Logger         # 日志记录器
    # ... 还有其他字段
```

### 4. PluginResult（插件执行结果）

```python
class PluginResult:
    success: bool        # 是否成功
    message: str         # "电影《xxx》已添加到下载队列"
    data: Dict[str, Any] # {"movie_id": 123, "year": 2014}
```

---

## 代码走读：一次完整的命令执行

让我们跟踪一封邮件的完整处理流程：

### 1. 邮件到达（main.py:177-194）

```python
def run(self):
    while self.running:
        # 获取未读邮件
        messages = self.email_provider.get_unread_messages(limit=5)

        for msg in messages:
            # 处理邮件
            results = self.dispatcher.process_email({
                'sender': msg.sender,
                'subject': msg.subject,
                'body': msg.body
            })

            # 记录到数据库
            for result in results:
                self.database.log_command(...)

            # 发送回复
            self._send_response_email(msg, results)

            # 标记为已读
            self.email_provider.mark_as_read(msg.message_id)
```

### 2. LLM解析（command_dispatcher.py:70-74）

```python
def process_email(self, email_data: Dict[str, Any]) -> List[PluginResult]:
    # 调用LLM解析邮件正文
    llm_result = self.llm_provider.parse_command(body)

    # llm_result.data = [{"action": "download_movie", "title": "星际穿越"}]
```

### 3. 查找插件（command_dispatcher.py:144-146）

```python
def _execute_command(self, email_data, parsed_command):
    action = parsed_command.get('action')  # "download_movie"

    # 在注册表中查找处理这个命令的插件
    plugin = self.registry.get_plugin_for_command(action)
    # plugin = MovieDownloadPlugin实例
```

### 4. 构造上下文（command_dispatcher.py:170-178）

```python
context = CommandContext(
    sender=email_data.get('sender'),
    subject=email_data.get('subject'),
    body=email_data.get('body'),
    parsed_command=parsed_command,  # {"action": "download_movie", "title": "星际穿越"}
    timestamp=datetime.now(),
    config=plugin.config,
    logger=self.logger
)
```

### 5. 执行插件（plugin.py:83-108）

```python
def execute(self, context: CommandContext) -> PluginResult:
    action = context.parsed_command.get('action')

    if action in ['download_movie', 'add_movie']:
        return self._handle_add_movie(context)
```

### 6. 调用Radarr API（plugin.py:131-143）

```python
def _handle_add_movie(self, context: CommandContext):
    title = context.parsed_command.get('title')  # "星际穿越"

    # 搜索电影
    search_results = self.radarr_client.search_movie(title)

    # 获取第一个结果
    movie = search_results[0]

    # 添加到Radarr
    success = self.radarr_client.add_movie(
        movie_data=movie,
        root_folder=self.config['root_folder'],
        quality_profile_id=self.config.get('quality_profile_id', 1)
    )
```

### 7. 返回结果（plugin.py:169-178）

```python
if success:
    return PluginResult(
        success=True,
        message=f"电影《{movie_title}》({movie_year}) 已添加到下载队列喵~",
        data={
            "title": movie_title,
            "year": movie_year,
            "tmdb_id": movie.get('tmdbId')
        }
    )
```

### 8. 发送回复邮件（main.py:228-293）

```python
def _send_response_email(self, original_msg, results):
    # 根据results构造回复邮件
    if all_success:
        reply_body = f"""主人好喵~ (*^▽^*)

您的指令已经成功执行啦！

执行结果：
  ✓ 电影《星际穿越》(2014) 已添加到下载队列喵~

Catnip 会继续为您服务的喵~ 🐾
"""
    # 发送邮件
    self.email_provider.send_message(to=original_msg.sender, ...)
```

---

## 常见任务指南

### 任务1：添加一个新命令到现有插件

**场景**：在电影下载插件中添加"删除电影"功能

1. **更新元数据** (`plugin.py:36-52`)
   ```python
   def get_metadata(self):
       return PluginMetadata(
           commands=["download_movie", "add_movie", "search_movie", "delete_movie"]  # 添加
       )
   ```

2. **添加处理方法** (`plugin.py:83-108`)
   ```python
   def execute(self, context: CommandContext):
       action = context.parsed_command.get('action')

       if action in ['download_movie', 'add_movie']:
           return self._handle_add_movie(context)
       elif action == 'delete_movie':  # 新增
           return self._handle_delete_movie(context)
   ```

3. **实现具体逻辑**
   ```python
   def _handle_delete_movie(self, context: CommandContext):
       title = context.parsed_command.get('title')
       # 调用RadarrClient删除电影
       # ...
       return PluginResult(success=True, message=f"已删除电影《{title}》")
   ```

4. **更新LLM提示词** (`config/base.yaml`)
   ```yaml
   llm:
     system_prompt: |
       支持的命令:
       - download_movie: {"action": "download_movie", "title": "电影名"}
       - delete_movie: {"action": "delete_movie", "title": "电影名"}
   ```

### 任务2：创建一个新插件

参考 `docs/ARCHITECTURE.md` 中的"开发新插件"章节。

简要步骤：
1. 创建插件目录 `plugins/your_plugin/`
2. 实现 `plugin.py` 继承 `BasePlugin`
3. 在 `config/base.yaml` 中添加配置
4. 在 `main.py` 中注册插件
5. 更新LLM提示词

### 任务3：切换到不同的LLM模型

1. **查看可用模型**
   ```bash
   ollama list
   ```

2. **修改配置** (`config/base.yaml`)
   ```yaml
   llm:
     model: "llama2"  # 改成你想用的模型
   ```

3. **重启应用**

### 任务4：添加日志调试

```python
# 在任何地方添加日志
self.logger.debug(f"Debug info: {variable}")
self.logger.info(f"Important info: {variable}")
self.logger.warning(f"Warning: {variable}")
self.logger.error(f"Error: {variable}")
```

查看日志：
```bash
tail -f logs/homecentralmaid_20260116.log
```

### 任务5：修改邮件轮询间隔

修改 `config/base.yaml`:
```yaml
email:
  poll_interval: 60  # 从30秒改为60秒
```

---

## 调试技巧

### 1. 使用测试脚本

不需要真的发邮件，直接测试：

```python
# test_my_feature.py
from core.command_dispatcher import CommandDispatcher
from core.plugin_registry import PluginRegistry
from core.providers.ollama_provider import OllamaProvider
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# 初始化组件
registry = PluginRegistry(logger)
llm_provider = OllamaProvider(config, logger)
dispatcher = CommandDispatcher(registry, llm_provider, logger)

# 模拟邮件
email_data = {
    'sender': 'test@example.com',
    'subject': 'Test',
    'body': '帮我下载电影《盗梦空间》'
}

# 执行
results = dispatcher.process_email(email_data)

for result in results:
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Data: {result.data}")
```

### 2. 使用Python调试器

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或者使用ipdb（更友好）
import ipdb; ipdb.set_trace()
```

### 3. 查看数据库

```bash
sqlite3 data/catnip.db

# 查看命令历史
SELECT * FROM command_history ORDER BY timestamp DESC LIMIT 10;

# 查看最近的失败命令
SELECT * FROM command_history WHERE success = 0 ORDER BY timestamp DESC;
```

### 4. 测试LLM解析

```python
# test_llm.py
from core.providers.ollama_provider import OllamaProvider
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

config = {
    'model': 'qwen3:8b',
    'system_prompt': '...'  # 从config/base.yaml复制
}

provider = OllamaProvider(config, logger)

# 测试解析
result = provider.parse_command("帮我下载电影《盗梦空间》")

print(f"Success: {result.success}")
print(f"Data: {result.data}")
print(f"Raw: {result.raw}")
```

---

## 常见陷阱

### ❌ 陷阱1：忘记从config读取secret

```python
# 错误：硬编码密钥
api_key = "abc123"

# 正确：从config读取
api_key = self.config.get('api_key')
```

### ❌ 陷阱2：不处理异常

```python
# 错误：直接调用API
result = requests.get(url)

# 正确：处理异常
try:
    result = requests.get(url, timeout=10)
except requests.exceptions.Timeout:
    self.logger.error("API timeout")
    return PluginResult(success=False, message="超时")
except Exception as e:
    self.logger.error(f"Error: {e}")
    return PluginResult(success=False, message="错误")
```

### ❌ 陷阱3：返回None而不是PluginResult

```python
# 错误：返回None
def execute(self, context):
    # ...
    return None  # 会导致错误！

# 正确：总是返回PluginResult
def execute(self, context):
    # ...
    return PluginResult(success=False, message="未知错误")
```

### ❌ 陷阱4：忘记更新LLM提示词

添加新命令后，必须更新 `config/base.yaml` 中的 `system_prompt`，否则LLM不知道这个命令的存在。

### ❌ 陷阱5：secrets.yaml被提交到Git

**永远不要提交 `config/secrets.yaml`！**

检查：
```bash
git status  # 不应该看到 secrets.yaml
```

如果不小心添加了：
```bash
git rm --cached config/secrets.yaml
```

---

## 性能优化建议

### 1. LLM调用优化

- 使用更小的模型（如 `qwen3:8b` 而不是 `llama2:70b`）
- 精简system_prompt，只包含必要信息
- 考虑缓存常见命令的解析结果

### 2. 邮件轮询优化

- 调整 `poll_interval`（不要太频繁）
- 使用 IMAP IDLE 而不是轮询（需要修改EmailProvider）

### 3. 数据库优化

- 定期执行 `VACUUM` 清理数据库
- 为常用查询添加索引（已经有了基本索引）
- 定期归档旧的command_history

---

## 下一步

- 📖 深入阅读 [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)
- 🔌 尝试开发你的第一个插件
- 🐛 运行测试：`python test_components.py`
- 🚀 启动系统：`python main.py`

---

## 获取帮助

- **代码问题**：阅读相应模块的文档字符串
- **架构问题**：查看 `docs/ARCHITECTURE.md`
- **配置问题**：查看 `config/base.yaml` 中的注释
- **Bug报告**：提交 GitHub Issue

**祝你编码愉快！ 🎉**

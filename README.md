# HomeCentralMaid v2.0.0

> 家庭中央女仆系统 - Catnip 喵~

一个基于邮件和LLM的智能家庭管理系统。通过发送邮件指令，由Catnip女仆管家为你执行各种任务。

## 🎯 特性

- **邮件指令解析**：通过LLM智能理解你的自然语言指令
- **插件化架构**：轻松扩展新功能，无需修改核心代码
- **电影下载管理**：通过Radarr自动下载电影
- **完整的审计日志**：所有命令执行都有记录
- **命令历史**：可查询历史执行记录
- **自动回复**：执行成功或失败都会自动发邮件通知

## 🏗️ 架构

```
核心框架
├── 配置管理器 (ConfigManager) - YAML配置加载
├── 插件注册表 (PluginRegistry) - 插件管理
├── 命令调度器 (CommandDispatcher) - 路由命令到插件
├── 数据库层 (Database) - SQLite持久化
└── 提供者抽象 (Providers)
    ├── 邮件提供者 (EmailProvider) - IMAP/SMTP
    └── LLM提供者 (LLMProvider) - Ollama

插件层
└── 电影下载插件 (MovieDownloadPlugin)
    └── Radarr客户端
```

**📚 详细文档**：
- [架构文档 (ARCHITECTURE.md)](docs/ARCHITECTURE.md) - 详细的系统架构说明
- [快速入门 (QUICKSTART.md)](docs/QUICKSTART.md) - 5分钟快速上手指南

## 📦 安装

### 1. 克隆项目

```bash
cd D:\AAAbase\HomeCentralMaid
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括：
- `pyyaml>=6.0` - YAML配置文件解析
- `requests>=2.31.0` - HTTP客户端
- `ollama>=0.1.0` - Ollama LLM客户端

### 3. 配置

#### 3.1 编辑 `config/secrets.yaml`

```yaml
email:
  username: "你的邮箱@qq.com"
  password: "你的邮箱授权码"

plugins:
  movie_download:
    radarr_api_key: "YOUR_RADARR_API_KEY"
```

#### 3.2 编辑 `config/base.yaml` (可选)

```yaml
email:
  poll_interval: 30  # 邮件轮询间隔（秒）
  allowed_senders:
    - "你信任的邮箱@gmail.com"

llm:
  model: "qwen3:8b"  # Ollama模型

plugins:
  movie_download:
    root_folder: "D:\\Movies"  # 电影下载目录
    quality_profile_id: 1
```

### 4. 启动Ollama（如果还没运行）

```bash
ollama serve
```

### 5. 启动Radarr（电影下载功能需要）

确保Radarr运行在 `http://localhost:7878`

## 🚀 运行

### 生产环境

```bash
python main.py
# 或
python main.py production
```

### 开发环境（更详细的日志）

```bash
python main.py development
```

### 测试初始化

不启动邮件轮询，只测试组件初始化：

```bash
python test_init.py
```

### 测试所有组件

运行完整的组件测试套件：

```bash
python test_components.py
```

## 📧 使用方法

### 1. 发送邮件指令

从允许的邮箱发送邮件到系统邮箱，例如：

```
主题：下载电影
内容：帮我下载电影《星际穿越》
```

### 2. Catnip处理

系统会：
1. 收到邮件
2. 用LLM解析你的指令
3. 路由到对应的插件
4. 执行任务
5. 发送回复邮件

### 3. 收到回复

成功时：
```
主人好喵~ (*^▽^*)

您的指令已经成功执行啦！

执行结果：
  ✓ 电影《星际穿越》(2014) 已添加到下载队列喵~ Catnip会自动为您下载的~

Catnip 会继续为您服务的喵~ 🐾
```

失败时会包含详细的错误信息。

## 🔌 支持的命令

### 电影下载插件

- **download_movie** / **add_movie**: 添加电影到Radarr
  - 示例：`帮我下载电影《盗梦空间》`

- **search_movie**: 搜索电影（不添加）
  - 示例：`搜索电影《复仇者联盟》`

## 📁 项目结构

```
HomeCentralMaid/
├── core/                          # 核心框架
│   ├── plugin_base.py             # 插件基类
│   ├── plugin_registry.py         # 插件注册
│   ├── config_manager.py          # 配置管理
│   ├── database.py                # 数据库层
│   ├── command_dispatcher.py      # 命令调度
│   ├── logger.py                  # 日志配置
│   └── providers/                 # 提供者实现
│       ├── email_provider.py      # 邮件抽象
│       ├── imap_smtp_provider.py  # IMAP/SMTP
│       ├── llm_provider.py        # LLM抽象
│       └── ollama_provider.py     # Ollama
│
├── plugins/                       # 插件目录
│   └── movie_download/            # 电影下载插件
│       ├── plugin.py              # 插件主类
│       └── radarr_client.py       # Radarr客户端
│
├── config/                        # 配置文件
│   ├── base.yaml                  # 基础配置
│   ├── development.yaml           # 开发配置
│   └── secrets.yaml               # 凭证（不提交）
│
├── data/                          # 运行时数据
│   └── catnip.db                  # SQLite数据库
│
├── logs/                          # 日志文件
│
├── main.py                        # 应用入口
├── test_init.py                   # 初始化测试
├── test_components.py             # 组件测试
└── requirements.txt               # Python依赖
```

## 🔧 开发新插件

### 1. 创建插件目录

```bash
mkdir -p plugins/my_plugin
```

### 2. 实现插件类

```python
# plugins/my_plugin/plugin.py
from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult

class MyPlugin(BasePlugin):
    def get_metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="你的名字",
            description="插件功能描述",
            commands=["my_command"],
            config_schema={}
        )

    def initialize(self):
        # 初始化资源
        return True

    def execute(self, context):
        # 执行命令
        return PluginResult(
            success=True,
            message="命令执行成功"
        )

    def cleanup(self):
        # 清理资源
        pass
```

### 3. 在配置中启用

编辑 `config/base.yaml`:

```yaml
plugins:
  enabled:
    - "movie_download"
    - "my_plugin"  # 添加你的插件
```

### 4. 在main.py中注册

```python
# 在main.py的initialize方法中添加
elif plugin_name == "my_plugin":
    from plugins.my_plugin.plugin import MyPlugin
    self.plugin_registry.register(MyPlugin, plugin_config)
```

## 📊 数据库

系统使用SQLite存储：

- **command_history**: 命令执行历史
- **task_queue**: 后台任务队列（未来功能）
- **user_preferences**: 用户配置
- **plugin_state**: 插件状态存储

数据库位置：`data/catnip.db` (或 `catnip_dev.db` 在开发环境)

## 📝 日志

日志文件位置：`logs/homecentralmaid_YYYYMMDD.log`

日志级别：
- **生产环境**: INFO
- **开发环境**: DEBUG

## 🔒 安全性

### 已实施的安全措施

- ✅ 凭证存储在 `config/secrets.yaml` (已加入 .gitignore)
- ✅ 支持环境变量替换
- ✅ 发件人白名单验证
- ✅ 所有命令记录到数据库（审计追踪）
- ✅ 参数化SQL查询防止注入

### 建议

- 不要将 `config/secrets.yaml` 提交到Git
- 定期更改邮箱授权码
- 限制允许的发件人列表

## 🎯 路线图

### 当前版本 (v2.0.0)
- ✅ 插件化架构
- ✅ 邮件+LLM指令解析
- ✅ 电影下载插件
- ✅ 命令历史记录
- ✅ 配置外部化

### 未来计划
- [ ] 后台任务队列（长时间运行的任务）
- [ ] 智能家居插件（Home Assistant集成）
- [ ] Git服务器管理插件
- [ ] Web管理界面
- [ ] 更多LLM提供者（OpenAI、Claude）
- [ ] 更多邮件提供者（Gmail API）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 💬 联系

有问题或建议？欢迎提Issue！

---

*Made with ❤️ by Catnip 喵~*

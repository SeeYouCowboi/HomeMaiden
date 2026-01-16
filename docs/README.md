# HomeCentralMaid 文档中心

欢迎来到 HomeCentralMaid 文档中心！这里包含了所有你需要的文档资源。

## 📚 文档列表

### 🚀 [快速入门 (QUICKSTART.md)](./QUICKSTART.md)
**适合人群**：新接手的开发人员、第一次接触项目的人

**内容**：
- 5分钟理解整个项目
- 代码结构速览
- 代码阅读路线图
- 关键数据结构说明
- 常见任务指南（添加命令、创建插件等）
- 调试技巧和常见陷阱

**阅读时间**：10-15分钟

---

### 🏛️ [架构文档 (ARCHITECTURE.md)](./ARCHITECTURE.md)
**适合人群**：需要深入理解系统设计的开发人员、架构师

**内容**：
- 系统概述和设计理念
- 完整的架构图和数据流
- 核心组件详细解析
- 插件系统设计
- 提供者抽象层说明
- 数据库设计
- 配置系统详解
- 开发新功能完整指南
- 最佳实践和未来规划

**阅读时间**：30-45分钟

---

### ✅ [开发者清单 (CHECKLIST.md)](./CHECKLIST.md)
**适合人群**：所有开发人员、贡献者

**内容**：
- 添加新插件清单
- 添加新命令清单
- 代码规范清单
- 安全清单
- 性能清单
- 测试清单
- 提交PR清单

**阅读时间**：10分钟

---

## 📖 阅读建议

### 如果你是...

#### 👨‍💻 新接手的开发人员
**推荐路线**：
1. 先读 [QUICKSTART.md](./QUICKSTART.md) 快速了解项目
2. 运行一次 `python main.py` 看看系统如何工作
3. 阅读 [ARCHITECTURE.md](./ARCHITECTURE.md) 深入理解设计
4. 尝试修改代码或添加新功能

#### 🏗️ 架构师/技术负责人
**推荐路线**：
1. 直接阅读 [ARCHITECTURE.md](./ARCHITECTURE.md)
2. 查看 `core/` 目录下的核心模块源码
3. 评估架构设计和扩展性

#### 🔌 插件开发者
**推荐路线**：
1. 阅读 [QUICKSTART.md](./QUICKSTART.md) 的"常见任务指南"部分
2. 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 的"插件系统"和"开发新功能"章节
3. 参考 `plugins/movie_download/` 示例
4. 开始开发你的插件

#### 🐛 维护者/运维人员
**推荐路线**：
1. 阅读 [QUICKSTART.md](./QUICKSTART.md) 了解系统组成
2. 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 的"配置系统"和"常见问题"部分
3. 熟悉日志和数据库查询
4. 了解备份和恢复流程

---

## 🆘 获取帮助

### 问题类型

| 问题类型 | 查看文档 | 补充资源 |
|---------|---------|---------|
| 快速上手 | [QUICKSTART.md](./QUICKSTART.md) | README.md |
| 架构设计 | [ARCHITECTURE.md](./ARCHITECTURE.md) | 源码注释 |
| 配置问题 | [ARCHITECTURE.md](./ARCHITECTURE.md) #配置系统 | `config/base.yaml` |
| 插件开发 | [ARCHITECTURE.md](./ARCHITECTURE.md) #插件系统 | `core/plugin_base.py` |
| 调试技巧 | [QUICKSTART.md](./QUICKSTART.md) #调试技巧 | 日志文件 |
| 数据库 | [ARCHITECTURE.md](./ARCHITECTURE.md) #数据库设计 | `core/database.py` |

---

## 📝 文档贡献

发现文档错误或有改进建议？欢迎贡献！

1. 在源码中改进注释和文档字符串
2. 更新或扩展这些Markdown文档
3. 添加新的示例和最佳实践

---

## 🔗 相关资源

### 项目资源
- [主 README](../README.md) - 项目总览和快速安装指南
- [requirements.txt](../requirements.txt) - Python依赖列表
- [.gitignore](../.gitignore) - Git忽略规则

### 核心模块文档
所有核心模块都有详细的文档字符串，直接阅读源码：
- `core/config_manager.py` - 配置管理
- `core/database.py` - 数据库操作
- `core/plugin_base.py` - 插件接口定义
- `core/plugin_registry.py` - 插件管理
- `core/command_dispatcher.py` - 命令调度
- `core/providers/` - 提供者抽象层

### 外部资源
- [Ollama 文档](https://github.com/ollama/ollama) - 本地LLM运行器
- [Radarr API](https://radarr.video/docs/api/) - Radarr API文档
- [Python IMAP 文档](https://docs.python.org/3/library/imaplib.html)
- [Python SMTP 文档](https://docs.python.org/3/library/smtplib.html)

---

**最后更新**: 2026-01-16
**维护者**: HomeCentralMaid Team

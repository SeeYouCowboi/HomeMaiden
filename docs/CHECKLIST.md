# 开发者清单

> 确保你的代码符合项目标准

## 🔌 添加新插件清单

在提交PR之前，请确保完成以下所有步骤：

### 代码实现
- [ ] 创建插件目录 `plugins/your_plugin/`
- [ ] 实现 `plugin.py` 继承 `BasePlugin`
- [ ] 实现所有必需方法：
  - [ ] `get_metadata()` - 返回插件元数据
  - [ ] `initialize()` - 初始化资源，返回 bool
  - [ ] `execute()` - 执行命令，返回 `PluginResult`
  - [ ] `cleanup()` - 清理资源
- [ ] （可选）覆盖 `health_check()` 实现自定义健康检查
- [ ] 所有方法都有文档字符串
- [ ] 代码有适当的错误处理（try-except）
- [ ] 使用 `self.logger` 记录关键操作

### 配置
- [ ] 在 `config/base.yaml` 中添加插件配置
- [ ] 敏感信息使用环境变量（`${ENV_VAR}`）
- [ ] 在 `config/secrets.yaml.example` 中添加示例配置
- [ ] 在 `get_metadata()` 中定义 `config_schema`

### 注册
- [ ] 在 `main.py` 的 `initialize()` 中注册插件
- [ ] 在 `config/base.yaml` 的 `plugins.enabled` 列表中添加插件名

### LLM集成
- [ ] 更新 `config/base.yaml` 中的 `llm.system_prompt`
- [ ] 添加命令格式说明
- [ ] 提供命令示例

### 文档
- [ ] 创建 `plugins/your_plugin/README.md`
- [ ] 说明插件功能
- [ ] 列出所有命令和参数
- [ ] 提供配置示例
- [ ] 添加使用示例
- [ ] 更新主 `README.md`（在"支持的命令"部分）

### 测试
- [ ] 创建测试脚本 `plugins/your_plugin/test_plugin.py`
- [ ] 测试插件初始化
- [ ] 测试所有命令
- [ ] 测试错误处理
- [ ] 手动测试完整流程（发邮件 → 执行 → 收回复）

---

## ➕ 添加新命令到现有插件清单

- [ ] 在 `get_metadata()` 的 `commands` 列表中添加命令名
- [ ] 在 `execute()` 中添加命令路由
- [ ] 实现命令处理方法 `_handle_xxx()`
- [ ] 更新插件的 `README.md`
- [ ] 更新 `config/base.yaml` 的 LLM 提示词
- [ ] 测试新命令

---

## 🔄 修改核心模块清单

**警告**：修改核心模块需要特别小心！

- [ ] 充分理解现有代码逻辑
- [ ] 考虑向后兼容性
- [ ] 更新相关文档字符串
- [ ] 测试所有现有插件是否正常工作
- [ ] 更新 `docs/ARCHITECTURE.md` 如果架构有变化
- [ ] 进行完整的集成测试

---

## 📝 代码规范清单

### Python风格
- [ ] 遵循 PEP 8 代码风格
- [ ] 使用 4 空格缩进
- [ ] 行长度不超过 100 字符（可适当超出）
- [ ] 导入顺序：标准库 → 第三方库 → 本地模块
- [ ] 导入按字母顺序排序

### 命名规范
- [ ] 类名使用 `PascalCase`
- [ ] 函数/方法使用 `snake_case`
- [ ] 常量使用 `UPPER_SNAKE_CASE`
- [ ] 私有方法使用 `_leading_underscore`
- [ ] 描述性命名，避免缩写（除非是通用缩写）

### 文档字符串
- [ ] 所有公共类、方法、函数都有文档字符串
- [ ] 使用 Google/NumPy 风格
- [ ] 包含 Args、Returns、Raises（如适用）
- [ ] 复杂逻辑有注释说明

### 类型提示
- [ ] 函数参数有类型提示
- [ ] 函数返回值有类型提示
- [ ] 使用 `typing` 模块的类型（Dict, List, Optional等）

### 错误处理
- [ ] 所有外部调用（API、文件、数据库）有异常处理
- [ ] 捕获具体异常类型，避免裸 `except:`
- [ ] 记录错误到日志（包含上下文信息）
- [ ] 返回友好的错误消息给用户

### 日志记录
- [ ] 使用 `self.logger` 而不是 `print()`
- [ ] 使用合适的日志级别：
  - DEBUG: 详细调试信息
  - INFO: 正常操作信息
  - WARNING: 警告但不影响功能
  - ERROR: 错误但可恢复
  - CRITICAL: 严重错误
- [ ] 关键操作有日志记录
- [ ] 错误日志包含足够的上下文

---

## 🔒 安全清单

- [ ] 不在代码中硬编码密钥、密码
- [ ] 敏感信息使用环境变量或 `secrets.yaml`
- [ ] 验证和清理用户输入
- [ ] 使用参数化SQL查询（不要字符串拼接）
- [ ] 限制API调用的超时时间
- [ ] 检查文件路径，防止路径遍历攻击
- [ ] 不提交 `config/secrets.yaml` 到Git

---

## 📊 性能清单

- [ ] 避免在循环中进行数据库/API调用
- [ ] 使用批量操作替代多次单个操作
- [ ] 设置合理的超时时间
- [ ] 大文件/数据流式处理，不全部加载到内存
- [ ] 考虑添加缓存（如果适用）

---

## 🧪 测试清单

### 单元测试
- [ ] 测试插件初始化成功情况
- [ ] 测试插件初始化失败情况（配置错误）
- [ ] 测试每个命令的成功路径
- [ ] 测试错误处理（API失败、网络超时等）
- [ ] 测试边界条件

### 集成测试
- [ ] 测试完整的邮件处理流程
- [ ] 测试LLM解析 → 插件执行流程
- [ ] 测试数据库记录是否正确
- [ ] 测试回复邮件是否发送

### 手动测试
- [ ] 发送真实邮件测试
- [ ] 测试各种用户输入（正常、异常、边界）
- [ ] 测试并发情况（如果适用）
- [ ] 检查日志输出是否合理
- [ ] 检查数据库记录是否正确

---

## 📤 提交PR清单

- [ ] 代码已通过所有测试
- [ ] 更新了相关文档
- [ ] Commit消息清晰明了
- [ ] 没有调试代码（如 `print()`, `pdb`）
- [ ] 没有无用的注释代码
- [ ] 解决了所有 TODO 和 FIXME
- [ ] PR描述清楚说明了：
  - [ ] 改动内容
  - [ ] 改动原因
  - [ ] 测试方法
  - [ ] 相关Issue（如有）

---

## 🎯 质量标准

### 代码质量
- ✅ 代码清晰易读
- ✅ 逻辑简洁，避免过度工程
- ✅ 遵循DRY原则（Don't Repeat Yourself）
- ✅ 单一职责原则
- ✅ 适当的抽象层次

### 文档质量
- ✅ 文档完整准确
- ✅ 示例代码可运行
- ✅ 用户能根据文档独立使用功能

### 测试质量
- ✅ 测试覆盖核心功能
- ✅ 测试能捕获真实问题
- ✅ 测试稳定可重复

---

## ✨ 可选增强项

这些不是必需的，但会让你的贡献更出色：

- [ ] 添加类型注解（类型提示）
- [ ] 添加性能基准测试
- [ ] 添加配置验证
- [ ] 添加使用示例脚本
- [ ] 改进错误消息的友好度
- [ ] 添加进度指示（对于长时间操作）
- [ ] 支持配置热重载
- [ ] 添加监控指标（execution_time等）

---

## 📋 示例检查流程

### 步骤 1: 开发前
```bash
# 创建功能分支
git checkout -b feature/your-feature

# 阅读相关文档
cat docs/QUICKSTART.md
cat docs/ARCHITECTURE.md
```

### 步骤 2: 开发中
```bash
# 编写代码
# 编写文档
# 编写测试

# 定期commit
git add .
git commit -m "feat: add xxx feature"
```

### 步骤 3: 开发后
```bash
# 运行所有测试
python test_components.py
python plugins/your_plugin/test_plugin.py

# 运行应用测试
python main.py

# 检查代码质量（如果安装了工具）
pylint plugins/your_plugin/plugin.py
black --check plugins/your_plugin/

# 检查文档
# 确保README.md更新了
# 确保ARCHITECTURE.md更新了（如有架构变化）
```

### 步骤 4: 提交前
```bash
# 最后检查
git status                     # 确认所有文件都正确添加
git diff --cached              # 检查暂存的更改
cat config/secrets.yaml        # 确保没被添加到Git

# 提交
git push origin feature/your-feature

# 创建PR
# 填写清晰的PR描述
```

---

**记住**：质量比速度更重要。花时间确保代码正确、文档完整、测试充分，将节省未来的维护时间！

**最后更新**: 2026-01-16

"""
HomeCentralMaid - 家庭中央女仆系统

一个基于邮件和LLM的智能家庭管理系统。
通过邮件发送指令，由Catnip女仆管家为你执行各种任务。

Features:
- 邮件指令解析（通过LLM）
- 插件化架构（易于扩展）
- 电影下载管理（通过Radarr）
- 完整的审计日志
- 命令历史记录

Author: HomeCentralMaid
Version: 2.0.0
"""

import sys
import time
import signal
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from core.config_manager import ConfigManager
from core.logger import setup_logging
from core.database import Database
from core.plugin_registry import PluginRegistry
from core.command_dispatcher import CommandDispatcher
from core.providers import IMAPSMTPProvider, OllamaProvider

# Plugin imports
from plugins.movie_download.plugin import MovieDownloadPlugin


class HomeCentralMaid:
    """Main application class for HomeCentralMaid"""

    def __init__(self, env: str = "production"):
        """
        Initialize HomeCentralMaid application

        Args:
            env: Environment name (development, production)
        """
        self.env = env
        self.running = False

        # Components (initialized in initialize())
        self.config = None
        self.logger = None
        self.database = None
        self.email_provider = None
        self.llm_provider = None
        self.plugin_registry = None
        self.dispatcher = None

    def initialize(self) -> bool:
        """
        Initialize all components

        Returns:
            True if initialization successful
        """
        try:
            print("Initializing HomeCentralMaid...")

            # Step 1: Load configuration
            print("  [1/6] Loading configuration...")
            self.config = ConfigManager()
            if not self.config.load(env=self.env):
                print("  [FAIL] Configuration loading failed")
                return False
            print(f"  [OK] Configuration loaded ({self.env})")

            # Step 2: Setup logging
            print("  [2/6] Setting up logging...")
            self.logger = setup_logging(
                log_dir=self.config.get('system.log_dir', 'logs'),
                log_level=self.config.get('system.log_level', 'INFO'),
                app_name=self.config.get('system.app_name', 'HomeCentralMaid')
            )
            app_name = self.config.get('system.app_name')
            app_version = self.config.get('system.version')
            self.logger.info(f"Starting {app_name} v{app_version}")
            self.logger.info(f"Environment: {self.env}")
            print(f"  [OK] Logging configured")

            # Step 3: Initialize database
            print("  [3/6] Connecting to database...")
            self.database = Database(
                db_path=self.config.get('database.path', 'data/catnip.db')
            )
            if not self.database.connect():
                self.logger.error("Database connection failed")
                print("  [FAIL] Database connection failed")
                return False
            print(f"  [OK] Database connected")

            # Step 4: Initialize providers
            print("  [4/6] Initializing providers...")

            # Email provider
            email_config = self.config.get('email')
            self.email_provider = IMAPSMTPProvider(email_config, self.logger)
            if not self.email_provider.connect():
                self.logger.error("Email provider connection failed")
                print("  [FAIL] Email provider connection failed")
                return False
            print("    - Email provider connected")

            # LLM provider
            llm_config = self.config.get('llm')
            self.llm_provider = OllamaProvider(llm_config, self.logger)
            # Note: We don't test LLM connection here as it might not be running yet
            print(f"    - LLM provider initialized ({self.llm_provider.get_model_name()})")

            # Step 5: Initialize plugin registry and register plugins
            print("  [5/6] Registering plugins...")
            self.plugin_registry = PluginRegistry(self.logger)

            enabled_plugins = self.config.get('plugins.enabled', [])
            registered_count = 0

            for plugin_name in enabled_plugins:
                plugin_config = self.config.get_plugin_config(plugin_name)

                # Map plugin name to class
                if plugin_name == "movie_download":
                    if self.plugin_registry.register(MovieDownloadPlugin, plugin_config):
                        registered_count += 1
                        print(f"    - Registered: movie_download")
                    else:
                        self.logger.warning(f"Failed to register plugin: {plugin_name}")
                        print(f"    - [WARN] Failed to register: {plugin_name}")
                # Add more plugins here as they're developed

            print(f"  [OK] {registered_count}/{len(enabled_plugins)} plugins registered")

            # Step 6: Initialize command dispatcher
            print("  [6/6] Initializing command dispatcher...")
            self.dispatcher = CommandDispatcher(
                self.plugin_registry,
                self.llm_provider,
                self.logger
            )
            print(f"  [OK] Command dispatcher ready")

            self.logger.info("All components initialized successfully")
            print("\n[SUCCESS] HomeCentralMaid initialized successfully!\n")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization failed: {e}", exc_info=True)
            else:
                print(f"[FAIL] Initialization failed: {e}")
                import traceback
                traceback.print_exc()
            return False

    def run(self):
        """Main application loop"""
        self.running = True
        poll_interval = self.config.get('email.poll_interval', 30)

        app_name = self.config.get('system.app_name', 'Catnip')
        self.logger.info(f"{app_name} 正在监视邮件喵喵... (polling every {poll_interval}s)")
        print(f"{app_name} 正在监视邮件喵喵...")
        print(f"轮询间隔: {poll_interval} 秒")
        print(f"允许的发件人: {self.config.get('email.allowed_senders', [])}")
        print("\n按 Ctrl+C 停止\n")

        while self.running:
            try:
                # Get unread messages
                messages = self.email_provider.get_unread_messages(limit=5)

                for msg in messages:
                    self.logger.info(f"处理邮件 - 发件人: {msg.sender}, 主题: {msg.subject}")
                    print(f"\n[新邮件] 发件人: {msg.sender}")
                    print(f"        主题: {msg.subject}")

                    # Process email through dispatcher
                    start_time = time.time()
                    results = self.dispatcher.process_email({
                        'sender': msg.sender,
                        'subject': msg.subject,
                        'body': msg.body
                    })
                    execution_time = int((time.time() - start_time) * 1000)

                    # Log all command results to database
                    for result in results:
                        self.database.log_command(
                            sender=msg.sender,
                            subject=msg.subject,
                            command_action=result.data.get('action', 'unknown'),
                            command_data=result.data,
                            plugin_name=result.data.get('plugin_name', 'unknown'),
                            success=result.success,
                            result_message=result.message,
                            result_data=result.data,
                            execution_time_ms=result.data.get('execution_time_ms', execution_time)
                        )

                    # Send response email
                    self._send_response_email(msg, results)

                    # Mark as read
                    self.email_provider.mark_as_read(msg.message_id)

                # Sleep until next poll
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                self.logger.info("收到中断信号，正在关闭...")
                print("\n\n正在关闭...")
                self.running = False
            except Exception as e:
                self.logger.error(f"主循环错误: {e}", exc_info=True)
                print(f"[ERROR] {e}")
                time.sleep(poll_interval)

    def _send_response_email(self, original_msg, results):
        """
        Send response email with command results

        Args:
            original_msg: Original email message
            results: List of PluginResult objects
        """
        try:
            # Determine overall success
            all_success = all(r.success for r in results)

            if all_success:
                # All commands succeeded
                reply_subject = f"Re: {original_msg.subject} - 任务执行成功 ✓"
                executed_tasks = [f"  ✓ {r.message}" for r in results]

                reply_body = f"""主人好喵~ (*^▽^*)

您的指令已经成功执行啦！

执行结果：
{chr(10).join(executed_tasks)}

Catnip 会继续为您服务的喵~ 🐾

---
Catnip 家庭女仆管家
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
                print("  [OK] 所有命令执行成功")

            else:
                # Some commands failed
                reply_subject = f"Re: {original_msg.subject} - 执行遇到问题"
                task_results = []
                for r in results:
                    status = "✓" if r.success else "✗"
                    task_results.append(f"  {status} {r.message}")

                reply_body = f"""主人，有些任务执行遇到问题喵... (｡•́︿•̀｡)

执行结果：
{chr(10).join(task_results)}

请检查日志或重试喵~

---
Catnip 家庭女仆管家
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
                print("  [WARN] 部分命令执行失败")

            # Send email
            if self.email_provider.send_message(
                to=original_msg.sender,
                subject=reply_subject,
                body=reply_body
            ):
                print("  [OK] 回复邮件已发送")
            else:
                print("  [FAIL] 回复邮件发送失败")

        except Exception as e:
            self.logger.error(f"发送回复邮件失败: {e}", exc_info=True)
            print(f"  [ERROR] 发送回复失败: {e}")

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down HomeCentralMaid...")
        print("\nShutting down...")

        self.running = False

        if self.plugin_registry:
            self.plugin_registry.cleanup_all()

        if self.email_provider:
            self.email_provider.disconnect()

        if self.database:
            self.database.close()

        self.logger.info("Shutdown complete")
        print("Shutdown complete. Goodbye!\n")


def main():
    """Application entry point"""
    # Parse command line arguments
    env = sys.argv[1] if len(sys.argv) > 1 else "production"

    # Banner
    print("\n" + "=" * 60)
    print("  HomeCentralMaid - Catnip 家庭中央女仆系统 v2.0.0")
    print("=" * 60 + "\n")

    # Create application
    app = HomeCentralMaid(env=env)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\n\n[SIGNAL] 收到关闭信号...")
        app.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize and run
    if app.initialize():
        try:
            app.run()
        except Exception as e:
            print(f"\n[FATAL ERROR] {e}")
            import traceback
            traceback.print_exc()
            app.shutdown()
            sys.exit(1)
    else:
        print("\n[FAIL] 应用初始化失败")
        print("请检查配置文件和日志")
        sys.exit(1)


if __name__ == "__main__":
    main()

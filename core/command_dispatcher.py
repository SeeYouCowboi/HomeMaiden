"""
Command Dispatcher

Routes commands from emails to appropriate plugins. This is the orchestration
layer that connects email parsing, LLM processing, and plugin execution.
"""

from typing import Dict, Any, List
from datetime import datetime
import time
import logging

from core.plugin_base import CommandContext, PluginResult
from core.plugin_registry import PluginRegistry
from core.providers.llm_provider import LLMProvider


class CommandDispatcher:
    """Routes commands to appropriate plugins"""

    def __init__(
        self,
        registry: PluginRegistry,
        llm_provider: LLMProvider,
        logger: logging.Logger
    ):
        """
        Initialize command dispatcher

        Args:
            registry: Plugin registry for command routing
            llm_provider: LLM provider for parsing natural language
            logger: Logger instance
        """
        self.registry = registry
        self.llm_provider = llm_provider
        self.logger = logger

    def process_email(self, email_data: Dict[str, Any]) -> List[PluginResult]:
        """
        Process an email: parse with LLM, route to plugins, execute.

        Workflow:
        1. Parse email body with LLM to extract commands
        2. If parsing fails, return error result
        3. For each parsed command:
           a. Find plugin that handles the command
           b. Create execution context
           c. Execute plugin
           d. Collect result
        4. Return all results

        Args:
            email_data: Dictionary with keys:
                - sender: Email sender address
                - subject: Email subject
                - body: Email body text

        Returns:
            List of PluginResult objects (one per command)
        """
        results = []
        sender = email_data.get('sender', 'unknown')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')

        self.logger.info(f"Processing email from {sender}: {subject}")

        try:
            # Step 1: Parse email with LLM
            start_time = time.time()
            llm_result = self.llm_provider.parse_command(body)
            parse_time = int((time.time() - start_time) * 1000)

            self.logger.debug(f"LLM parsing took {parse_time}ms")

            # Step 2: Check if parsing succeeded
            if not llm_result.success:
                self.logger.warning(f"LLM parsing failed: {llm_result.error}")
                return [PluginResult(
                    success=False,
                    message=f"无法理解指令: {llm_result.error}",
                    data={
                        "error": llm_result.error,
                        "raw_output": llm_result.raw,
                        "parse_time_ms": parse_time
                    }
                )]

            # Step 3: Execute each parsed command
            commands = llm_result.data
            self.logger.info(f"LLM parsed {len(commands)} command(s)")

            if not commands:
                return [PluginResult(
                    success=False,
                    message="邮件中没有识别到有效的命令",
                    data={"raw_output": llm_result.raw}
                )]

            for idx, cmd_data in enumerate(commands):
                self.logger.debug(f"Processing command {idx + 1}/{len(commands)}: {cmd_data}")
                result = self._execute_command(email_data, cmd_data)
                results.append(result)

            self.logger.info(f"Processed {len(results)} commands, "
                           f"{sum(1 for r in results if r.success)} succeeded")

            return results

        except Exception as e:
            self.logger.error(f"Error processing email: {e}", exc_info=True)
            return [PluginResult(
                success=False,
                message=f"处理邮件时出错: {str(e)}",
                data={"exception": str(e)}
            )]

    def _execute_command(
        self,
        email_data: Dict[str, Any],
        parsed_command: Dict[str, Any]
    ) -> PluginResult:
        """
        Execute a single command via appropriate plugin

        Args:
            email_data: Original email data
            parsed_command: Parsed command dictionary from LLM

        Returns:
            PluginResult from plugin execution
        """
        action = parsed_command.get('action')

        if not action:
            self.logger.warning("Command missing 'action' field")
            return PluginResult(
                success=False,
                message="命令格式错误：缺少 action 字段",
                data={"parsed_command": parsed_command}
            )

        # Find plugin for this command
        plugin = self.registry.get_plugin_for_command(action)

        if not plugin:
            self.logger.warning(f"No plugin found for action: {action}")
            available_commands = list(self.registry.list_commands().keys())
            return PluginResult(
                success=False,
                message=f"不支持的命令: {action}",
                data={
                    "action": action,
                    "available_commands": available_commands
                }
            )

        # Check plugin health
        if not plugin.health_check():
            plugin_name = plugin.get_metadata().name
            self.logger.error(f"Plugin {plugin_name} health check failed")
            return PluginResult(
                success=False,
                message=f"插件 {plugin_name} 不可用",
                data={"plugin_name": plugin_name, "action": action}
            )

        # Build execution context
        context = CommandContext(
            sender=email_data.get('sender', 'unknown'),
            subject=email_data.get('subject', ''),
            body=email_data.get('body', ''),
            parsed_command=parsed_command,
            timestamp=datetime.now(),
            config=plugin.config,
            logger=self.logger
        )

        # Execute plugin
        try:
            start_time = time.time()
            result = plugin.execute(context)
            execution_time = int((time.time() - start_time) * 1000)

            # Add metadata to result
            result.data['plugin_name'] = plugin.get_metadata().name
            result.data['action'] = action
            result.data['execution_time_ms'] = execution_time

            status = "success" if result.success else "failed"
            self.logger.info(
                f"Plugin {plugin.get_metadata().name} executed: {status} "
                f"({execution_time}ms)"
            )

            return result

        except Exception as e:
            self.logger.error(
                f"Plugin execution error: {e}",
                exc_info=True
            )
            return PluginResult(
                success=False,
                message=f"执行命令时出错: {str(e)}",
                data={
                    "plugin_name": plugin.get_metadata().name,
                    "action": action,
                    "exception": str(e)
                }
            )

    def get_available_commands(self) -> Dict[str, str]:
        """
        Get all available commands and their descriptions

        Returns:
            Dictionary mapping command -> plugin description
        """
        result = {}
        command_map = self.registry.list_commands()

        for command, plugin_name in command_map.items():
            plugin = self.registry.get_plugin(plugin_name)
            if plugin:
                metadata = plugin.get_metadata()
                result[command] = metadata.description

        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get dispatcher statistics

        Returns:
            Dictionary with statistics
        """
        plugins = self.registry.list_plugins()
        health_status = self.registry.health_check()

        return {
            "total_plugins": len(plugins),
            "total_commands": len(self.registry.list_commands()),
            "healthy_plugins": sum(1 for status in health_status.values() if status),
            "llm_model": self.llm_provider.get_model_name(),
            "plugins": [
                {
                    "name": p.name,
                    "version": p.version,
                    "commands": p.commands,
                    "healthy": health_status.get(p.name, False)
                }
                for p in plugins
            ]
        }

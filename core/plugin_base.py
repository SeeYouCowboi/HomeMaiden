"""
Plugin Base Classes and Interfaces

This module defines the base classes and interfaces that all plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging


class PluginStatus(Enum):
    """Plugin lifecycle status"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    FAILED = "failed"


@dataclass
class PluginMetadata:
    """Plugin metadata descriptor"""
    name: str
    version: str
    author: str
    description: str
    commands: List[str]  # Commands this plugin handles
    dependencies: List[str] = field(default_factory=list)  # Other plugins this depends on
    config_schema: Dict[str, Any] = field(default_factory=dict)  # Expected config structure
    priority: int = 100  # Lower = higher priority for command routing


@dataclass
class CommandContext:
    """Context passed to plugin when executing a command"""
    sender: str
    subject: str
    body: str
    parsed_command: Dict[str, Any]
    timestamp: datetime
    config: Dict[str, Any]
    logger: logging.Logger


class PluginResult:
    """Standardized result from plugin execution"""

    def __init__(self, success: bool, message: str, data: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"PluginResult(success={self.success}, message='{self.message}')"


class BasePlugin(ABC):
    """
    Base class all plugins must inherit from

    Plugins provide the core extensibility mechanism for HomeCentralMaid.
    Each plugin handles specific commands and can maintain its own state.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize plugin with configuration and logger

        Args:
            config: Plugin-specific configuration dictionary
            logger: Logger instance for this plugin
        """
        self.config = config
        self.logger = logger
        self.status = PluginStatus.UNLOADED

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Return plugin metadata

        Returns:
            PluginMetadata describing this plugin's capabilities
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize plugin resources (connections, validate config, etc.)

        Called once when plugin is loaded. Use this to:
        - Validate configuration
        - Establish connections to external services
        - Allocate resources

        Returns:
            True on successful initialization, False on failure
        """
        pass

    @abstractmethod
    def execute(self, context: CommandContext) -> PluginResult:
        """
        Execute the plugin's action based on the command context

        This is the main entry point for command execution. The plugin
        should extract relevant data from context.parsed_command and
        perform the requested action.

        Args:
            context: Command execution context

        Returns:
            PluginResult indicating success/failure and any data
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Cleanup plugin resources

        Called when plugin is being unloaded or system is shutting down.
        Use this to:
        - Close connections
        - Release resources
        - Save state if needed
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate plugin configuration against schema

        Override if custom validation needed. Default implementation
        performs basic validation against config_schema.

        Returns:
            True if configuration is valid
        """
        metadata = self.get_metadata()
        if not metadata.config_schema:
            return True

        # Basic validation: check required fields exist
        for key, schema in metadata.config_schema.items():
            if schema.get('required', False) and key not in self.config:
                self.logger.error(f"Required configuration key '{key}' missing")
                return False

        return True

    def health_check(self) -> bool:
        """
        Check if plugin is healthy and ready to execute

        Override for custom health checks (e.g., check if external
        service is accessible).

        Returns:
            True if plugin is healthy
        """
        return self.status == PluginStatus.INITIALIZED

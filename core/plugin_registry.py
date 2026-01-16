"""
Plugin Registry

Central registry for plugin management. Handles:
- Plugin registration and discovery
- Plugin lifecycle management
- Command-to-plugin routing
"""

from typing import Dict, List, Type, Optional
from core.plugin_base import BasePlugin, PluginStatus, PluginMetadata
import logging


class PluginRegistry:
    """Central registry for plugin management"""

    def __init__(self, logger: logging.Logger):
        """
        Initialize plugin registry

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self._plugins: Dict[str, BasePlugin] = {}
        self._command_map: Dict[str, str] = {}  # command -> plugin_name

    def register(self, plugin_class: Type[BasePlugin], config: Dict[str, any]) -> bool:
        """
        Register a plugin class with configuration

        Workflow:
        1. Instantiate plugin
        2. Validate configuration
        3. Initialize plugin
        4. Register command mappings
        5. Mark as initialized

        Args:
            plugin_class: Plugin class to register (must inherit from BasePlugin)
            config: Plugin-specific configuration

        Returns:
            True on successful registration
        """
        try:
            # Instantiate plugin
            plugin = plugin_class(config, self.logger)
            metadata = plugin.get_metadata()

            # Check for name conflicts
            if metadata.name in self._plugins:
                self.logger.error(f"Plugin {metadata.name} already registered")
                return False

            self.logger.info(f"Registering plugin: {metadata.name} v{metadata.version}")

            # Validate configuration
            if not plugin.validate_config():
                self.logger.error(f"Plugin {metadata.name} config validation failed")
                plugin.status = PluginStatus.FAILED
                return False

            # Initialize plugin
            plugin.status = PluginStatus.LOADED
            if not plugin.initialize():
                self.logger.error(f"Plugin {metadata.name} initialization failed")
                plugin.status = PluginStatus.FAILED
                return False

            plugin.status = PluginStatus.INITIALIZED
            self._plugins[metadata.name] = plugin

            # Register commands
            for cmd in metadata.commands:
                if cmd in self._command_map:
                    self.logger.warning(
                        f"Command '{cmd}' already mapped to {self._command_map[cmd]}, "
                        f"overriding with {metadata.name}"
                    )
                self._command_map[cmd] = metadata.name
                self.logger.debug(f"  Registered command: {cmd}")

            self.logger.info(
                f"Plugin {metadata.name} registered successfully "
                f"({len(metadata.commands)} commands)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to register plugin: {e}", exc_info=True)
            return False

    def get_plugin_for_command(self, command: str) -> Optional[BasePlugin]:
        """
        Get the plugin that handles a specific command

        Args:
            command: Command name (e.g., 'download_movie')

        Returns:
            Plugin instance or None if no plugin handles this command
        """
        plugin_name = self._command_map.get(command)
        if not plugin_name:
            self.logger.warning(f"No plugin found for command: {command}")
            return None

        plugin = self._plugins.get(plugin_name)
        if not plugin:
            self.logger.error(
                f"Plugin {plugin_name} registered for command {command} but not found in registry"
            )
            return None

        return plugin

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get plugin by name

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def list_plugins(self) -> List[PluginMetadata]:
        """
        List all registered plugins

        Returns:
            List of plugin metadata
        """
        return [p.get_metadata() for p in self._plugins.values()]

    def list_commands(self) -> Dict[str, str]:
        """
        List all registered commands and their plugins

        Returns:
            Dictionary mapping command -> plugin_name
        """
        return self._command_map.copy()

    def get_plugin_status(self, name: str) -> Optional[PluginStatus]:
        """
        Get plugin status

        Args:
            name: Plugin name

        Returns:
            Plugin status or None if plugin not found
        """
        plugin = self._plugins.get(name)
        return plugin.status if plugin else None

    def health_check(self, name: str = None) -> Dict[str, bool]:
        """
        Perform health check on plugins

        Args:
            name: Specific plugin name (if None, checks all plugins)

        Returns:
            Dictionary mapping plugin_name -> health_status
        """
        results = {}

        if name:
            plugin = self._plugins.get(name)
            if plugin:
                results[name] = plugin.health_check()
            else:
                self.logger.warning(f"Plugin {name} not found for health check")
        else:
            for plugin_name, plugin in self._plugins.items():
                results[plugin_name] = plugin.health_check()

        return results

    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin and clean up resources

        Args:
            name: Plugin name

        Returns:
            True if unloaded successfully
        """
        plugin = self._plugins.get(name)
        if not plugin:
            self.logger.warning(f"Plugin {name} not found for unloading")
            return False

        try:
            self.logger.info(f"Unloading plugin: {name}")

            # Cleanup plugin
            plugin.cleanup()
            metadata = plugin.get_metadata()

            # Remove command mappings
            for cmd in metadata.commands:
                if self._command_map.get(cmd) == name:
                    del self._command_map[cmd]
                    self.logger.debug(f"  Unregistered command: {cmd}")

            # Remove from registry
            del self._plugins[name]
            plugin.status = PluginStatus.UNLOADED

            self.logger.info(f"Plugin {name} unloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error unloading plugin {name}: {e}", exc_info=True)
            return False

    def reload_plugin(self, plugin_class: Type[BasePlugin], config: Dict[str, any]) -> bool:
        """
        Reload a plugin (unload then register)

        Args:
            plugin_class: Plugin class
            config: Plugin configuration

        Returns:
            True if reloaded successfully
        """
        # Get plugin name by instantiating temporarily
        temp_plugin = plugin_class(config, self.logger)
        name = temp_plugin.get_metadata().name

        # Unload existing plugin if present
        if name in self._plugins:
            if not self.unload_plugin(name):
                self.logger.error(f"Failed to unload plugin {name} for reload")
                return False

        # Register new instance
        return self.register(plugin_class, config)

    def cleanup_all(self):
        """Cleanup all plugins"""
        self.logger.info("Cleaning up all plugins")

        for name in list(self._plugins.keys()):
            self.unload_plugin(name)

        self.logger.info("All plugins cleaned up")

    def get_plugin_count(self) -> int:
        """
        Get number of registered plugins

        Returns:
            Plugin count
        """
        return len(self._plugins)

    def get_command_count(self) -> int:
        """
        Get number of registered commands

        Returns:
            Command count
        """
        return len(self._command_map)

    def __repr__(self):
        return f"PluginRegistry(plugins={self.get_plugin_count()}, commands={self.get_command_count()})"

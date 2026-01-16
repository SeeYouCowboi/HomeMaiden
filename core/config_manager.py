"""
Configuration Manager

Manages application configuration from YAML files with support for:
- Multiple environments (development, production)
- Secrets management
- Environment variable substitution
- Hierarchical configuration access
"""

import yaml
import os
import re
from typing import Dict, Any, Optional
from pathlib import Path
import logging


class ConfigManager:
    """Manage application configuration from YAML files"""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger('ConfigManager')

    def load(self, env: str = "production") -> bool:
        """
        Load configuration files

        Configuration is loaded in this order (later overrides earlier):
        1. base.yaml - Base configuration
        2. {env}.yaml - Environment-specific overrides
        3. secrets.yaml - Sensitive credentials (optional)

        After loading, ${ENV_VAR} patterns are replaced with environment variables.

        Args:
            env: Environment name (development, production, etc.)

        Returns:
            True if configuration loaded successfully
        """
        try:
            # Load base config
            base_config = self._load_yaml("base.yaml")
            if not base_config:
                self.logger.error("Failed to load base.yaml")
                return False

            # Load environment-specific config
            env_config = self._load_yaml(f"{env}.yaml") or {}

            # Load secrets (optional)
            secrets = self._load_yaml("secrets.yaml") or {}

            # Merge configs (env overrides base, secrets override both)
            self.config = self._deep_merge(base_config, env_config)
            self.config = self._deep_merge(self.config, secrets)

            # Environment variable substitution
            self._substitute_env_vars()

            self.logger.info(f"Configuration loaded for environment: {env}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False

    def _load_yaml(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a single YAML file

        Args:
            filename: Name of YAML file to load

        Returns:
            Parsed YAML data or None if file doesn't exist
        """
        filepath = self.config_dir / filename
        if not filepath.exists():
            self.logger.warning(f"Configuration file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.logger.debug(f"Loaded configuration from {filepath}")
                return data
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file {filepath}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {e}")
            return None

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries

        Args:
            base: Base dictionary
            override: Dictionary with values to override

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def _substitute_env_vars(self):
        """
        Replace ${ENV_VAR} patterns with environment variables

        Recursively processes the entire configuration tree.
        If environment variable doesn't exist, keeps the original pattern.
        """
        def substitute(value):
            if isinstance(value, str):
                # Match ${VAR_NAME} pattern
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)

                for var_name in matches:
                    env_value = os.getenv(var_name)
                    if env_value is not None:
                        value = value.replace(f"${{{var_name}}}", env_value)
                    else:
                        self.logger.warning(f"Environment variable {var_name} not found")

                return value
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(item) for item in value]
            else:
                return value

        self.config = substitute(self.config)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation

        Examples:
            config.get("email.smtp.server")
            config.get("plugins.movie_download.radarr_url")

        Args:
            key_path: Dot-separated path to configuration value
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific plugin

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin configuration dictionary (empty if not found)
        """
        return self.get(f"plugins.{plugin_name}", {})

    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration dictionary

        Returns:
            Complete configuration
        """
        return self.config.copy()

    def reload(self, env: str = "production") -> bool:
        """
        Reload configuration

        Useful for applying configuration changes without restarting.

        Args:
            env: Environment name

        Returns:
            True if reload successful
        """
        self.config = {}
        return self.load(env)

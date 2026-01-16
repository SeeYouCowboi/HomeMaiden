"""
Test Script for Phase 1 & 2 Components

This script tests:
1. Configuration loading
2. Database initialization
3. Logger setup
4. Provider imports and initialization
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)

    try:
        # Core imports
        from core.config_manager import ConfigManager
        from core.database import Database
        from core.logger import setup_logging
        from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult
        from core.plugin_registry import PluginRegistry
        from core.providers import (
            EmailProvider, EmailMessage, IMAPSMTPProvider,
            LLMProvider, LLMResponse, OllamaProvider
        )

        print("[OK] All imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_config_manager():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("Testing ConfigManager...")
    print("=" * 60)

    try:
        from core.config_manager import ConfigManager

        config = ConfigManager(config_dir="config")

        # Test loading base config
        if config.load(env="development"):
            print("[OK] Configuration loaded successfully")

            # Test retrieving values
            app_name = config.get("system.app_name")
            print(f"  - App name: {app_name}")

            log_level = config.get("system.log_level")
            print(f"  - Log level: {log_level}")

            email_server = config.get("email.imap_server")
            print(f"  - Email server: {email_server}")

            # Test plugin config
            plugin_config = config.get_plugin_config("movie_download")
            print(f"  - Movie plugin config loaded: {bool(plugin_config)}")

            return True
        else:
            print("[FAIL] Configuration loading failed")
            return False

    except Exception as e:
        print(f"[FAIL] ConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("Testing Database...")
    print("=" * 60)

    try:
        from core.database import Database

        # Use test database
        db = Database(db_path="data/test_catnip.db")

        if db.connect():
            print("[OK] Database connected and schema initialized")

            # Test command logging
            cmd_id = db.log_command(
                sender="test@example.com",
                subject="Test Command",
                command_action="test_action",
                command_data={"test": "data"},
                plugin_name="test_plugin",
                success=True,
                result_message="Test successful"
            )
            print(f"  - Test command logged with ID: {cmd_id}")

            # Test retrieving history
            history = db.get_command_history(limit=5)
            print(f"  - Retrieved {len(history)} command history records")

            db.close()
            return True
        else:
            print("[FAIL] Database connection failed")
            return False

    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger():
    """Test logger setup"""
    print("\n" + "=" * 60)
    print("Testing Logger...")
    print("=" * 60)

    try:
        from core.logger import setup_logging, get_logger

        # Setup logger
        main_logger = setup_logging(
            log_dir="logs",
            log_level="INFO",
            app_name="HomeCentralMaid"
        )

        print("[OK] Logger initialized")

        # Test logging
        main_logger.info("This is a test info message")
        main_logger.debug("This is a test debug message (should not appear in INFO level)")

        # Get module logger
        module_logger = get_logger("TestModule")
        module_logger.info("Module logger working")

        print("[OK] Logging working correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_providers():
    """Test provider initialization"""
    print("\n" + "=" * 60)
    print("Testing Providers...")
    print("=" * 60)

    try:
        from core.providers import IMAPSMTPProvider, OllamaProvider
        from core.logger import get_logger
        import logging

        logger = get_logger("ProviderTest")

        # Test email provider (without actually connecting)
        print("\n  Testing Email Provider...")
        email_config = {
            'imap_server': 'imap.qq.com',
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 587,
            'username': 'test@qq.com',
            'password': 'test_password',
            'allowed_senders': ['allowed@example.com']
        }
        email_provider = IMAPSMTPProvider(email_config, logger)
        print("  [OK] Email provider initialized")

        # Test LLM provider (without actually calling)
        print("\n  Testing LLM Provider...")
        llm_config = {
            'model': 'qwen3:8b',
            'system_prompt': 'Test prompt'
        }
        llm_provider = OllamaProvider(llm_config, logger)
        print("  [OK] LLM provider initialized")
        print(f"    - Model: {llm_provider.get_model_name()}")

        return True

    except Exception as e:
        print(f"[FAIL] Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plugin_system():
    """Test plugin base classes"""
    print("\n" + "=" * 60)
    print("Testing Plugin System...")
    print("=" * 60)

    try:
        from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult
        from core.plugin_registry import PluginRegistry
        from core.logger import get_logger
        from datetime import datetime

        logger = get_logger("PluginTest")

        # Create a simple test plugin
        class TestPlugin(BasePlugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_plugin",
                    version="1.0.0",
                    author="Test",
                    description="Test plugin",
                    commands=["test_command"]
                )

            def initialize(self):
                self.logger.info("Test plugin initialized")
                return True

            def execute(self, context):
                return PluginResult(
                    success=True,
                    message="Test command executed"
                )

            def cleanup(self):
                self.logger.info("Test plugin cleaned up")

        # Test plugin registry
        registry = PluginRegistry(logger)
        print("[OK] Plugin registry created")

        # Register test plugin
        if registry.register(TestPlugin, {"test": "config"}):
            print("[OK] Test plugin registered successfully")

            # Test command lookup
            plugin = registry.get_plugin_for_command("test_command")
            if plugin:
                print("[OK] Plugin found for command")

                # Test execution
                context = CommandContext(
                    sender="test@example.com",
                    subject="Test",
                    body="Test body",
                    parsed_command={"action": "test_command"},
                    timestamp=datetime.now(),
                    config={},
                    logger=logger
                )
                result = plugin.execute(context)
                print(f"[OK] Plugin executed: {result}")

            # Cleanup
            registry.cleanup_all()
            print("[OK] Plugin cleaned up")

            return True
        else:
            print("[FAIL] Plugin registration failed")
            return False

    except Exception as e:
        print(f"[FAIL] Plugin system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" + "=" * 58 + "=")
    print("" + " HomeCentralMaid Component Test Suite".center(58) + "")
    print("=" + "=" * 58 + "╝")
    print()

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("ConfigManager", test_config_manager()))
    results.append(("Database", test_database()))
    results.append(("Logger", test_logger()))
    results.append(("Providers", test_providers()))
    results.append(("Plugin System", test_plugin_system()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{name:.<40} {status}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] All tests passed! Phase 1 & 2 components are ready.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

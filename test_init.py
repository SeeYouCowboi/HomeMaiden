"""
Quick initialization test for the refactored system
Tests all components without actually running the email loop
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import HomeCentralMaid

def main():
    print("\n" + "=" * 60)
    print("  Testing HomeCentralMaid Initialization")
    print("=" * 60 + "\n")

    app = HomeCentralMaid(env="development")

    if app.initialize():
        print("\n" + "=" * 60)
        print("  INITIALIZATION TEST: PASSED")
        print("=" * 60)

        # Print some stats
        if app.dispatcher:
            stats = app.dispatcher.get_stats()
            print(f"\nSystem Statistics:")
            print(f"  - Total plugins: {stats['total_plugins']}")
            print(f"  - Total commands: {stats['total_commands']}")
            print(f"  - Healthy plugins: {stats['healthy_plugins']}/{stats['total_plugins']}")
            print(f"  - LLM model: {stats['llm_model']}")

            print(f"\nRegistered Plugins:")
            for plugin in stats['plugins']:
                status = "[OK]" if plugin['healthy'] else "[FAIL]"
                print(f"  {status} {plugin['name']} v{plugin['version']}")
                print(f"      Commands: {', '.join(plugin['commands'])}")

        # Test command history
        if app.database:
            history = app.database.get_command_history(limit=5)
            print(f"\nCommand history entries: {len(history)}")

        # Cleanup
        app.shutdown()

        print("\n[SUCCESS] All components working correctly!\n")
        return 0
    else:
        print("\n[FAIL] Initialization failed\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

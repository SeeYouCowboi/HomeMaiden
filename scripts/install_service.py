"""
Install HomeCentralMaid as a Windows Service

This script installs HomeCentralMaid as a Windows service using NSSM
(Non-Sucking Service Manager).

Requirements:
- NSSM (download from https://nssm.cc/)
- Administrator privileges

Usage:
    python scripts/install_service.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Configuration
SERVICE_NAME = "HomeCentralMaid"
SERVICE_DISPLAY_NAME = "HomeCentralMaid - Catnip 家庭女仆系统"
SERVICE_DESCRIPTION = "邮件驱动的智能家庭管理系统"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"


def check_admin():
    """Check if running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def find_nssm():
    """Find NSSM executable"""
    # Check if nssm is in PATH
    try:
        result = subprocess.run(["nssm", "version"],
                              capture_output=True,
                              text=True)
        if result.returncode == 0:
            return "nssm"
    except FileNotFoundError:
        pass

    # Check common locations
    common_paths = [
        r"C:\Program Files\nssm\nssm.exe",
        r"C:\Program Files (x86)\nssm\nssm.exe",
        PROJECT_ROOT / "tools" / "nssm.exe",
    ]

    for path in common_paths:
        if Path(path).exists():
            return str(path)

    return None


def install_service(nssm_path):
    """Install service using NSSM"""
    print(f"Installing service: {SERVICE_NAME}")
    print(f"Python: {PYTHON_EXE}")
    print(f"Script: {MAIN_SCRIPT}")

    # Create directories
    LOG_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    # Install service
    cmd = [
        nssm_path,
        "install",
        SERVICE_NAME,
        str(PYTHON_EXE),
        str(MAIN_SCRIPT),
        "production"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Failed to install service: {result.stderr}")
        return False

    print("[OK] Service installed")

    # Configure service
    configs = [
        ("set", SERVICE_NAME, "DisplayName", SERVICE_DISPLAY_NAME),
        ("set", SERVICE_NAME, "Description", SERVICE_DESCRIPTION),
        ("set", SERVICE_NAME, "Start", "SERVICE_AUTO_START"),
        ("set", SERVICE_NAME, "AppDirectory", str(PROJECT_ROOT)),
        ("set", SERVICE_NAME, "AppStdout", str(LOG_DIR / "service_stdout.log")),
        ("set", SERVICE_NAME, "AppStderr", str(LOG_DIR / "service_stderr.log")),
        ("set", SERVICE_NAME, "AppRotateFiles", "1"),
        ("set", SERVICE_NAME, "AppRotateOnline", "1"),
        ("set", SERVICE_NAME, "AppRotateBytes", "10485760"),  # 10MB
    ]

    for config in configs:
        cmd = [nssm_path] + list(config)
        subprocess.run(cmd, capture_output=True)

    print("[OK] Service configured")
    return True


def main():
    print("\n" + "=" * 60)
    print("  HomeCentralMaid Service Installer")
    print("=" * 60 + "\n")

    # Check admin privileges
    if not check_admin():
        print("[ERROR] This script requires administrator privileges")
        print("Please run as administrator")
        return 1

    # Check if Python exists
    if not PYTHON_EXE.exists():
        print(f"[ERROR] Python not found: {PYTHON_EXE}")
        print("Please ensure virtual environment is set up")
        return 1

    # Check if main script exists
    if not MAIN_SCRIPT.exists():
        print(f"[ERROR] Main script not found: {MAIN_SCRIPT}")
        return 1

    # Find NSSM
    nssm_path = find_nssm()
    if not nssm_path:
        print("[ERROR] NSSM not found")
        print("\nPlease install NSSM:")
        print("1. Download from https://nssm.cc/download")
        print("2. Extract to C:\\Program Files\\nssm\\")
        print("3. Or add to PATH")
        return 1

    print(f"[OK] Found NSSM: {nssm_path}")

    # Check if service already exists
    result = subprocess.run(
        [nssm_path, "status", SERVICE_NAME],
        capture_output=True
    )

    if result.returncode == 0:
        print(f"\n[WARNING] Service '{SERVICE_NAME}' already exists")
        response = input("Remove existing service? (y/n): ")
        if response.lower() == 'y':
            print("Stopping service...")
            subprocess.run([nssm_path, "stop", SERVICE_NAME], capture_output=True)
            print("Removing service...")
            subprocess.run([nssm_path, "remove", SERVICE_NAME, "confirm"], capture_output=True)
            print("[OK] Existing service removed")
        else:
            print("Installation cancelled")
            return 1

    # Install service
    if install_service(nssm_path):
        print("\n" + "=" * 60)
        print("[SUCCESS] Service installed successfully!")
        print("=" * 60)
        print(f"\nService Name: {SERVICE_NAME}")
        print(f"Display Name: {SERVICE_DISPLAY_NAME}")
        print("\nManagement commands:")
        print(f"  Start:   nssm start {SERVICE_NAME}")
        print(f"  Stop:    nssm stop {SERVICE_NAME}")
        print(f"  Restart: nssm restart {SERVICE_NAME}")
        print(f"  Status:  nssm status {SERVICE_NAME}")
        print(f"  Remove:  nssm remove {SERVICE_NAME} confirm")
        print("\nOr use Windows Services Manager (services.msc)")
        print("\nLogs:")
        print(f"  Application: {LOG_DIR / 'homecentralmaid_YYYYMMDD.log'}")
        print(f"  Service:     {LOG_DIR / 'service_stdout.log'}")
        print(f"  Errors:      {LOG_DIR / 'service_stderr.log'}")

        # Ask to start service
        print()
        response = input("Start service now? (y/n): ")
        if response.lower() == 'y':
            result = subprocess.run([nssm_path, "start", SERVICE_NAME],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] Service started")
            else:
                print(f"[ERROR] Failed to start service: {result.stderr}")

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

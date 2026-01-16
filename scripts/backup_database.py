"""
Database Backup Script

Backs up the HomeCentralMaid database with rotation.

Features:
- Automatic backup with timestamp
- Configurable retention (keep last N backups)
- Compression support
- Backup verification

Usage:
    python scripts/backup_database.py
    python scripts/backup_database.py --compress
    python scripts/backup_database.py --keep 14
"""

import sys
import shutil
import gzip
from pathlib import Path
from datetime import datetime
import argparse
import sqlite3


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"


def create_backup(db_path: Path, compress: bool = False) -> Path:
    """
    Create database backup

    Args:
        db_path: Path to database file
        compress: Whether to compress backup

    Returns:
        Path to backup file
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = db_path.stem
    backup_name = f"{db_name}_backup_{timestamp}.db"

    if compress:
        backup_name += ".gz"

    backup_path = BACKUP_DIR / backup_name

    print(f"Creating backup: {backup_path.name}")

    try:
        if compress:
            # Compressed backup
            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Direct copy
            shutil.copy2(db_path, backup_path)

        # Get file size
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        print(f"  Size: {size_mb:.2f} MB")

        return backup_path

    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        if backup_path.exists():
            backup_path.unlink()
        raise


def verify_backup(backup_path: Path, compress: bool = False) -> bool:
    """
    Verify backup integrity

    Args:
        backup_path: Path to backup file
        compress: Whether backup is compressed

    Returns:
        True if backup is valid
    """
    print("Verifying backup...")

    try:
        if compress:
            # Decompress to temporary file for verification
            temp_path = backup_path.with_suffix('')
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Verify decompressed database
            conn = sqlite3.connect(temp_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()

            # Clean up temp file
            temp_path.unlink()
        else:
            # Verify directly
            conn = sqlite3.connect(backup_path)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()

            if result[0] != 'ok':
                print(f"[ERROR] Database integrity check failed: {result[0]}")
                return False

        print("  [OK] Backup verified")
        return True

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


def rotate_backups(keep: int = 7):
    """
    Remove old backups, keeping only the most recent N

    Args:
        keep: Number of backups to keep
    """
    if not BACKUP_DIR.exists():
        return

    # Get all backup files
    backups = sorted(
        BACKUP_DIR.glob("*_backup_*.db*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if len(backups) <= keep:
        print(f"Found {len(backups)} backup(s), no rotation needed")
        return

    # Remove old backups
    removed_count = 0
    for backup in backups[keep:]:
        print(f"Removing old backup: {backup.name}")
        backup.unlink()
        removed_count += 1

    print(f"Removed {removed_count} old backup(s)")
    print(f"Keeping {keep} most recent backup(s)")


def list_backups():
    """List all available backups"""
    if not BACKUP_DIR.exists():
        print("No backups found")
        return

    backups = sorted(
        BACKUP_DIR.glob("*_backup_*.db*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not backups:
        print("No backups found")
        return

    print(f"\nFound {len(backups)} backup(s):\n")
    print(f"{'Filename':<50} {'Size':>10} {'Date':>20}")
    print("-" * 82)

    for backup in backups:
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{backup.name:<50} {size_mb:>8.2f}MB {mtime.strftime('%Y-%m-%d %H:%M:%S'):>20}")


def restore_backup(backup_path: Path, target_path: Path):
    """
    Restore database from backup

    Args:
        backup_path: Path to backup file
        target_path: Path to restore to
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    # Backup current database if it exists
    if target_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = target_path.with_name(f"{target_path.stem}_pre_restore_{timestamp}.db")
        print(f"Backing up current database to: {current_backup.name}")
        shutil.copy2(target_path, current_backup)

    print(f"Restoring from: {backup_path.name}")

    try:
        if backup_path.suffix == '.gz':
            # Decompress
            with gzip.open(backup_path, 'rb') as f_in:
                with open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Direct copy
            shutil.copy2(backup_path, target_path)

        # Verify restored database
        conn = sqlite3.connect(target_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if result[0] != 'ok':
            raise Exception(f"Restored database integrity check failed: {result[0]}")

        print("[OK] Database restored successfully")

    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="HomeCentralMaid Database Backup Tool"
    )
    parser.add_argument(
        '--compress', '-c',
        action='store_true',
        help='Compress backup with gzip'
    )
    parser.add_argument(
        '--keep', '-k',
        type=int,
        default=7,
        help='Number of backups to keep (default: 7)'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='catnip.db',
        help='Database filename (default: catnip.db)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available backups'
    )
    parser.add_argument(
        '--restore', '-r',
        type=str,
        help='Restore from backup file'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  HomeCentralMaid Database Backup Tool")
    print("=" * 60 + "\n")

    # List backups
    if args.list:
        list_backups()
        return 0

    # Restore backup
    if args.restore:
        backup_path = BACKUP_DIR / args.restore
        target_path = DATA_DIR / args.db

        response = input(f"Restore {args.restore} to {args.db}? (y/n): ")
        if response.lower() == 'y':
            try:
                restore_backup(backup_path, target_path)
                return 0
            except Exception as e:
                print(f"\n[ERROR] {e}")
                return 1
        else:
            print("Restore cancelled")
            return 0

    # Create backup
    db_path = DATA_DIR / args.db

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print("\nAvailable databases:")
        for db in DATA_DIR.glob("*.db"):
            print(f"  - {db.name}")
        return 1

    try:
        # Create backup
        backup_path = create_backup(db_path, compress=args.compress)

        # Verify backup
        if verify_backup(backup_path, compress=args.compress):
            print("[OK] Backup created successfully")

            # Rotate old backups
            print()
            rotate_backups(keep=args.keep)

            print("\n" + "=" * 60)
            print("[SUCCESS] Backup complete")
            print("=" * 60)
            print(f"\nBackup location: {backup_path}")
            print(f"Backup directory: {BACKUP_DIR}")

            return 0
        else:
            print("[ERROR] Backup verification failed")
            return 1

    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

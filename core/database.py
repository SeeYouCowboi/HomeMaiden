"""
Database Layer

Provides SQLite-based persistence for:
- Command history (audit trail)
- Task queue (background jobs)
- User preferences
- Plugin state
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging


class Database:
    """SQLite database manager for persistence"""

    def __init__(self, db_path: str = "data/catnip.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('Database')
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> bool:
        """
        Establish database connection and initialize schema

        Returns:
            True if connection successful
        """
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
            self._init_schema()
            self.logger.info(f"Database connected: {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False

    def _init_schema(self):
        """Create tables if they don't exist"""
        cursor = self.conn.cursor()

        # Command history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                subject TEXT,
                command_action TEXT NOT NULL,
                command_data TEXT NOT NULL,
                plugin_name TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                result_message TEXT,
                result_data TEXT,
                execution_time_ms INTEGER
            )
        ''')

        # Create indexes for command_history
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cmd_history_timestamp
            ON command_history(timestamp DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cmd_history_sender
            ON command_history(sender)
        ''')

        # Task queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                task_type TEXT NOT NULL,
                task_data TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 100,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT,
                scheduled_for TEXT,
                completed_at TEXT
            )
        ''')

        # Create indexes for task_queue
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_status
            ON task_queue(status, priority, created_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_scheduled
            ON task_queue(scheduled_for)
        ''')

        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_email TEXT PRIMARY KEY,
                preferences TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Plugin state table (for plugins to store data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugin_state (
                plugin_name TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (plugin_name, key)
            )
        ''')

        # Create index for plugin_state
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_plugin_state_name
            ON plugin_state(plugin_name)
        ''')

        self.conn.commit()
        self.logger.info("Database schema initialized")

    # =============================================================================
    # Command History Methods
    # =============================================================================

    def log_command(
        self,
        sender: str,
        subject: str,
        command_action: str,
        command_data: Dict[str, Any],
        plugin_name: str,
        success: bool,
        result_message: str,
        result_data: Dict[str, Any] = None,
        execution_time_ms: int = 0
    ) -> int:
        """
        Log command execution to history

        Args:
            sender: Email address of sender
            subject: Email subject
            command_action: Action performed (e.g., 'download_movie')
            command_data: Command parameters as dictionary
            plugin_name: Name of plugin that executed command
            success: Whether execution succeeded
            result_message: Result message
            result_data: Additional result data
            execution_time_ms: Execution time in milliseconds

        Returns:
            ID of inserted record
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO command_history (
                timestamp, sender, subject, command_action, command_data,
                plugin_name, success, result_message, result_data, execution_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            sender,
            subject,
            command_action,
            json.dumps(command_data, ensure_ascii=False),
            plugin_name,
            success,
            result_message,
            json.dumps(result_data or {}, ensure_ascii=False),
            execution_time_ms
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_command_history(
        self,
        limit: int = 100,
        sender: str = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve command history

        Args:
            limit: Maximum number of records to return
            sender: Filter by sender email (optional)
            success_only: Only return successful commands

        Returns:
            List of command history records
        """
        cursor = self.conn.cursor()

        query = 'SELECT * FROM command_history WHERE 1=1'
        params = []

        if sender:
            query += ' AND sender = ?'
            params.append(sender)

        if success_only:
            query += ' AND success = 1'

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dictionaries and parse JSON fields
        results = []
        for row in rows:
            record = dict(row)
            record['command_data'] = json.loads(record['command_data'])
            record['result_data'] = json.loads(record['result_data'])
            results.append(record)

        return results

    # =============================================================================
    # Task Queue Methods
    # =============================================================================

    def enqueue_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 100,
        scheduled_for: Optional[datetime] = None,
        max_retries: int = 3
    ) -> int:
        """
        Add task to queue

        Args:
            task_type: Type of task
            task_data: Task data as dictionary
            priority: Priority (lower = higher priority)
            scheduled_for: When to execute task (None = immediately)
            max_retries: Maximum retry attempts

        Returns:
            Task ID
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO task_queue (
                created_at, updated_at, task_type, task_data, status,
                priority, max_retries, scheduled_for
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now,
            now,
            task_type,
            json.dumps(task_data, ensure_ascii=False),
            'pending',
            priority,
            max_retries,
            scheduled_for.isoformat() if scheduled_for else None
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending tasks ready for execution

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of pending tasks
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute('''
            SELECT * FROM task_queue
            WHERE status = 'pending'
            AND (scheduled_for IS NULL OR scheduled_for <= ?)
            ORDER BY priority ASC, created_at ASC
            LIMIT ?
        ''', (now, limit))

        rows = cursor.fetchall()
        results = []
        for row in rows:
            record = dict(row)
            record['task_data'] = json.loads(record['task_data'])
            results.append(record)

        return results

    def update_task_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ):
        """
        Update task status

        Args:
            task_id: Task ID
            status: New status (pending, running, completed, failed, cancelled)
            error_message: Error message if failed
            increment_retry: Increment retry count
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        if increment_retry:
            cursor.execute('''
                UPDATE task_queue
                SET status = ?, updated_at = ?, error_message = ?,
                    retry_count = retry_count + 1,
                    completed_at = CASE WHEN ? IN ('completed', 'failed', 'cancelled') THEN ? ELSE NULL END
                WHERE id = ?
            ''', (status, now, error_message, status, now, task_id))
        else:
            cursor.execute('''
                UPDATE task_queue
                SET status = ?, updated_at = ?, error_message = ?,
                    completed_at = CASE WHEN ? IN ('completed', 'failed', 'cancelled') THEN ? ELSE NULL END
                WHERE id = ?
            ''', (status, now, error_message, status, now, task_id))

        self.conn.commit()

    # =============================================================================
    # User Preferences Methods
    # =============================================================================

    def save_user_preferences(self, user_email: str, preferences: Dict[str, Any]):
        """
        Save user preferences

        Args:
            user_email: User email address
            preferences: Preferences dictionary
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_email, preferences, created_at, updated_at)
            VALUES (?, ?, COALESCE((SELECT created_at FROM user_preferences WHERE user_email = ?), ?), ?)
        ''', (
            user_email,
            json.dumps(preferences, ensure_ascii=False),
            user_email,
            now,
            now
        ))
        self.conn.commit()

    def get_user_preferences(self, user_email: str) -> Dict[str, Any]:
        """
        Get user preferences

        Args:
            user_email: User email address

        Returns:
            Preferences dictionary (empty if not found)
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT preferences FROM user_preferences WHERE user_email = ?', (user_email,))
        row = cursor.fetchone()

        if row:
            return json.loads(row['preferences'])
        return {}

    # =============================================================================
    # Plugin State Methods
    # =============================================================================

    def set_plugin_state(self, plugin_name: str, key: str, value: Any):
        """
        Set plugin state value

        Args:
            plugin_name: Plugin name
            key: State key
            value: State value (will be JSON serialized)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO plugin_state (plugin_name, key, value, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (
            plugin_name,
            key,
            json.dumps(value, ensure_ascii=False),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def get_plugin_state(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """
        Get plugin state value

        Args:
            plugin_name: Plugin name
            key: State key
            default: Default value if not found

        Returns:
            State value or default
        """
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT value FROM plugin_state WHERE plugin_name = ? AND key = ?',
            (plugin_name, key)
        )
        row = cursor.fetchone()

        if row:
            return json.loads(row['value'])
        return default

    def delete_plugin_state(self, plugin_name: str, key: str = None):
        """
        Delete plugin state

        Args:
            plugin_name: Plugin name
            key: State key (if None, deletes all state for plugin)
        """
        cursor = self.conn.cursor()

        if key:
            cursor.execute(
                'DELETE FROM plugin_state WHERE plugin_name = ? AND key = ?',
                (plugin_name, key)
            )
        else:
            cursor.execute(
                'DELETE FROM plugin_state WHERE plugin_name = ?',
                (plugin_name,)
            )

        self.conn.commit()

    # =============================================================================
    # Utility Methods
    # =============================================================================

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")

    def vacuum(self):
        """Optimize database (reclaim space, rebuild indexes)"""
        if self.conn:
            self.conn.execute('VACUUM')
            self.logger.info("Database vacuumed")

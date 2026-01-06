"""
Database models and operations for SOC Agent Automation.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from config.settings import Config


class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_file: str = None):
        self.db_file = db_file or Config.DATABASE_FILE
        self._initialized = False
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_initialized(self):
        """Ensure database is initialized before operations"""
        if not self._initialized:
            self.init_db()
            self._initialized = True
    
    def init_db(self) -> None:
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT DEFAULT 'default'
                )
            """)
            
            # Tools log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tools_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    usage TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT DEFAULT 'default'
                )
            """)
            
            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proactive_enabled INTEGER DEFAULT 1,
                    proactive_interval INTEGER DEFAULT 60,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Proactive agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proactive_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    prompt TEXT NOT NULL,
                    interval_minutes INTEGER NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    last_run TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Initialize default preferences if not exists
            cursor.execute("SELECT COUNT(*) FROM preferences")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO preferences (proactive_enabled, proactive_interval, created_at, updated_at) VALUES (?,?,?,?)",
                    (1, Config.DEFAULT_PROACTIVE_INTERVAL, now, now)
                )
            
            conn.commit()
            self._initialized = True
    
    def save_message(self, role: str, content: str, session_id: str = "default") -> int:
        """Save a chat message"""
        self._ensure_initialized()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (role, content, timestamp, session_id) VALUES (?,?,?,?)",
                (role, content, datetime.now().isoformat(), session_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def save_tool_log(self, tool_name: str, usage: str, session_id: str = "default") -> int:
        """Save a tool usage log"""
        self._ensure_initialized()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tools_log (tool_name, usage, timestamp, session_id) VALUES (?,?,?,?)",
                (tool_name, usage, datetime.now().isoformat(), session_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_all_messages(self, session_id: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get all messages, optionally filtered by session"""
        self._ensure_initialized()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT role, content, timestamp FROM messages"
            params = []
            
            if session_id:
                query += " WHERE session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY id"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {"role": row[0], "content": row[1], "timestamp": row[2]} 
                for row in rows
            ]
    
    def get_all_tool_logs(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get all tool logs, optionally filtered by session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT tool_name, usage, timestamp FROM tools_log"
            params = []
            
            if session_id:
                query += " WHERE session_id = ?"
                params.append(session_id)
                
            query += " ORDER BY id"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {"tool_name": row[0], "usage": row[1], "timestamp": row[2]}
                for row in rows
            ]
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT proactive_enabled, proactive_interval FROM preferences ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            
            if row:
                return {"enabled": bool(row[0]), "interval": row[1]}
            else:
                # Return defaults if no preferences found
                return {"enabled": True, "interval": Config.DEFAULT_PROACTIVE_INTERVAL}
    
    def update_user_preferences(self, enabled: bool, interval: int) -> None:
        """Update user preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "UPDATE preferences SET proactive_enabled=?, proactive_interval=?, updated_at=? WHERE id=1",
                (int(enabled), interval, now)
            )
            conn.commit()
    
    def save_proactive_agent(self, name: str, prompt: str, interval_minutes: int) -> int:
        """Save or update a proactive agent configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Try to update existing agent first
            cursor.execute(
                "UPDATE proactive_agents SET prompt=?, interval_minutes=?, updated_at=? WHERE name=?",
                (prompt, interval_minutes, now, name)
            )
            
            if cursor.rowcount == 0:
                # Insert new agent if update didn't affect any rows
                cursor.execute(
                    "INSERT INTO proactive_agents (name, prompt, interval_minutes, created_at, updated_at) VALUES (?,?,?,?,?)",
                    (name, prompt, interval_minutes, now, now)
                )
            
            conn.commit()
            return cursor.lastrowid
    
    def get_proactive_agents(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get proactive agent configurations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT name, prompt, interval_minutes, enabled, last_run FROM proactive_agents"
            if enabled_only:
                query += " WHERE enabled = 1"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [
                {
                    "name": row[0],
                    "prompt": row[1], 
                    "interval_minutes": row[2],
                    "enabled": bool(row[3]),
                    "last_run": row[4]
                }
                for row in rows
            ]
    
    def update_proactive_agent_last_run(self, name: str) -> None:
        """Update last run timestamp for a proactive agent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE proactive_agents SET last_run=? WHERE name=?",
                (datetime.now().isoformat(), name)
            )
            conn.commit()
    
    def delete_proactive_agent(self, name: str) -> None:
        """Delete a proactive agent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proactive_agents WHERE name=?", (name,))
            conn.commit()


# Global database instance
_db = DatabaseManager()


# Legacy functions for backward compatibility
def init_db():
    """Initialize database (legacy function)"""
    _db.init_db()


def save_message(role: str, content: str):
    """Save message (legacy function)"""
    _db.save_message(role, content)


def save_tool_log(tool_name: str, usage: str):
    """Save tool log (legacy function)"""
    _db.save_tool_log(tool_name, usage)


def get_all_messages():
    """Get all messages (legacy function)"""
    return _db.get_all_messages()


def get_all_tool_logs():
    """Get all tool logs (legacy function)"""
    logs = _db.get_all_tool_logs()
    return [(log["tool_name"], log["usage"], log["timestamp"]) for log in logs]


def get_user_preferences():
    """Get user preferences (legacy function)"""
    return _db.get_user_preferences()


def update_user_preferences(enabled: bool, interval: int):
    """Update user preferences (legacy function)"""
    _db.update_user_preferences(enabled, interval)
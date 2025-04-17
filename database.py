# database.py (New File)
import sqlite3
import bcrypt
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DATABASE_NAME = "chatbot.db"

class DatabaseManager:
    def __init__(self):
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    expires_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Rate limits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    request_count INTEGER DEFAULT 0,
                    last_request DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

    # User management methods
    def create_user(self, username, password):
        with self._get_connection() as conn:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            ''', (username, hashed))
            return cursor.lastrowid

    def verify_user(self, username, password):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, password_hash FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            if result and bcrypt.checkpw(password.encode(), result[1]):
                return result[0]
            return None

    # Session management methods
    def create_session(self, user_id, session_duration=3600):
        session_id = os.urandom(16).hex()
        expires_at = datetime.now() + timedelta(seconds=session_duration)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, expires_at)
                VALUES (?, ?, ?)
            ''', (session_id, user_id, expires_at))
            return session_id

    def validate_session(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, expires_at FROM sessions WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            if result and datetime.now() < datetime.fromisoformat(result[1]):
                return result[0]
            return None

    # Rate limiting methods
    def check_rate_limit(self, user_id, limit=10, window=60):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT request_count, last_request 
                FROM rate_limits 
                WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            
            now = datetime.now()
            if not result or (now - datetime.fromisoformat(result[1]) > timedelta(seconds=window)):
                cursor.execute('''
                    REPLACE INTO rate_limits (user_id, request_count, last_request)
                    VALUES (?, 1, ?)
                ''', (user_id, now))
                conn.commit()
                return True
            elif result[0] < limit:
                cursor.execute('''
                    UPDATE rate_limits 
                    SET request_count = request_count + 1, last_request = ?
                    WHERE user_id = ?
                ''', (now, user_id))
                conn.commit()
                return True
            return False

    # Chat history methods
    def save_message(self, user_id, role, content):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (user_id, role, content)
                VALUES (?, ?, ?)
            ''', (user_id, role, content))
            conn.commit()

    def get_history(self, user_id, limit=100):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
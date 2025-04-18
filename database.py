# database.py
import sqlite3
import bcrypt
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

DATABASE_NAME = "chatbot.db"

class DatabaseManager:
    def __init__(self):
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
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
            
            # Chat history table - updated schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Conversation metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_favorite BOOLEAN DEFAULT 0,
                    tags TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Recent queries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recent_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    conversation_id TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                )
            ''')
            
            # Favorites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
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

    # Conversation management methods
    def create_conversation(self, user_id, title="New Conversation"):
        conversation_id = os.urandom(8).hex()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (conversation_id, user_id, title)
                VALUES (?, ?, ?)
            ''', (conversation_id, user_id, title))
            conn.commit()
            return conversation_id

    def update_conversation_title(self, conversation_id, new_title):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET title = ?, last_updated = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
            ''', (new_title, conversation_id))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_favorite_conversation(self, conversation_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET is_favorite = NOT is_favorite,
                    last_updated = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
            ''', (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_user_conversations(self, user_id, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT conversation_id, title, last_updated, is_favorite
                FROM conversations
                WHERE user_id = ?
                ORDER BY last_updated DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_favorite_conversations(self, user_id, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT conversation_id, title, last_updated
                FROM conversations
                WHERE user_id = ? AND is_favorite = 1
                ORDER BY last_updated DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Chat history methods
    def save_message(self, user_id, conversation_id, role, content):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (user_id, conversation_id, role, content)
                VALUES (?, ?, ?, ?)
            ''', (user_id, conversation_id, role, content))
            
            # Update the conversation's last_updated timestamp
            cursor.execute('''
                UPDATE conversations
                SET last_updated = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
            ''', (conversation_id,))
            
            # If this is a user message, add to recent queries
            if role == "user":
                # First check if it already exists
                cursor.execute('''
                    SELECT id FROM recent_queries
                    WHERE user_id = ? AND query = ?
                ''', (user_id, content))
                
                existing = cursor.fetchone()
                if existing:
                    # Update timestamp to move it to the top
                    cursor.execute('''
                        UPDATE recent_queries
                        SET timestamp = CURRENT_TIMESTAMP,
                            conversation_id = ?
                        WHERE id = ?
                    ''', (conversation_id, existing[0]))
                else:
                    # Insert new query, maintaining only the latest 10
                    cursor.execute('''
                        INSERT INTO recent_queries (user_id, query, conversation_id)
                        VALUES (?, ?, ?)
                    ''', (user_id, content, conversation_id))
                    
                    # Delete older queries if more than 10
                    cursor.execute('''
                        DELETE FROM recent_queries
                        WHERE user_id = ? AND id NOT IN (
                            SELECT id FROM recent_queries
                            WHERE user_id = ?
                            ORDER BY timestamp DESC
                            LIMIT 10
                        )
                    ''', (user_id, user_id))
            
            conn.commit()

    def get_conversation_history(self, conversation_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp
                FROM chat_history
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            ''', (conversation_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_conversations(self, user_id, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.conversation_id, c.title, c.last_updated, c.is_favorite,
                       (SELECT content FROM chat_history 
                        WHERE conversation_id = c.conversation_id AND role = 'user'
                        ORDER BY timestamp DESC LIMIT 1) as last_query
                FROM conversations c
                WHERE c.user_id = ?
                ORDER BY c.last_updated DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Recent queries methods
    def get_recent_queries(self, user_id, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT query, conversation_id
                FROM recent_queries
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Favorite queries methods
    def add_favorite_query(self, user_id, query):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if already exists
            cursor.execute('''
                SELECT id FROM favorite_queries
                WHERE user_id = ? AND query = ?
            ''', (user_id, query))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO favorite_queries (user_id, query)
                    VALUES (?, ?)
                ''', (user_id, query))
                conn.commit()
                return True
            return False

    def remove_favorite_query(self, user_id, query):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM favorite_queries
                WHERE user_id = ? AND query = ?
            ''', (user_id, query))
            conn.commit()
            return cursor.rowcount > 0

    def get_favorite_queries(self, user_id, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT query
                FROM favorite_queries
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            return [row[0] for row in cursor.fetchall()]

    # Statistics and aggregation methods
    def get_user_stats(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversations WHERE user_id = ?', (user_id,))
            stats['total_conversations'] = cursor.fetchone()[0]
            
            # Total messages
            cursor.execute('SELECT COUNT(*) FROM chat_history WHERE user_id = ?', (user_id,))
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Messages by role
            cursor.execute('''
                SELECT role, COUNT(*) 
                FROM chat_history 
                WHERE user_id = ? 
                GROUP BY role
            ''', (user_id,))
            stats['messages_by_role'] = dict(cursor.fetchall())
            
            # Recent activity (past 7 days)
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) 
                FROM chat_history 
                WHERE user_id = ? AND timestamp > datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', (user_id,))
            stats['recent_activity'] = dict(cursor.fetchall())
            
            return stats

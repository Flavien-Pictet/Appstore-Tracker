import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Optional, Dict
import config

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS apps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id TEXT UNIQUE NOT NULL,
                    app_name TEXT NOT NULL,
                    app_url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    revenue REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0,
                    FOREIGN KEY (app_id) REFERENCES apps(app_id)
                )
            ''')

            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_app_id ON rankings(app_id)
            ''')

            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON rankings(timestamp)
            ''')

            await db.commit()

    async def add_app(self, app_id: str, app_name: str, app_url: str, category: str):
        """Add or update an app"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO apps (app_id, app_name, app_url, category, last_checked)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(app_id) DO UPDATE SET
                    app_name = excluded.app_name,
                    app_url = excluded.app_url,
                    last_checked = excluded.last_checked
            ''', (app_id, app_name, app_url, category, datetime.now()))
            await db.commit()

    async def add_ranking(self, app_id: str, rank: int, revenue: Optional[float] = None):
        """Add a ranking entry"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO rankings (app_id, rank, revenue, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (app_id, rank, revenue, datetime.now()))
            await db.commit()

    async def is_new_in_top_100(self, app_id: str) -> bool:
        """Check if app is newly in top 100"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM rankings
                WHERE app_id = ? AND rank <= 100
            ''', (app_id,))
            row = await cursor.fetchone()
            count = row[0] if row else 0
            return count <= 1

    async def was_notified(self, app_id: str) -> bool:
        """Check if app entry was already notified"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT notified FROM rankings
                WHERE app_id = ? AND rank <= 100 AND notified = 1
                LIMIT 1
            ''', (app_id,))
            row = await cursor.fetchone()
            return row is not None

    async def mark_as_notified(self, app_id: str):
        """Mark the latest ranking as notified"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE rankings
                SET notified = 1
                WHERE app_id = ? AND id = (
                    SELECT id FROM rankings
                    WHERE app_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                )
            ''', (app_id, app_id))
            await db.commit()

    async def get_app_info(self, app_id: str) -> Optional[Dict]:
        """Get app information"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM apps WHERE app_id = ?
            ''', (app_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_latest_revenue(self, app_id: str) -> Optional[float]:
        """Get the latest revenue for an app"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT revenue FROM rankings
                WHERE app_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (app_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

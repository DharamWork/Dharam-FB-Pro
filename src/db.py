import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any


class DatabaseManager:
    """Manages SQLite state with WAL mode, duplicate guard, and upload telemetry."""

    def __init__(self, db_path: str = "data/posted_videos.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Set WAL mode and busy timeout for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Videos table with unique drive_file_id to strictly prevent duplicates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id TEXT NOT NULL,
                    drive_file_id TEXT UNIQUE NOT NULL,
                    facebook_video_id TEXT,
                    filename TEXT,
                    post_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );
            """)

            # Runs telemetry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    status TEXT NOT NULL,
                    runner_ip TEXT,
                    pages_processed INTEGER DEFAULT 0,
                    errors TEXT
                );
            """)

            # Page statistics cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_stats_cache (
                    page_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    followers INTEGER DEFAULT 0,
                    views_24h INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    stock_count INTEGER DEFAULT 0,
                    last_posted_at DATETIME,
                    last_sync DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Indexes for fast querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_page ON videos(page_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_posted_at ON videos(posted_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_drive_id ON videos(drive_file_id);")
            conn.commit()

    def is_video_posted(self, drive_file_id: str) -> bool:
        """Returns True if the drive file has already been posted or recorded."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM videos WHERE drive_file_id = ? AND status = 'posted'", (drive_file_id,))
            return cursor.fetchone() is not None

    def record_upload(
        self,
        page_id: str,
        drive_file_id: str,
        facebook_video_id: Optional[str],
        filename: str,
        post_type: str,
        status: str = "posted",
        error_message: Optional[str] = None
    ) -> int:
        """Records an upload attempt or success into the videos table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO videos 
                (page_id, drive_file_id, facebook_video_id, filename, post_type, status, posted_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (page_id, drive_file_id, facebook_video_id, filename, post_type, status, error_message))
            video_id = cursor.lastrowid
            
            # Update last_posted_at in cache if posted successfully
            if status == "posted":
                cursor.execute("""
                    INSERT INTO page_stats_cache (page_id, last_posted_at, last_sync)
                    VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(page_id) DO UPDATE SET 
                        last_posted_at = CURRENT_TIMESTAMP,
                        last_sync = CURRENT_TIMESTAMP
                """, (page_id,))
            conn.commit()
            return video_id

    def get_daily_upload_count(self, page_id: str, hours: int = 24) -> int:
        """Returns the number of successful posts for this page in the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM videos 
                WHERE page_id = ? AND status = 'posted' AND posted_at >= ?
            """, (page_id, cutoff))
            row = cursor.fetchone()
            return row[0] if row else 0

    def record_run_start(self, runner_ip: Optional[str] = None) -> int:
        """Records the start of a runner execution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (started_at, status, runner_ip)
                VALUES (CURRENT_TIMESTAMP, 'running', ?)
            """, (runner_ip,))
            run_id = cursor.lastrowid
            conn.commit()
            return run_id

    def record_run_complete(self, run_id: int, status: str, pages_processed: int, errors: Optional[str] = None) -> None:
        """Records the completion of a runner execution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE runs 
                SET completed_at = CURRENT_TIMESTAMP, status = ?, pages_processed = ?, errors = ?
                WHERE id = ?
            """, (status, pages_processed, errors, run_id))
            conn.commit()

    def get_recent_uploads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent uploads across all pages for telemetry and dashboard feed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, page_id, drive_file_id, facebook_video_id, filename, post_type, status, posted_at, error_message
                FROM videos
                ORDER BY posted_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_last_posted_time(self, page_id: str) -> Optional[str]:
        """Returns the most recent posted_at timestamp for a specific page."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT posted_at FROM videos 
                WHERE page_id = ? AND status = 'posted'
                ORDER BY posted_at DESC LIMIT 1
            """, (page_id,))
            row = cursor.fetchone()
            return row["posted_at"] if row else None

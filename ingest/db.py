"""Database operations for Harvard events."""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from models import Event, Config


class Database:
    """SQLite database operations for events."""
    
    def __init__(self, db_path: str = "events.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with events table and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    source_list_tag TEXT NOT NULL,
                    source_list_id TEXT,
                    message_id TEXT,
                    subject TEXT NOT NULL,
                    received_utc TEXT NOT NULL,
                    title TEXT NOT NULL,
                    start TEXT,
                    end TEXT,
                    timezone TEXT DEFAULT 'America/New_York',
                    location TEXT,
                    etype TEXT,
                    food INTEGER DEFAULT 0,
                    free INTEGER DEFAULT 1,
                    links TEXT DEFAULT '[]',
                    raw_excerpt TEXT,
                    confidence INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_start ON events(start)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_list ON events(source_list_tag)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(etype)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_food ON events(food)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_free ON events(free)")
            
            conn.commit()
    
    def upsert_event(self, event: Event) -> bool:
        """Insert or update an event."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if event exists
            cursor = conn.execute("SELECT id FROM events WHERE id = ?", (event.id,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update existing event
                conn.execute("""
                    UPDATE events SET
                        thread_id = ?, source_list_tag = ?, source_list_id = ?,
                        message_id = ?, subject = ?, received_utc = ?, title = ?,
                        start = ?, end = ?, timezone = ?, location = ?, etype = ?,
                        food = ?, free = ?, links = ?, raw_excerpt = ?,
                        confidence = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    event.thread_id, event.source_list_tag, event.source_list_id,
                    event.message_id, event.subject, event.received_utc, event.title,
                    event.start, event.end, event.timezone, event.location, event.etype,
                    event.food, event.free, event.links, event.raw_excerpt,
                    event.confidence, event.updated_at, event.id
                ))
            else:
                # Insert new event
                conn.execute("""
                    INSERT INTO events (
                        id, thread_id, source_list_tag, source_list_id, message_id,
                        subject, received_utc, title, start, end, timezone, location,
                        etype, food, free, links, raw_excerpt, confidence,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.thread_id, event.source_list_tag, event.source_list_id,
                    event.message_id, event.subject, event.received_utc, event.title,
                    event.start, event.end, event.timezone, event.location, event.etype,
                    event.food, event.free, event.links, event.raw_excerpt, event.confidence,
                    event.created_at, event.updated_at
                ))
            
            conn.commit()
            return True
    
    def get_events(
        self,
        source_list_tag: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        q: Optional[str] = None,
        has_food: Optional[bool] = None,
        free: Optional[bool] = None,
        etype: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "start DESC"
    ) -> List[Dict[str, Any]]:
        """Get events with filtering and pagination."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if source_list_tag:
                where_conditions.append("source_list_tag = ?")
                params.append(source_list_tag)
            
            if after:
                where_conditions.append("start >= ?")
                params.append(after)
            
            if before:
                where_conditions.append("start <= ?")
                params.append(before)
            
            if q:
                where_conditions.append("(subject LIKE ? OR title LIKE ? OR location LIKE ?)")
                params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
            
            if has_food is not None:
                where_conditions.append("food = ?")
                params.append(1 if has_food else 0)
            
            if free is not None:
                where_conditions.append("free = ?")
                params.append(1 if free else 0)
            
            if etype:
                where_conditions.append("etype = ?")
                params.append(etype)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Build query
            query = f"""
                SELECT * FROM events 
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            return [dict(row) for row in rows]
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a single event by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_distinct_list_tags(self) -> List[str]:
        """Get all distinct source list tags."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source_list_tag FROM events ORDER BY source_list_tag")
            return [row[0] for row in cursor.fetchall()]
    
    def get_distinct_types(self) -> List[str]:
        """Get all distinct event types."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT etype FROM events WHERE etype IS NOT NULL ORDER BY etype")
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total events
            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]
            
            # Events with food
            cursor.execute("SELECT COUNT(*) FROM events WHERE food = 1")
            events_with_food = cursor.fetchone()[0]
            
            # Free events
            cursor.execute("SELECT COUNT(*) FROM events WHERE free = 1")
            free_events = cursor.fetchone()[0]
            
            # Events by type
            cursor.execute("SELECT etype, COUNT(*) FROM events WHERE etype IS NOT NULL GROUP BY etype")
            events_by_type = dict(cursor.fetchall())
            
            # Events by list
            cursor.execute("SELECT source_list_tag, COUNT(*) FROM events GROUP BY source_list_tag")
            events_by_list = dict(cursor.fetchall())
            
            return {
                "total_events": total_events,
                "events_with_food": events_with_food,
                "free_events": free_events,
                "events_by_type": events_by_type,
                "events_by_list": events_by_list
            }

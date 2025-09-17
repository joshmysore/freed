#!/usr/bin/env python3
"""Create sample data for testing the Harvard Events system."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Sample events data
SAMPLE_EVENTS = [
    {
        "id": "sample_001",
        "thread_id": "thread_001",
        "source_list_tag": "hcs-discuss",
        "source_list_id": "hcs-discuss.lists.harvard.edu",
        "message_id": "<sample001@harvard.edu>",
        "subject": "[hcs-discuss] Comp Harvard Alternative Investment! [9/18 Kickoff]",
        "received_utc": "2024-09-15T10:00:00Z",
        "title": "Comp Harvard Alternative Investment! [9/18 Kickoff]",
        "start": "2024-09-18T19:00:00-04:00",
        "end": "2024-09-18T20:00:00-04:00",
        "timezone": "America/New_York",
        "location": "Sever 202",
        "etype": "info session",
        "food": 0,
        "free": 1,
        "links": '["https://eventbrite.com/event123", "https://forms.gle/abc123"]',
        "raw_excerpt": "Join us for the Harvard Alternative Investment kickoff event! Learn about opportunities in alternative investments and network with industry professionals.",
        "confidence": 3,
        "created_at": "2024-09-15T10:00:00Z",
        "updated_at": "2024-09-15T10:00:00Z"
    },
    {
        "id": "sample_002",
        "thread_id": "thread_002",
        "source_list_tag": "Pfoho-open",
        "source_list_id": "pfoho-open.lists.harvard.edu",
        "message_id": "<sample002@harvard.edu>",
        "subject": "[Pfoho-open] PFOOD DROP - Free Pizza!",
        "received_utc": "2024-09-16T14:00:00Z",
        "title": "PFOOD DROP - Free Pizza!",
        "start": "2024-09-17T18:00:00-04:00",
        "end": "2024-09-17T19:00:00-04:00",
        "timezone": "America/New_York",
        "location": "Pfoho Dining Hall",
        "etype": "social",
        "food": 1,
        "free": 1,
        "links": '[]',
        "raw_excerpt": "Come get free pizza in the Pfoho dining hall! First come, first served.",
        "confidence": 2,
        "created_at": "2024-09-16T14:00:00Z",
        "updated_at": "2024-09-16T14:00:00Z"
    },
    {
        "id": "sample_003",
        "thread_id": "thread_003",
        "source_list_tag": "WECode",
        "source_list_id": "wecode.lists.harvard.edu",
        "message_id": "<sample003@harvard.edu>",
        "subject": "[WECode] DUE WEDNESDAY, SEPTEMBER 17th, 11:59PM EST",
        "received_utc": "2024-09-15T09:00:00Z",
        "title": "DUE WEDNESDAY, SEPTEMBER 17th, 11:59PM EST",
        "start": "2024-09-17T23:59:00-04:00",
        "end": "2024-09-18T00:00:00-04:00",
        "timezone": "America/New_York",
        "location": None,
        "etype": "application deadline",
        "food": 0,
        "free": 1,
        "links": '["https://forms.gle/wecode2024"]',
        "raw_excerpt": "Application deadline for WECode 2024. Submit your application by 11:59PM EST on September 17th.",
        "confidence": 3,
        "created_at": "2024-09-15T09:00:00Z",
        "updated_at": "2024-09-15T09:00:00Z"
    },
    {
        "id": "sample_004",
        "thread_id": "thread_004",
        "source_list_tag": "tech-talk",
        "source_list_id": "tech-talk.lists.harvard.edu",
        "message_id": "<sample004@harvard.edu>",
        "subject": "[tech-talk] Machine Learning Workshop with Google",
        "received_utc": "2024-09-14T16:00:00Z",
        "title": "Machine Learning Workshop with Google",
        "start": "2024-09-20T14:00:00-04:00",
        "end": "2024-09-20T16:00:00-04:00",
        "timezone": "America/New_York",
        "location": "Science Center 101",
        "etype": "workshop",
        "food": 1,
        "free": 1,
        "links": '["https://eventbrite.com/ml-workshop"]',
        "raw_excerpt": "Hands-on machine learning workshop with Google engineers. Learn TensorFlow and PyTorch basics. Lunch provided!",
        "confidence": 3,
        "created_at": "2024-09-14T16:00:00Z",
        "updated_at": "2024-09-14T16:00:00Z"
    },
    {
        "id": "sample_005",
        "thread_id": "thread_005",
        "source_list_tag": "career",
        "source_list_id": "career.lists.harvard.edu",
        "message_id": "<sample005@harvard.edu>",
        "subject": "[career] Goldman Sachs Info Session",
        "received_utc": "2024-09-13T11:00:00Z",
        "title": "Goldman Sachs Info Session",
        "start": "2024-09-19T17:00:00-04:00",
        "end": "2024-09-19T18:30:00-04:00",
        "timezone": "America/New_York",
        "location": "Maxwell-Dworkin 119",
        "etype": "info session",
        "food": 1,
        "free": 1,
        "links": '["https://goldmansachs.com/careers"]',
        "raw_excerpt": "Learn about internship and full-time opportunities at Goldman Sachs. Networking reception with refreshments.",
        "confidence": 2,
        "created_at": "2024-09-13T11:00:00Z",
        "updated_at": "2024-09-13T11:00:00Z"
    },
    {
        "id": "sample_006",
        "thread_id": "thread_006",
        "source_list_tag": "hcs-discuss",
        "source_list_id": "hcs-discuss.lists.harvard.edu",
        "message_id": "<sample006@harvard.edu>",
        "subject": "[hcs-discuss] Tech Talk: AI in Healthcare",
        "received_utc": "2024-09-12T15:30:00Z",
        "title": "Tech Talk: AI in Healthcare",
        "start": "2024-09-21T12:00:00-04:00",
        "end": "2024-09-21T13:00:00-04:00",
        "timezone": "America/New_York",
        "location": "SEC 1.321",
        "etype": "tech talk",
        "food": 0,
        "free": 1,
        "links": '[]',
        "raw_excerpt": "Dr. Sarah Johnson from MIT will discuss the latest advances in AI applications for healthcare and medical diagnosis.",
        "confidence": 2,
        "created_at": "2024-09-12T15:30:00Z",
        "updated_at": "2024-09-12T15:30:00Z"
    }
]

def create_sample_database():
    """Create a sample database with test events."""
    db_path = "events.db"
    
    # Remove existing database
    if Path(db_path).exists():
        Path(db_path).unlink()
    
    # Create database and table
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE events (
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
    conn.execute("CREATE INDEX idx_events_start ON events(start)")
    conn.execute("CREATE INDEX idx_events_list ON events(source_list_tag)")
    conn.execute("CREATE INDEX idx_events_type ON events(etype)")
    conn.execute("CREATE INDEX idx_events_food ON events(food)")
    conn.execute("CREATE INDEX idx_events_free ON events(free)")
    
    # Insert sample events
    for event in SAMPLE_EVENTS:
        conn.execute("""
            INSERT INTO events (
                id, thread_id, source_list_tag, source_list_id, message_id,
                subject, received_utc, title, start, end, timezone, location,
                etype, food, free, links, raw_excerpt, confidence,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['id'], event['thread_id'], event['source_list_tag'], event['source_list_id'],
            event['message_id'], event['subject'], event['received_utc'], event['title'],
            event['start'], event['end'], event['timezone'], event['location'], event['etype'],
            event['food'], event['free'], event['links'], event['raw_excerpt'], event['confidence'],
            event['created_at'], event['updated_at']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created sample database with {len(SAMPLE_EVENTS)} events")
    print(f"📁 Database location: {Path(db_path).absolute()}")

if __name__ == "__main__":
    create_sample_database()


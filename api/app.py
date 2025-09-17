"""FastAPI application for Harvard Events API."""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import ingest modules
sys.path.append(str(Path(__file__).parent.parent / "ingest"))

# Import the database module
import importlib.util
spec = importlib.util.spec_from_file_location("db", Path(__file__).parent.parent / "ingest" / "db.py")
db_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_module)
Database = db_module.Database


# Pydantic models for API responses
class EventResponse(BaseModel):
    """Event response model."""
    id: str
    thread_id: str
    source_list_tag: str
    source_list_id: Optional[str] = None
    message_id: Optional[str] = None
    subject: str
    received_utc: str
    title: str
    start: Optional[str] = None
    end: Optional[str] = None
    timezone: str
    location: Optional[str] = None
    etype: Optional[str] = None
    food: int
    free: int
    links: List[str]
    raw_excerpt: Optional[str] = None
    confidence: int
    created_at: str
    updated_at: str


class EventsListResponse(BaseModel):
    """Events list response model."""
    events: List[EventResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    """Statistics response model."""
    total_events: int
    events_with_food: int
    free_events: int
    events_by_type: Dict[str, int]
    events_by_list: Dict[str, int]


# Initialize FastAPI app
app = FastAPI(
    title="Harvard Events API",
    description="API for Harvard mailing list events",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_database() -> Database:
    """Get database instance."""
    db_path = os.getenv("EVENTS_DB", "../ingest/events.db")
    return Database(db_path)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"ok": True, "timestamp": datetime.now().isoformat()}


@app.get("/events", response_model=EventsListResponse)
async def get_events(
    source_list_tag: Optional[str] = Query(None, description="Filter by source list tag"),
    after: Optional[str] = Query(None, description="Filter events after this ISO datetime"),
    before: Optional[str] = Query(None, description="Filter events before this ISO datetime"),
    q: Optional[str] = Query(None, description="Search in subject, title, and location"),
    has_food: Optional[bool] = Query(None, description="Filter by food availability"),
    free: Optional[bool] = Query(None, description="Filter by free events"),
    etype: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    order_by: str = Query("start DESC", description="Sort order (e.g., 'start DESC', 'title ASC')"),
    db: Database = Depends(get_database)
):
    """Get events with filtering and pagination."""
    try:
        # Get events from database
        events_data = db.get_events(
            source_list_tag=source_list_tag,
            after=after,
            before=before,
            q=q,
            has_food=has_food,
            free=free,
            etype=etype,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        # Convert to response format
        events = []
        for event_data in events_data:
            # Parse links JSON
            try:
                import json
                links = json.loads(event_data.get('links', '[]'))
            except (json.JSONDecodeError, TypeError):
                links = []
            
            event = EventResponse(
                id=event_data['id'],
                thread_id=event_data['thread_id'],
                source_list_tag=event_data['source_list_tag'],
                source_list_id=event_data['source_list_id'],
                message_id=event_data['message_id'],
                subject=event_data['subject'],
                received_utc=event_data['received_utc'],
                title=event_data['title'],
                start=event_data['start'],
                end=event_data['end'],
                timezone=event_data['timezone'],
                location=event_data['location'],
                etype=event_data['etype'],
                food=event_data['food'],
                free=event_data['free'],
                links=links,
                raw_excerpt=event_data['raw_excerpt'],
                confidence=event_data['confidence'],
                created_at=event_data['created_at'],
                updated_at=event_data['updated_at']
            )
            events.append(event)
        
        # Get total count for pagination
        # Note: This is a simplified approach. In production, you might want to optimize this
        total_events = len(events)
        
        return EventsListResponse(
            events=events,
            total=total_events,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")


@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Database = Depends(get_database)
):
    """Get a single event by ID."""
    try:
        event_data = db.get_event_by_id(event_id)
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Parse links JSON
        try:
            import json
            links = json.loads(event_data.get('links', '[]'))
        except (json.JSONDecodeError, TypeError):
            links = []
        
        event = EventResponse(
            id=event_data['id'],
            thread_id=event_data['thread_id'],
            source_list_tag=event_data['source_list_tag'],
            source_list_id=event_data['source_list_id'],
            message_id=event_data['message_id'],
            subject=event_data['subject'],
            received_utc=event_data['received_utc'],
            title=event_data['title'],
            start=event_data['start'],
            end=event_data['end'],
            timezone=event_data['timezone'],
            location=event_data['location'],
            etype=event_data['etype'],
            food=event_data['food'],
            free=event_data['free'],
            links=links,
            raw_excerpt=event_data['raw_excerpt'],
            confidence=event_data['confidence'],
            created_at=event_data['created_at'],
            updated_at=event_data['updated_at']
        )
        
        return event
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event: {str(e)}")


@app.get("/lists")
async def get_list_tags(db: Database = Depends(get_database)):
    """Get all distinct source list tags."""
    try:
        list_tags = db.get_distinct_list_tags()
        return {"list_tags": list_tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching list tags: {str(e)}")


@app.get("/types")
async def get_event_types(db: Database = Depends(get_database)):
    """Get all distinct event types."""
    try:
        event_types = db.get_distinct_types()
        return {"event_types": event_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event types: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Database = Depends(get_database)):
    """Get database statistics."""
    try:
        stats = db.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.post("/reindex")
async def reindex_events(db: Database = Depends(get_database)):
    """Trigger database reindexing (placeholder for future optimization)."""
    try:
        # This is a placeholder for future optimization
        # In a real implementation, you might rebuild indexes or update materialized views
        return {"message": "Reindexing completed", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

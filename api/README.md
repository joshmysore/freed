# Harvard Events API

FastAPI service that exposes Harvard events data via RESTful JSON endpoints.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export EVENTS_DB="../ingest/events.db"  # Path to SQLite database
   ```

3. **Start the server:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```

## API Endpoints

### Health Check
- `GET /health` - Returns API health status

### Events
- `GET /events` - List events with filtering and pagination
- `GET /events/{event_id}` - Get single event by ID

### Metadata
- `GET /lists` - Get all distinct source list tags
- `GET /types` - Get all distinct event types
- `GET /stats` - Get database statistics

### Admin
- `POST /reindex` - Trigger database reindexing

## Query Parameters

### GET /events

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_list_tag` | string | Filter by source list tag |
| `after` | string | Filter events after this ISO datetime |
| `before` | string | Filter events before this ISO datetime |
| `q` | string | Search in subject, title, and location |
| `has_food` | boolean | Filter by food availability |
| `free` | boolean | Filter by free events |
| `etype` | string | Filter by event type |
| `limit` | integer | Maximum events to return (1-1000, default: 100) |
| `offset` | integer | Number of events to skip (default: 0) |
| `order_by` | string | Sort order (default: "start DESC") |

## Response Format

### Event Object
```json
{
  "id": "gmail_message_id",
  "thread_id": "gmail_thread_id",
  "source_list_tag": "hcs-discuss",
  "source_list_id": "hcs-discuss.lists.harvard.edu",
  "message_id": "<message@harvard.edu>",
  "subject": "[hcs-discuss] Event Title",
  "received_utc": "2024-09-15T10:00:00Z",
  "title": "Event Title",
  "start": "2024-09-18T19:00:00-04:00",
  "end": "2024-09-18T20:00:00-04:00",
  "timezone": "America/New_York",
  "location": "Sever 202",
  "etype": "info session",
  "food": 1,
  "free": 1,
  "links": ["https://eventbrite.com/event123"],
  "raw_excerpt": "Event description...",
  "confidence": 3,
  "created_at": "2024-09-15T10:00:00Z",
  "updated_at": "2024-09-15T10:00:00Z"
}
```

### Events List Response
```json
{
  "events": [...],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

## Examples

### Get recent events
```bash
curl "http://localhost:8000/events?limit=10&order_by=start%20DESC"
```

### Filter by list and type
```bash
curl "http://localhost:8000/events?source_list_tag=hcs-discuss&etype=info%20session"
```

### Search for events with food
```bash
curl "http://localhost:8000/events?has_food=true&free=true"
```

### Get events in date range
```bash
curl "http://localhost:8000/events?after=2024-09-01T00:00:00Z&before=2024-09-30T23:59:59Z"
```

### Search by keyword
```bash
curl "http://localhost:8000/events?q=machine%20learning"
```

## CORS

The API includes CORS middleware configured for:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `404` - Event not found
- `500` - Internal server error

Error responses include a `detail` field with error information.

## Development

### Running in Development Mode
```bash
uvicorn app:app --reload --port 8000 --log-level debug
```

### API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test events endpoint
curl "http://localhost:8000/events?limit=5"

# Test specific event
curl http://localhost:8000/events/some_event_id
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
- `EVENTS_DB` - Path to SQLite database file
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

## Monitoring

The API includes basic health check endpoint for monitoring:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "ok": true,
  "timestamp": "2024-09-15T10:00:00Z"
}
```

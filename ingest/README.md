# Gmail Event Ingestion

This module fetches labeled emails from Gmail, parses Harvard mailing list events, and stores them in SQLite.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download `credentials.json` to this directory

3. **Configure the application:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

4. **Set up Gmail label:**
   - Create a label in Gmail (e.g., "GG.Events")
   - Apply the label to emails you want to process
   - Update `label_name` in config.json

## Usage

### Basic ingestion:
```bash
python main.py --since 60 --limit 100
```

### Command line options:
- `--since DAYS`: Look back N days (default: 60)
- `--limit N`: Maximum messages to process (default: 100)
- `--label NAME`: Override label name from config
- `--save-body`: Save full message body text
- `--dump-json FILE`: Export raw messages to JSONL
- `--config FILE`: Use custom config file
- `--db FILE`: Use custom database file

### Examples:

```bash
# Process last 30 days, save to custom DB
python main.py --since 30 --db my_events.db

# Export raw messages for debugging
python main.py --dump-json messages.jsonl --since 7

# Process specific label
python main.py --label "MyEvents" --since 14
```

## Configuration

Edit `config.json`:

```json
{
  "label_name": "GG.Events",
  "gmail_query": "newer_than:60d",
  "timezone": "America/New_York",
  "save_body_text": false,
  "body_max_chars": 20000
}
```

## Automation

### Cron job (runs every 6 hours):
```bash
# Add to crontab: crontab -e
0 */6 * * * cd /path/to/ingest && python main.py --since 1
```

### Systemd timer (Linux):
```ini
# /etc/systemd/system/harvard-events.timer
[Unit]
Description=Harvard Events Ingestion Timer

[Timer]
OnCalendar=*:0/6:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Database Schema

The SQLite database contains an `events` table with the following fields:

- `id`: Gmail message ID (primary key)
- `thread_id`: Gmail thread ID
- `source_list_tag`: List tag from subject [TAG]
- `source_list_id`: List-Id header value
- `message_id`: Message-ID header value
- `subject`: Email subject
- `received_utc`: When email was received (ISO UTC)
- `title`: Cleaned event title
- `start`: Event start time (ISO with timezone)
- `end`: Event end time (ISO with timezone)
- `timezone`: Event timezone
- `location`: Event location
- `etype`: Event type (info session, workshop, etc.)
- `food`: Has food (0/1)
- `free`: Is free (0/1)
- `links`: JSON array of links
- `raw_excerpt`: Short text excerpt
- `confidence`: Parsing confidence (0-3)
- `created_at`: Record creation time
- `updated_at`: Record update time

## Event Parsing

The parser extracts information using these heuristics:

### Time/Date Detection:
- Looks for explicit markers: 🗓️, 🕒, When:, Date:, Time:
- Parses subject patterns like [9/18]
- Uses `dateparser` with future date preference
- Defaults to 60-minute duration if only start time found

### Location Detection:
- Explicit markers: 📍, Where:, Location:, Venue:
- Common Harvard buildings: Sever, Science Center, SEC, etc.
- Room numbers and building codes

### Event Type Classification:
- **info session**: recruiting, kickoff, company presentation
- **workshop**: hands-on, tutorial, training
- **tech talk**: technical presentation, lecture
- **career**: job fair, networking, interview prep
- **social**: mixer, party, food events
- **application deadline**: DUE, DEADLINE patterns

### Food/Free Detection:
- **Food**: pizza, boba, dumpling, snack, refreshment, cater, lunch, dinner
- **Free**: absence of $, ticket, fee, cost, price, charge, non-huid

### Link Extraction:
- Prioritizes Eventbrite and Google Forms
- Extracts up to 5 links per event

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Troubleshooting

### Common Issues:

1. **"Label not found"**: Make sure the label exists in Gmail and matches config
2. **"Credentials not found"**: Download credentials.json from Google Cloud Console
3. **"Permission denied"**: Check OAuth scopes and re-authorize
4. **"No messages found"**: Verify label is applied to emails and query is correct

### Debug Mode:
```bash
# Export raw messages for inspection
python main.py --dump-json debug.jsonl --since 7 --limit 10

# Check database contents
sqlite3 events.db "SELECT * FROM events LIMIT 5;"
```

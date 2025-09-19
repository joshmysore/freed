# GG.Events Parser - Cursor Prompt

## ROLE
You are implementing two things:
1) A robust email→event parser that outputs strict JSON for a Pydantic ParsedEvent.
2) A minimal, fast UI that auto-loads the most recent emails, provides a calendar filter + list view with expandable rows, and a Food filter that isolates events with food.

## CONSTRAINTS
- Language: Python 3.11 backend, Pydantic v2, FastAPI, httpx. Frontend: React (TypeScript), existing stack.
- Timezone: America/New_York. RECEIVED_AT is available per email.
- No prose in parser outputs. Either a JSON object or the exact string "DROP".
- Never log "Failed to parse" for intentional drops; log at INFO: "Email dropped (no event)".

## BACKEND: PARSER LLM INSTRUCTIONS
You are an email→event extractor. Output strict JSON that passes Pydantic. No prose.

### GOAL
- From a single email, extract a calendar event.
- If no resolvable event date exists, output the literal string: "DROP".

### INPUTS
- Email subject, body, sender, and the email's RECEIVED_AT timestamp (local).
- Timezone: America/New_York.

### OUTPUT SCHEMA (JSON)
```json
{
  "title": str,                                  # <= 140 chars
  "organizer": str | null,
  "contacts": [{"name": str | null, "email": str | null}] | [],
  "date_start": "YYYY-MM-DD",                    # required for events
  "time_start": "HH:MM" | null,                  # 24h
  "time_end": "HH:MM" | null,                    # 24h, may be null
  "timezone": "America/New_York",
  "location": str | "",
  "description": str | "",
  "urls": [str],
  "food_type": str | "",
  "food_quantity_hint": str | "",
  "source_message_id": str | "",
  "source_subject": str | "",
  "mailing_list": str | ""
}
```

### STRICT VALIDATION
- date_start must match \d{4}-\d{2}-\d{2}.
- time_* must match \d{2}:\d{2} if present.
- Never emit "null" as a string. Use null or omit per schema.

### CLASSIFY FIRST
- If the content is recruiting/ongoing/apply-now with NO resolvable date, output "DROP".
  Down-rank subjects/bodies with phrases like: join our team, hiring, recruiting, roles, apply, form link only, ongoing.

### NORMALIZATION PIPELINE (before deciding DROP vs EVENT)
1) Trim whitespace. Replace fancy dashes (–, —) with "-".
2) Map placeholders {"", "TBD", "N/A", "-"} → null.
3) Collapse repeated spaces.
4) Collect URLs.

### DATE RESOLUTION
- Use RECEIVED_AT (America/New_York) for relative terms:
  - "today", "tonight" → RECEIVED_AT date.
  - "tomorrow" → RECEIVED_AT + 1 day.
  - Weekday names → next occurrence ≥ RECEIVED_AT date.
  - Month name + day without year → infer year from RECEIVED_AT.
- If multiple candidate dates appear, prefer the earliest future date ≥ RECEIVED_AT. If none future, use the clearest explicit date.

### TIME PARSING
- Regex: \b(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\b
- Convert 12h → 24h. 12:xx AM → 00:xx. 12:xx PM → 12:xx.
- Ranges:
  - Forms: "9-10", "9–10", "9-10pm", "9-10 PM", "9:30-10:45 am".
  - If one meridiem is present, apply to both ends.
  - If none, infer from context tokens:
    - {tonight, evening, late} ⇒ PM
    - {morning, breakfast} ⇒ AM
  - If still ambiguous, set both to null.
- If only a start time exists, time_end may be null.

### GUARDRAILS
- If after normalization you still lack a valid date_start, output "DROP".
- Do not invent locations or organizers. Use null/empty if unclear.
- Title: concise. Remove listserv tags like "[PFOHO]" or "Fwd:".
- Description: 1–3 sentences. No HTML.

### EXAMPLES

#### A) Recruiting, no date → DROP
Subject: [Pfoho-open] Fwd: Join Our Startup: Barry & Bonna Publishing LLC
Body mentions roles and an application form only.
→ "DROP"

#### B) Relative date and range
RECEIVED_AT: 2025-09-18 16:48 America/New_York
Subject: [PFOHO] Resume Review Table *9-10 Tonight!
Body: "upper d-hall"
→
```json
{
  "title": "Career Fair Preparation – Resume Review Table",
  "organizer": "Larissa J. Senatus",
  "contacts": [{"name":"Larissa J. Senatus","email":"pfoho-announce@lists.fas.harvard.edu"}],
  "date_start": "2025-09-18",
  "time_start": "21:00",
  "time_end": "22:00",
  "timezone": "America/New_York",
  "location": "upper d-hall",
  "description": "Resume reviews and career fair Q&A.",
  "urls": [],
  "food_type": "",
  "food_quantity_hint": "",
  "source_message_id": "...",
  "source_subject": "[PFOHO] Resume Review Table *9-10 Tonight!",
  "mailing_list": "PFOHO"
}
```

#### C) Explicit date and time
Subject: Re: COMPSCI 2821R: Presentation on Expert Systems – Monday, September 22 at 12:45 PM
RECEIVED_AT: 2025-09-18
→
```json
{
  "title": "COMPSCI 2821R: Expert Systems Presentation",
  "organizer": "Talha Rehman",
  "contacts": [{"name":"Talha Rehman","email":"talha@g.harvard.edu"}],
  "date_start": "2025-09-22",
  "time_start": "12:45",
  "time_end": null,
  "timezone": "America/New_York",
  "location": "",
  "description": "Presentation on Expert Systems moved to Monday at 12:45.",
  "urls": [],
  "food_type": "",
  "food_quantity_hint": "",
  "source_message_id": "...",
  "source_subject": "Re: COMPSCI 2821R: Presentation on Expert Systems – Monday, September 22 at 12:45 PM",
  "mailing_list": ""
}
```

### FINAL INSTRUCTIONS
- Output exactly one JSON object conforming to the schema above OR the exact string "DROP".
- No commentary. No Markdown. No code fences.

## BACKEND: PRE-VALIDATION PATCHES (code to implement)
- Normalize URLs before Pydantic:

```python
import re
from urllib.parse import urlsplit

SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*://')
DOMAIN_LIKE_RE = re.compile(r'^[\w.-]+\.[a-zA-Z]{2,}(/.*)?$')

def normalize_url(u: str) -> str | None:
    if not u:
        return None
    u = u.strip()
    if SCHEME_RE.match(u):
        return u
    if DOMAIN_LIKE_RE.match(u):
        return f'https://{u}'
    return None

def normalize_urls(urls: list[str]) -> list[str]:
    seen = set()
    out = []
    for u in urls or []:
        v = normalize_url(u)
        if v and urlsplit(v).netloc and v not in seen:
            out.append(v); seen.add(v)
    return out
```

* Map placeholders to None; strip exotic dashes; collapse whitespace.
* Log intentional drops at INFO without error wording.

Pydantic (v2) model accepts:

* date_start: constr(regex=r'^\d{4}-\d{2}-\d{2}$') | None  (but DROP earlier if None)
* time_start/time_end: constr(regex=r'^\d{2}:\d{2}$') | None

## FRONTEND: UI REQUIREMENTS
Goal: Auto-read newest emails, filter by date via calendar, list events, expand details, and filter by Food.

### Data contract (from backend /events):
```typescript
[
{
"title": string,
"date_start": "YYYY-MM-DD",
"time_start": "HH:MM" | null,
"time_end": "HH:MM" | null,
"timezone": "America/New_York",
"location": string,
"description": string,
"urls": string[],
"food_type": string,                  # empty if none
"food_quantity_hint": string,
"source_subject": string,
"source_message_id": string,
"mailing_list": string,
"organizer": string | null,
"contacts": [{"name": string | null, "email": string | null}]
},
...
]
```

### Behavior
* On load: fetch `/events/gg-events?max_results=50&sort=desc` and store.
* Default view: date range = [today .. today+14]. Show only events within range.
* Calendar filter: single-date or range select. Changes update the list reactively.
* Food filter: toggle "Food only". When ON, show events where:
  * `food_type` is non-empty OR
  * `food_quantity_hint` is non-empty OR
  * description matches /(pizza|snack|snacks|food|lunch|dinner|breakfast|refreshments|cater(ed|ing)|bagels?|coffee|tea|chai|cookies?)/i
* List: grouped by date. Within a date, sort by time_start (nulls last).
* Each row shows: title, time range, location, "Food" pill if detected.
* Expand row: show description, organizer, contacts, URLs (clickable), mailing list, and source subject. Collapse/expand per row.
* Persist filters in URL query or localStorage.
* Loading and empty states present. No dropped emails appear.
* Accessibility: all interactive elements keyboard-focusable; ARIA for disclosure.

### Acceptance criteria
* Fresh fetch on mount shows newest first with default range applied.
* Toggling Food only updates results instantly.
* Selecting a date on the calendar narrows the list to that day.
* Expanding a row reveals URLs with https added for bare domains.
* No console errors. No "Failed to parse" logs for intentional drops.

### Deliverables
* Backend: URL normalization and logging changes integrated in parser pipeline.
* Frontend: Calendar+List+Expand+Food Filter implemented as above.
* Tests: unit tests for normalize_urls; UI smoke test for Food filter and date filter.


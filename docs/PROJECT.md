# Project: Email → Event Parser (LLM-Assisted) – MVP + Roadmap

## High-level goal

Create a minimal, reliable pipeline that:

1. pulls recent emails from Gmail,
2. parses them with an LLM into a **strict JSON** event object,
3. validates the JSON against a schema, and
4. outputs a highlighted summary of the parsed data (CLI + API), with an option to generate an `.ics` or (later) insert into Google Calendar.

## Deliverables (initial commit)

* A working Python project (FastAPI + CLI) that implements the MVP workflow.
* **`PROJECT.md`**: includes concise MVP definition, constraints, and a **roadmap** to next features.
* **`UPDATES.md`**: empty but created, with a template for future changelogs.
* Clear, testable acceptance criteria and examples.
* Minimal UI (FastAPI endpoints + simple HTML preview page) that shows parsed events with fields highlighted.
* Strong commit hygiene (see policy below).

## Repo layout

```
.
├─ src/
│  ├─ app.py                # FastAPI app with endpoints
│  ├─ cli.py                # CLI runner for scan/parse/highlight
│  ├─ gmail_client.py       # Gmail fetch (readonly)
│  ├─ parser_llm.py         # LLM calls with JSON-only contract
│  ├─ schema.py             # Pydantic models + validators
│  ├─ postprocess.py        # heuristics (time/location/food/link extraction sanity checks)
│  ├─ calendar_ics.py       # ICS generation
│  ├─ views/
│  │  └─ index.html         # simple page listing parsed events + highlights
│  └─ utils.py              # shared helpers (logging, dedupe hash, etc.)
├─ tests/
│  ├─ test_schema.py
│  ├─ test_postprocess.py
│  └─ test_end_to_end.py
├─ prompts/
│  └─ event_parser_prompt.txt
├─ docs/
│  ├─ PROJECT.md            # MVP + roadmap (this file)
│  └─ UPDATES.md            # running changelog
├─ env.example
├─ requirements.txt
├─ README.md
├─ Makefile
└─ LICENSE
```

## Tech choices

* Python 3.11+, FastAPI, Uvicorn
* Google APIs (`google-api-python-client`, `google-auth`, `google-auth-oauthlib`)
* Pydantic v2
* HTML sanitization: `beautifulsoup4`
* LLM SDK: Harvard OpenAI API integration (`OPENAI_API_KEY` env var; Harvard gateway endpoint)
* Tests: `pytest`

## Gmail scopes & search

* Scopes (MVP): `https://www.googleapis.com/auth/gmail.readonly`
* Query (MVP demo):

  * default: `newer_than:14d (subject:invite OR subject:event OR subject:seminar OR subject:talk OR subject:workshop OR subject:session)`
* For mailing lists (future feature): support queries like:

  * `list:*` (uses List-Id header when present)
  * `from:*@lists.harvard.edu` (and user-provided domains)
  * user-editable query string in `.env`

## Event JSON schema (Pydantic) – **strict**

```python
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List

class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class ParsedEvent(BaseModel):
    title: str = Field(..., description="Event name")
    organizer: Optional[str] = None
    contacts: List[Contact] = []
    date_start: str = Field(..., description="YYYY-MM-DD")
    time_start: Optional[str] = Field(None, description="HH:MM 24h")
    time_end: Optional[str] = None
    timezone: str = "America/New_York"
    location: Optional[str] = None
    description: Optional[str] = None
    urls: List[HttpUrl] = []
    # food details:
    food_type: Optional[str] = None         # e.g., "Bonchon", "pizza", "sushi"
    food_quantity_hint: Optional[str] = None # e.g., "dinner provided", "limited snacks"
    # source ids:
    source_message_id: Optional[str] = None
    source_subject: Optional[str] = None

    @field_validator("date_start")
    @classmethod
    def _date_fmt(cls, v: str) -> str:
        # enforce YYYY-MM-DD
        import re
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v or ""):
            raise ValueError("date_start must be YYYY-MM-DD")
        return v

    @field_validator("time_start", "time_end")
    @classmethod
    def _time_fmt(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is None: return v
        if not re.fullmatch(r"\d{2}:\d{2}", v):
            raise ValueError("time must be HH:MM 24h")
        return v
```

## LLM prompt contract

**Absolutely require JSON-only output.** If a field is missing/ambiguous, set it to `null` instead of guessing.

```
You extract EVENTS from raw emails. Return ONLY a single JSON object with this exact schema and keys:
{
  "title": "", "organizer": "", "contacts":[{"name":"","email":""}],
  "date_start":"YYYY-MM-DD", "time_start":"HH:MM or null", "time_end":"HH:MM or null",
  "timezone":"IANA tz like America/New_York",
  "location":"", "description":"(<=600 chars)",
  "urls":["..."],
  "food_type":"", "food_quantity_hint":"",
  "source_message_id":"", "source_subject":""
}
Rules:
- Parse concrete, explicit dates/times only. If ambiguous, return null for time fields.
- If both weekday and explicit date exist, use the explicit date.
- Prefer timezone mentioned in the email; otherwise "America/New_York".
- Food: infer named vendor/food type if explicitly present (e.g., "Bonchon"). If only generic info (e.g., "dinner provided"), set food_type accordingly and food_quantity_hint conservatively.
- Include sign-up/RSVP links in "urls".
- Do NOT add extra keys. Do NOT include commentary.
EMAIL:
<<<
{{EMAIL_PLAIN_TEXT}}
>>>
```

## MVP user flows

* **CLI**

  * `make scan` → fetch candidates via Gmail query; for each message, extract text; call LLM; validate; print colored highlight of title/date/time/location/food/links; write `.ics` if `--ics`.
* **API**

  * `GET /health` → ok
  * `GET /events/scan` → run once, return parsed JSON list
  * `POST /ics` → accepts `ParsedEvent` JSON, returns `.ics` bytes

## Acceptance criteria (MVP)

* Given the HUMIC sample email, system returns:

  * `title="HUMIC Intro Session"`
  * `date_start="2025-09-19"`
  * `time_start="17:00"`, `time_end="18:00"` (if explicit; else `time_end=null`)
  * `timezone="America/New_York"`
  * `location="Sever Hall 203"`
  * `food_type="Bonchon"` and `food_quantity_hint` that reflects "dinner provided / snacks"
  * at least one `urls` if present in email
  * `source_message_id` and `source_subject` filled
* JSON validates with Pydantic; non-conforming output is rejected.
* CLI & `/events/scan` both work with a small batch (≤10 emails).
* `.ics` generation produces a valid file that imports in Google Calendar.

## Post-processing heuristics (MVP)

* If `time_start` missing but a time-like string is present, attempt normalization; otherwise leave `null`.
* If `time_end` missing but duration phrasing like "5–6 PM" exists, infer end; else `null`.
* Normalization of location strings (trim whitespace; keep building + room).
* Food rules:

  * explicit vendor/brand → `food_type=vendor`
  * otherwise generic → `food_type` generic, `food_quantity_hint` from phrases (e.g., "dinner provided", "light snacks", "pizza provided while supplies last")

## Frontend (lite for MVP)

* One static page (`views/index.html`) that:

  * Lists parsed events as cards.
  * Highlights key fields.
  * Offers "Download ICS" button (posts the event JSON to `/ics`).
* No auth in MVP; just a preview.

## Environment & secrets

* `env.example` keys:

  * `GOOGLE_CLIENT_ID=`
  * `GOOGLE_CLIENT_SECRET=`
  * `GOOGLE_PROJECT_ID=`
  * `OPENAI_API_KEY=` (Harvard Community Developers API key)
  * `GMAIL_QUERY=newer_than:14d (subject:invite OR subject:event OR subject:seminar OR subject:talk OR subject:workshop OR subject:session)`
  * `DEFAULT_TIMEZONE=America/New_York`
* README: explain OAuth steps, token storage, and how to obtain Gmail creds.

## Makefile (targets)

* `make setup` → install deps
* `make run` → start FastAPI (reload)
* `make test` → run pytest
* `make scan` → run CLI scan once
* `make fmt` → black + isort
* `make lint` → ruff

## Roadmap

* **Phase 0 (MVP – COMPLETED)**

  * ✅ Gmail read-only polling
  * ✅ LLM JSON parse with validation (Harvard OpenAI API)
  * ✅ Basic highlight view
  * ✅ ICS export
  * ✅ GG.Events specialized parsing
  * ✅ Mailing list extraction and tagging
  * ✅ Web interface with event cards
  * ✅ Harvard OpenAI API integration ($10/month credits)
* **Phase 1**

  * Frontend site (Next.js or keep FastAPI templates) listing events; per-event page
  * User-provided Gmail search strings (including mailing lists: `list:*`, `from:*@domain`)
  * Basic auth/session just for storing queries locally (no user data at rest beyond tokens)
* **Phase 2**

  * "Add to Google Calendar" via Calendar API (with confirmation screen)
  * Improved parsing quality for: exact **time**, **location**, and **food** details (type & quantity hints)
  * Link harvesting: RSVP, signup forms, Zoom/Meet links; show as badges
  * Confidence scores + NEEDS\_REVIEW label for low-confidence cases
* **Phase 3**

  * Multi-user sign-up with OAuth (Google) to parse **their** inbox/lists
  * Background jobs (polling or Gmail push with Pub/Sub)
  * Admin dashboard for parsing accuracy metrics, false-negative/positive dashboards
* **Phase 4**

  * Fine-tuned small model or rules-backed extraction to reduce LLM cost
  * Templates for common orgs (e.g., campus clubs) with deterministic regexes
  * iCal feed per user
  * Attachments OCR (flyers) with vision model (optional)

## Documentation & anti-hallucination policy

* Cursor: **Never** invent fields. If missing/ambiguous → set `null`.
* Keep **`docs/PROJECT.md`** as the single source of truth for scope and roadmap.
* Maintain **`docs/UPDATES.md`** with every meaningful change:

  * Date (YYYY-MM-DD), short summary, affected files, migration notes if any, tests added/updated.
* In PRs/commits, link the section of `PROJECT.md` you're implementing.

## Commit/version policy

* Conventional commits:

  * `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
* Each commit must update **`docs/UPDATES.md`** if behavior/contract changes.
* No large multi-purpose commits. Atomic, reviewable changes only.

## Agent roles

* **Agent A – Internal Docs & Maintenance**

  * Owns `docs/PROJECT.md`, `docs/UPDATES.md`, and README coherence.
  * Ensures tests align with documented acceptance criteria.
* **Agent B – Incremental Features**

  * Adds small features behind flags or clear endpoints.
  * Writes tests first; coordinates with A to update docs.
* **Human-in-the-loop**

  * Approves schema changes, Gmail queries, and Calendar insertion behavior.
  * Reviews parsing examples before enabling auto-insert.

## Tasks (initial)

1. Scaffold repo structure (above).
2. Implement `schema.py` and tests for JSON validation.
3. Implement `gmail_client.py` (readonly) with simple query from `.env`.
4. Implement `parser_llm.py` to call LLM with **`prompts/event_parser_prompt.txt`** and return **strict JSON** (reject anything else).
5. Implement `postprocess.py` heuristics (time/location/food/link normalization).
6. Implement ICS generation (`calendar_ics.py`).
7. Implement CLI (`cli.py`) and minimal API (`app.py` + `views/index.html`).
8. Create **`docs/PROJECT.md`** with MVP + roadmap (as specified), and **`docs/UPDATES.md`** (template).
9. Add tests (`tests/`), Makefile, `.env.example`, `requirements.txt`.
10. Run end-to-end on at least one real email (mocked if needed in CI).

## Non-goals (for MVP)

* No Calendar insertion yet (keep code ready but behind a flag).
* No user auth or persistence beyond OAuth tokens for the dev account.
* No heavy frontend or complex styling.

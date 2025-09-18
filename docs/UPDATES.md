# Updates Log

This file tracks all meaningful changes to the Email Event Parser project.

## Template

For each update, include:
- Date (YYYY-MM-DD)
- Short summary
- Affected files
- Migration notes (if any)
- Tests added/updated

---

## 2024-12-19 - Initial MVP Implementation

**Summary**: Complete MVP implementation with all core components

**Affected files**:
- `src/schema.py` - Pydantic models and validators
- `src/gmail_client.py` - Gmail API integration
- `src/parser_llm.py` - LLM parsing with strict JSON contract
- `src/postprocess.py` - Post-processing heuristics
- `src/calendar_ics.py` - ICS calendar generation
- `src/cli.py` - Command-line interface
- `src/app.py` - FastAPI application
- `src/views/index.html` - Web interface
- `src/utils.py` - Utility functions
- `prompts/event_parser_prompt.txt` - LLM prompt template
- `requirements.txt` - Python dependencies
- `Makefile` - Build and run commands
- `env.example` - Environment variables template
- `docs/PROJECT.md` - Project documentation and roadmap
- `docs/UPDATES.md` - This changelog

**Features implemented**:
- Gmail read-only email fetching with OAuth2
- LLM-based event parsing with strict JSON validation
- Post-processing heuristics for time/location/food normalization
- ICS calendar file generation
- CLI interface with colored output
- FastAPI web interface with HTML preview
- Comprehensive error handling and logging

**Tests added**: None yet (pending implementation)

**Migration notes**: None (initial implementation)

---

## 2024-12-19 - GG.Events Integration and Mailing List Support

**Summary**: Added specialized support for GG.Events mailing list emails with mailing list extraction and enhanced frontend

**Affected files**:
- `src/schema.py` - Added mailing_list and original_email_body fields
- `src/utils.py` - Added extract_mailing_list_from_subject function
- `src/parser_llm.py` - Updated to extract mailing list from subject lines
- `src/gmail_client.py` - Added get_gg_events_emails method for GG.Events filtering
- `src/app.py` - Added /events/gg-events endpoint
- `src/views/index.html` - Complete frontend redesign for GG.Events focus
- `.gitignore` - Added sensitive files to gitignore

**Features implemented**:
- GG.Events email filtering using Gmail labels
- Mailing list name extraction from [XXXXX] subject format
- Enhanced event cards with mailing list information
- Expandable event cards to view original email content
- Manual refresh button to control API calls and costs
- Updated UI specifically for GG.Events workflow
- Added original email body display functionality

**Migration notes**: 
- Frontend now defaults to GG.Events workflow instead of generic email search
- New /events/gg-events endpoint for specialized processing
- Mailing list information automatically extracted and displayed

**Tests added**: Mailing list extraction function tested with various subject formats

---

## Open Questions

* None currently

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

## Open Questions

* None currently

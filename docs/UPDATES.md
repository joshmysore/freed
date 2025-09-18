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

## 2024-12-19 - Parsing Analysis and 14-Day Search Implementation

**Summary**: Expanded search to 14 days, analyzed parsing issues, and improved system robustness

**Affected files**:
- `src/gmail_client.py` - Updated to search last 14 days of GG.Events emails
- `docs/UPDATES.md` - Added parsing analysis findings

**Key Findings from Parsing Analysis**:
- **Success Rate**: 48% (24 out of 50 emails parsed successfully)
- **Total Emails Found**: 50 GG.Events emails from last 14 days
- **Successfully Parsed**: 24 events
- **Failed to Parse**: 26 emails

**Common Parsing Issues Identified**:
1. **Mailing List Footer Emails**: Many emails contain only mailing list footers (180 characters) with no actual content
2. **Forwarded Emails**: Emails with "Fwd:" in subject often fail due to poor content structure
3. **Date Parsing Issues**: Some events fail validation due to missing or invalid date_start fields
4. **Non-Event Content**: Job postings, merchandise announcements, and administrative messages
5. **Reply Emails**: "Re:" emails often contain fragmented event information

**Successfully Parsed Events Include**:
- Figma Workshop (Sept 24, Harvard Hall 101, with mochi donuts and boba)
- Expert Systems Presentation (Sept 22, 12:45 PM)
- ReCompute 2025 Fall Comp (Sept 28, with snacks)
- HUMIC Intro Session (Sept 19, 5:00 PM, Sever Hall 203, Bonchon dinner)
- Student-Tutor Sustainability Committee Meeting (Sept 21, 6:00 PM, Holmes Heritage Room)
- De La Rose Concert (Sept 17, 8:30 PM, Big Night Live)
- And 18 more events with full details

**System Improvements Made**:
- Expanded search from 10 to 50 emails maximum
- Added 14-day time filter for more comprehensive coverage
- Improved error handling for validation failures
- Enhanced mailing list extraction accuracy

**Migration notes**: 
- Search now covers last 14 days by default
- Increased max results to 50 emails
- Better handling of parsing failures

**Tests added**: Comprehensive parsing analysis with 50 real GG.Events emails

---

## Open Questions

* Consider improving LLM prompt for better event detection
* Add more robust date/time parsing for edge cases
* Implement better filtering for forwarded emails and replies
* Consider adding confidence scoring for parsed events

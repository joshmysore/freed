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

## 2025-09-19 - Initial MVP Implementation

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

## 2025-09-22 - GG.Events Integration and Mailing List Support

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

## 2024-09-22 - Parsing Analysis and 14-Day Search Implementation

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

## 2025-09-22 - Harvard OpenAI API Integration

**Summary**: Successfully integrated Harvard's OpenAI Community Developers API with $10/month credits

**Affected files**:
- `src/parser_llm.py` - Updated to use Harvard API gateway endpoint
- `env.example` - Updated with Harvard API key configuration
- `.env` - Created with Harvard API key
- `README.md` - Updated with Harvard API setup instructions
- `docs/README.md` - Updated with current system status

**Features implemented**:
- Harvard OpenAI API gateway integration (`https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1`)
- GPT-4o-mini model usage with Harvard credits
- Proper API key configuration and environment setup
- Updated documentation with Harvard API setup instructions
- Verified API connection and email parsing functionality

**Technical details**:
- Base URL: `https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1`
- Model: `gpt-4o-mini` (cost-effective for parsing tasks)
- Authentication: `api-key` header as required by Harvard gateway
- Credits: $10/month provided by Harvard for community developers
- Streaming: Not supported (as per Harvard API limitations)

**Migration notes**: 
- Existing code was already configured for Harvard API gateway
- No breaking changes to existing functionality
- API key now uses Harvard's community developers program

**Tests added**: API connection test verified successful integration

---

## 2025-09-24 - Google Calendar Integration and Email Parsing Improvements

**Summary**: Major feature addition with direct Google Calendar integration, improved email parsing, and enhanced UI/UX

**Affected files**:
- `app/server.py` - Added Google Calendar ICS endpoints and debug endpoints
- `app/gmail_client.py` - Enhanced email body extraction for multipart/related structures
- `app/config.py` - Added food-related keywords to event detection patterns
- `src/views/index.html` - Complete Google Calendar integration and UI improvements
- `app/calendar_ics.py` - Existing ICS generation functionality (leveraged)

**Features implemented**:
- **Direct Google Calendar Integration**: One-click "Add to Calendar" buttons on all events
- **Enhanced Email Parsing**: Improved multipart email body extraction for complex email structures
- **Better Event Detection**: Added food-related keywords (bread, community, join, etc.) to catch more events
- **Fixed Date Display**: Proper Today/Tomorrow grouping in UI with timezone handling
- **Improved PFOHO Parsing**: Fixed "Bread Stein" email parsing with full content extraction
- **Enhanced Debug Capabilities**: Added debug endpoints for email analysis and troubleshooting
- **Better Error Handling**: Improved JavaScript error handling and user feedback

**Technical improvements**:
- **Email Body Extraction**: Fixed `_extract_text_from_payload()` to handle `multipart/related` structures
- **JavaScript Fixes**: Resolved variable naming conflicts in `addToGoogleCalendar()` function
- **Date Formatting**: Enhanced `formatDate()` function with proper timezone handling
- **Google Calendar URLs**: Robust date/time formatting for Google Calendar integration
- **Event Filtering**: Enhanced mailing list query construction for better email discovery

**Key fixes resolved**:
- **PFOHO Email Issue**: "[PFOHO] Bread Stein TOMORROW (9/24)@9:30" now parses correctly with full content
- **Date Display Bug**: Events now show under correct date groups (Today/Tomorrow/Future)
- **Google Calendar Button**: Fixed non-functional calendar integration with proper URL generation
- **Email Content**: Full email body extraction instead of just mailing list footers

**Migration notes**: 
- Google Calendar integration replaces ICS download functionality
- Enhanced email parsing requires no configuration changes
- UI improvements are backward compatible
- Debug endpoints available for troubleshooting

**Tests added**: 
- Google Calendar URL generation validation
- Email body extraction testing with multipart structures
- Date formatting and timezone handling verification

---

## Open Questions

* Consider improving LLM prompt for better event detection
* Add more robust date/time parsing for edge cases
* Implement better filtering for forwarded emails and replies
* Consider adding confidence scoring for parsed events

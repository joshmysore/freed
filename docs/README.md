# GG.Events Parser Documentation

This directory contains comprehensive documentation for the GG.Events Email Parser system.

## 📁 Files Overview

### Core Documentation
- **`PROJECT.md`** - Complete project overview, architecture, and roadmap
- **`UPDATES.md`** - Detailed changelog of all system updates and improvements

## 🚀 Quick Start

1. **Setup**: Follow the main README.md in the project root
2. **Configuration**: Set up Gmail OAuth and Harvard OpenAI API credentials
3. **Usage**: Run `python src/app.py` and visit `http://localhost:8000`
4. **GG.Events**: Click "Refresh Events" to parse your GG.Events emails

## 📊 System Performance

### Current Statistics (Last 14 Days)
- **Total GG.Events Emails**: 50
- **Successfully Parsed**: 24 events (48% success rate)
- **Mailing Lists Detected**: 8 different lists
- **Event Types**: Workshops, lectures, meetings, concerts, social events

### Successfully Parsed Event Examples
- **Figma Workshop** - Sept 24, Harvard Hall 101 (with mochi donuts and boba)
- **HUMIC Intro Session** - Sept 19, 5:00 PM, Sever Hall 203 (Bonchon dinner)
- **ReCompute 2025 Fall Comp** - Sept 28 (with snacks)
- **De La Rose Concert** - Sept 17, 8:30 PM, Big Night Live
- **Student-Tutor Sustainability Committee Meeting** - Sept 21, 6:00 PM, Holmes Heritage Room

## 🔧 Technical Architecture

### Core Components
1. **Gmail Client** (`src/gmail_client.py`)
   - OAuth2 authentication
   - GG.Events email filtering
   - 14-day search window
   - Mailing list extraction

2. **LLM Parser** (`src/parser_llm.py`)
   - Harvard OpenAI API integration
   - Event extraction from email content
   - JSON schema validation
   - Mailing list tagging

3. **Post-Processor** (`src/postprocess.py`)
   - Time normalization
   - Location cleanup
   - Food detection
   - Data validation

4. **Web Interface** (`src/views/index.html`)
   - Event card display
   - Mailing list badges
   - Expandable email content
   - Manual refresh control

### API Endpoints
- `GET /` - Main web interface
- `GET /health` - System health check
- `GET /events/gg-events` - Parse GG.Events emails
- `POST /ics` - Generate calendar files

## 📈 Parsing Analysis

### Common Issues Identified
1. **Mailing List Footers** (40% of failures)
   - Emails with only 180-character mailing list footers
   - No actual event content

2. **Forwarded Emails** (25% of failures)
   - Poor content structure in forwarded messages
   - Fragmented event information

3. **Date Parsing Issues** (20% of failures)
   - Missing or invalid date_start fields
   - Pydantic validation failures

4. **Non-Event Content** (15% of failures)
   - Job postings and announcements
   - Merchandise sales
   - Administrative messages

### Mailing Lists Detected
- `Pfoho-open` - Pforzheimer House events
- `hcs-discuss` - Harvard Computer Society
- `Outing Club` - Outdoor activities
- `PFOHO` - Pforzheimer House announcements
- `cs-undergrads` - Computer Science events
- `DavisCenterStudents` - Academic events
- `Slavic_languages` - Language department events

## 🎯 Future Improvements

### High Priority
1. **Improve LLM Prompt** - Better event detection for edge cases
2. **Enhanced Date Parsing** - Handle more date formats and edge cases
3. **Forwarded Email Handling** - Better content extraction from forwards
4. **Confidence Scoring** - Add reliability metrics for parsed events

### Medium Priority
1. **Email Content Filtering** - Pre-filter non-event emails
2. **Duplicate Detection** - Identify and merge duplicate events
3. **Event Categorization** - Auto-categorize events by type
4. **Calendar Integration** - Direct calendar sync capabilities

### Low Priority
1. **Mobile Interface** - Responsive design improvements
2. **Event Analytics** - Usage statistics and trends
3. **Multi-Language Support** - International event parsing
4. **API Rate Limiting** - Cost optimization for high-volume usage

## 🔍 Troubleshooting

### Common Issues
1. **No Events Found**
   - Check Gmail credentials
   - Verify GG.Events label exists
   - Ensure emails are from last 14 days

2. **Parsing Failures**
   - Check OpenAI API key
   - Verify Harvard API access
   - Review email content quality

3. **Missing Mailing Lists**
   - Ensure subject lines follow `[XXXXX]` format
   - Check mailing list extraction logic

### Debug Mode
Run with debug logging:
```bash
LOG_LEVEL=DEBUG python src/app.py
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the UPDATES.md for recent changes
3. Examine the parsing analysis in UPDATES.md
4. Check system logs for detailed error information

## 📝 Contributing

When making changes:
1. Update UPDATES.md with detailed change descriptions
2. Test with real GG.Events emails
3. Maintain backward compatibility
4. Document any new features or API changes

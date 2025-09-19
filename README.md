# Email Event Parser

A Python application that parses events from Gmail emails using LLM (Large Language Model) assistance. The system extracts event information, validates it against a strict schema, and provides both CLI and web interfaces for viewing and exporting events.

## Features

- **Gmail Integration**: Read-only access to Gmail emails via OAuth2
- **Harvard OpenAI API**: Uses Harvard's OpenAI Community Developers API with $10/month credits
- **LLM Parsing**: Uses OpenAI GPT-4o-mini to extract structured event data from email content
- **Strict Validation**: Pydantic schema validation ensures data quality
- **Post-processing**: Heuristics for time normalization, location cleanup, and food detection
- **Calendar Export**: Generate ICS files for calendar applications
- **Web Interface**: Simple HTML interface for browsing parsed events
- **CLI Interface**: Command-line tool for batch processing
- **GG.Events Support**: Specialized parsing for Harvard GG.Events mailing list

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <repository-url>
cd freed

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```bash
# Google OAuth Credentials (required)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# OpenAI API Key (Harvard Community Developers)
# Get from: https://go.apis.huit.harvard.edu/ (Harvard API Portal)
# 1. Log in with HarvardKey
# 2. Go to "Apps" in the dropdown menu
# 3. Click "+NEW APP" 
# 4. Enable "AI Services - OpenAI API for Community Developers"
# 5. Copy the generated API key
OPENAI_API_KEY=your_harvard_api_key_here

# Optional: Customize Gmail search query
GMAIL_QUERY=newer_than:14d (subject:invite OR subject:event OR subject:seminar OR subject:talk OR subject:workshop OR subject:session)
```

### 3. Get API Credentials

#### Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth 2.0 Client ID**
6. Choose **Desktop application** as the application type
7. Download the JSON file and rename it to `credentials.json`
8. Place `credentials.json` in the project root
9. Extract the `client_id` and `client_secret` from the JSON file
10. Add them to your `.env` file

#### Harvard OpenAI API Key
1. Go to [Harvard API Portal](https://go.apis.huit.harvard.edu/)
2. Log in with your HarvardKey
3. Click on your username dropdown → "Apps"
4. Click "+NEW APP"
5. Enter a unique app name (e.g., "Email Event Parser - [your initials]")
6. Enable "AI Services - OpenAI API for Community Developers"
7. Click "SAVE" and copy the generated API key
8. Add the API key to your `.env` file

### 4. Run the Application

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the web interface
python src/app.py

# Or run CLI scan
python src/cli.py --help
```

## Usage

### Web Interface

1. Start the server: `make run`
2. Open http://localhost:8000 in your browser
3. Configure search query and click "Scan Emails"
4. View parsed events with highlighted fields
5. Download ICS files for calendar import

### CLI Interface

```bash
# Activate virtual environment first
source venv/bin/activate

# Basic scan with default query
python src/cli.py

# Custom query
python src/cli.py --query "from:events@university.edu" --max-results 5

# Generate ICS files
python src/cli.py --ics

# JSON output
python src/cli.py --json
```

### API Endpoints

- `GET /health` - Health check
- `GET /events/scan?query=...&max_results=10` - Scan and parse events
- `GET /events/gg-events?max_results=50` - Parse GG.Events emails specifically
- `POST /ics` - Generate ICS file from event data

## Project Structure

```
.
├─ src/
│  ├─ app.py                # FastAPI application
│  ├─ cli.py                # CLI interface
│  ├─ gmail_client.py       # Gmail API integration
│  ├─ parser_llm.py         # LLM parsing
│  ├─ schema.py             # Pydantic models
│  ├─ postprocess.py        # Post-processing heuristics
│  ├─ calendar_ics.py       # ICS generation
│  ├─ views/
│  │  └─ index.html         # Web interface
│  └─ utils.py              # Utilities
├─ tests/                   # Test files
├─ prompts/                 # LLM prompt templates
├─ docs/                    # Documentation
└─ requirements.txt         # Dependencies
```

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_schema.py -v
```

### Code Formatting

```bash
# Install formatting tools
pip install black isort

# Format code
black src/ tests/
isort src/ tests/
```

### Linting

```bash
# Install linting tool
pip install ruff

# Lint code
ruff check src/ tests/

## Event Schema

Events are parsed into a strict JSON schema with the following fields:

- `title` (required): Event name
- `date_start` (required): Date in YYYY-MM-DD format
- `time_start`: Start time in HH:MM format
- `time_end`: End time in HH:MM format
- `timezone`: IANA timezone (default: America/New_York)
- `location`: Event location
- `organizer`: Event organizer
- `description`: Event description
- `urls`: List of relevant URLs
- `food_type`: Type of food provided
- `food_quantity_hint`: Food quantity information
- `contacts`: List of contact information
- `source_message_id`: Gmail message ID
- `source_subject`: Email subject

## Roadmap

See [PROJECT.md](docs/PROJECT.md) for detailed roadmap and future features.

## Contributing

1. Follow conventional commit format
2. Update `docs/UPDATES.md` for any changes
3. Add tests for new features
4. Ensure code passes linting and formatting

## License

[Add your license here]

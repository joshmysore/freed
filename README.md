# Harvard Events - Gmail to Web Dashboard

A comprehensive monorepo that ingests labeled emails from Gmail, parses Harvard mailing-list events, stores them in SQLite, and serves them via a modern React dashboard.

## 🏗️ Architecture

- **`ingest/`**: Python Gmail API client with intelligent event parsing and SQLite storage
- **`api/`**: FastAPI service exposing RESTful JSON endpoints with filtering and search
- **`web/`**: Next.js 14 frontend with real-time updates, advanced filtering, and responsive design

## 🚀 Quick Start

### Option 1: Automated Setup
```bash
# Clone and setup everything automatically
git clone <your-repo-url>
cd freed
./setup.sh
```

### Option 2: Manual Setup

1. **Setup Gmail API credentials** (see [Gmail API Setup](#gmail-api-setup))
2. **Install dependencies and run services**:
   ```bash
   # Terminal 1 - API Server
   cd api && pip install -r requirements.txt && uvicorn app:app --reload --port 8000
   
   # Terminal 2 - Data Ingestion
   cd ingest && pip install -r requirements.txt && python main.py --since 60
   
   # Terminal 3 - Web Dashboard
   cd web && npm install && npm run dev
   ```
3. **Open your browser**: [http://localhost:3000](http://localhost:3000)

## 🔧 Gmail API Setup

1. **Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download `credentials.json` to `ingest/` directory

2. **Configure the application**:
   ```bash
   cd ingest
   cp config.example.json config.json
   # Edit config.json with your Gmail label name
   ```

3. **Set up Gmail label**:
   - Create a label in Gmail (e.g., "GG.Events")
   - Apply the label to emails you want to process
   - Update `label_name` in `config.json`

## ✨ Features

### 🎯 Event Parsing
- **Smart Date/Time Detection**: Handles various formats, timezones, and relative dates
- **Location Extraction**: Recognizes Harvard buildings and room numbers
- **Event Type Classification**: Automatically categorizes events (info session, workshop, tech talk, etc.)
- **Food/Free Detection**: Identifies events with food and free status
- **Link Extraction**: Prioritizes Eventbrite and Google Forms links
- **Confidence Scoring**: 0-3 confidence rating for parsing quality

### 🔍 Advanced Filtering
- **Multi-dimensional Filters**: List, type, date range, food, free status
- **Full-text Search**: Search across titles, subjects, and locations
- **Real-time Updates**: Auto-refreshes every 60 seconds
- **Responsive Design**: Works on desktop and mobile

### 📊 Dashboard Features
- **Event Cards**: Rich display with all event information
- **Statistics**: Live stats on total events, food events, free events
- **Sorting Options**: Sort by date, title, list, or type
- **Pagination**: Load events in batches for performance
- **Error Handling**: Graceful error states and retry mechanisms

## 🗄️ Data Model

Events are stored in SQLite with the following key fields:
- **Metadata**: Gmail ID, thread ID, subject, received date
- **Event Details**: Title, start/end time, location, timezone
- **Classification**: Event type, food status, free status, confidence
- **Content**: Links, raw excerpt, parsing metadata

## 🧪 Testing

Run the comprehensive test suite:
```bash
./test.sh
```

This tests:
- Python dependencies
- API server startup
- Database initialization
- Web app build
- End-to-end integration

## 📁 Project Structure

```
hvd-events/
├── ingest/                 # Python Gmail ingestion
│   ├── main.py            # Main ingestion script
│   ├── gmail_client.py    # Gmail API client
│   ├── parser.py          # Event parsing logic
│   ├── models.py          # Data models
│   ├── db.py              # Database operations
│   ├── config.json        # Configuration
│   └── tests/             # Unit tests
├── api/                   # FastAPI service
│   ├── app.py             # FastAPI application
│   └── requirements.txt   # Python dependencies
├── web/                   # Next.js frontend
│   ├── app/               # Next.js 14 App Router
│   ├── lib/               # Utilities and types
│   ├── styles/            # CSS and styling
│   └── package.json       # Node.js dependencies
├── setup.sh               # Automated setup script
├── test.sh                # Test suite
└── README.md              # This file
```

## 🔧 Configuration

### Ingest Configuration (`ingest/config.json`)
```json
{
  "label_name": "GG.Events",
  "gmail_query": "newer_than:60d",
  "timezone": "America/New_York",
  "save_body_text": false,
  "body_max_chars": 20000
}
```

### Web Configuration (`web/.env.local`)
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_DEBUG=false
```

## 🚀 Deployment

### Development
- All services run locally
- Hot reloading enabled
- Debug logging available

### Production
- **API**: Deploy to any Python hosting (Heroku, Railway, AWS)
- **Web**: Deploy to Vercel, Netlify, or any Next.js hosting
- **Database**: SQLite file can be backed up or migrated to PostgreSQL

## 📚 Documentation

- **[Ingest README](ingest/README.md)**: Gmail API setup and event parsing
- **[API README](api/README.md)**: RESTful API documentation
- **[Web README](web/README.md)**: Frontend development guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

1. **"Label not found"**: Ensure Gmail label exists and matches config
2. **"Credentials not found"**: Download credentials.json from Google Cloud Console
3. **"Permission denied"**: Check OAuth scopes and re-authorize
4. **"No events found"**: Verify label is applied to emails and query is correct
5. **API connection errors**: Ensure API server is running on port 8000

### Debug Mode

Enable debug mode in web app:
```env
NEXT_PUBLIC_DEBUG=true
```

### Getting Help

- Check the individual README files in each directory
- Run `./test.sh` to diagnose issues
- Check browser console and API logs for error details

# Freed: Event and Food Finder

🎉 **Discover campus events and delicious food from your mailing lists with AI-powered intelligence.**

Freed is a smart event discovery platform that automatically scans your Gmail for event emails from mailing lists, extracts key information using advanced AI, and presents everything in a beautiful, organized interface. Perfect for students and community members who want to stay on top of campus activities and food offerings.

## ✨ What Makes Freed Special

- **🤖 AI-Powered Parsing**: Uses advanced language models to extract structured event data from unstructured emails
- **🎯 Smart Categorization**: Automatically categorizes events (workshops, lectures, social events, etc.) with confidence scoring
- **🍕 Food Detection**: Identifies food offerings, cuisines, and quantity hints from event descriptions
- **📧 Mailing List Integration**: Seamlessly connects to your Gmail and processes emails from various mailing lists
- **🎨 Modern Interface**: Beautiful dark mode design with intuitive navigation and real-time progress tracking
- **🔍 Intelligent Filtering**: Filter events by date, category, cuisine, mailing list, and food availability

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ installed on your system
- Gmail account with mailing list subscriptions
- Harvard OpenAI API access (for Harvard community members)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/joshmysore/freed.git
   cd freed
   ```

2. **Set up the environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure your credentials**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your API keys (see Configuration section below)
   ```

4. **Run Freed**
   ```bash
   # Start the application
   cd app
   OPENAI_API_KEY=your_api_key_here uvicorn server:app --host 0.0.0.0 --port 8080 --reload
   
   # Open your browser to http://localhost:8080
   ```

## ⚙️ Configuration

### Required: OpenAI API Key (Harvard Community)

1. Visit [Harvard API Portal](https://go.apis.huit.harvard.edu/)
2. Log in with your HarvardKey
3. Go to "Apps" → "+NEW APP"
4. Enable "AI Services - OpenAI API for Community Developers"
5. Copy your API key and add it to `.env`:
   ```bash
   OPENAI_API_KEY=your_harvard_api_key_here
   ```

### Required: Gmail OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable Gmail API
3. Create OAuth 2.0 credentials for a desktop application
4. Download the JSON file and rename it to `credentials.json`
5. Place `credentials.json` in the project root

## 🎯 How to Use

### Web Interface

1. **Launch Freed**: Navigate to http://localhost:8080
2. **Browse Events**: Click "Load Events" to process your mailing list emails
3. **Filter Results**: Use the filter options to find specific types of events or food
4. **View Details**: Click on any event to see full details, food information, and links
5. **Learn More**: Check the "About" page to understand Freed's capabilities

### Key Features

- **📊 Real-time Progress**: Watch as Freed processes your emails with detailed status updates
- **🏷️ Smart Badges**: See event categories, confidence scores, and food types at a glance
- **🔍 Advanced Filters**: Find exactly what you're looking for with multiple filter options
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## 🍕 Event Information Extracted

Freed intelligently extracts and organizes:

- **Basic Info**: Title, description, date, time, location
- **Organization**: Event organizer and contact information
- **Food Details**: Specific food items, cuisines, and quantity hints
- **Categories**: Event type (workshop, lecture, social, etc.)
- **Links**: Registration URLs and relevant web links
- **Source**: Original mailing list and email subject

## 🛠️ Technical Details

### Architecture

- **Backend**: FastAPI with Python 3.8+
- **AI Processing**: OpenAI GPT-4o-mini via Harvard API
- **Email Integration**: Gmail API with OAuth2 authentication
- **Frontend**: Modern HTML5/CSS3/JavaScript with responsive design
- **Data Validation**: Pydantic schemas for robust data handling

### Supported Mailing Lists

Freed automatically processes emails from:
- GG.Events (Harvard)
- HCS Discuss
- Pfoho mailing lists
- CNUGS
- And many more campus mailing lists

## 🔒 Privacy & Security

- **Read-Only Access**: Freed only reads your emails, never modifies or deletes anything
- **Local Processing**: Your email content is processed locally and never stored permanently
- **Secure Authentication**: Uses OAuth2 for secure Gmail access
- **API Efficiency**: Intelligent caching reduces API calls and costs

## 🚧 Development

### Project Structure

```
freed/
├── app/                    # Main application code
│   ├── server.py          # FastAPI web server
│   ├── gmail_client.py    # Gmail integration
│   ├── parser_llm.py      # AI parsing logic
│   └── views/             # Web interface
├── src/                   # Legacy code (backup)
├── backup_v1/            # Previous version backup
└── requirements.txt       # Python dependencies
```

### Running in Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Start with auto-reload
cd app
uvicorn server:app --reload --port 8080
```

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Submit a pull request with a clear description

## 📄 License

This project is open source. Please check the license file for details.

## 🙋‍♂️ Support

Having trouble? Here are some common solutions:

- **Gmail Connection Issues**: Ensure your `credentials.json` is in the project root and properly configured
- **API Errors**: Check that your OpenAI API key is valid and has sufficient credits
- **No Events Found**: Verify you have emails in supported mailing lists within the last 14 days

## 🌟 Acknowledgments

- Built for the Harvard community with love
- Powered by OpenAI's advanced language models
- Designed with modern web technologies and best practices

---

**Ready to discover your next great event? Launch Freed and let AI help you stay connected to campus life! 🎉**
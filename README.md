# Freed: Event and Food Finder

**Discover campus events and delicious food from your mailing lists with AI-powered intelligence.**

Freed is a smart event discovery platform that automatically scans for event emails from mailing lists, extracts key information using advanced AI, and presents everything in a beautiful, organized interface. Perfect for students and community members who want to stay on top of campus activities and food offerings.

## ✨ What Makes Freed Special

- **🤖 AI-Powered Parsing**: Uses advanced language models to extract structured event data from unstructured emails
- **🎯 Smart Categorization**: Automatically categorizes events (workshops, lectures, social events, etc.) with confidence scoring
- **🍕 Food Detection**: Identifies food offerings, cuisines, and quantity hints from event descriptions
- **📧 Mailing List Integration**: Processes emails from various mailing lists
- **🎨 Modern Interface**: Beautiful dark mode design with intuitive navigation and real-time progress tracking
- **🔍 Intelligent Filtering**: Filter events by date, category, cuisine, mailing list, and food availability

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

## 📄 License

This project is open source. Please check the license file for details.


## 🌟 Acknowledgments

- Built for the Harvard community with love
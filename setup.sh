#!/bin/bash

# Harvard Events Setup Script
# This script sets up the entire Harvard Events system

set -e

echo "🚀 Setting up Harvard Events system..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p ingest/tests
mkdir -p api
mkdir -p web/app/components
mkdir -p web/app/events
mkdir -p web/lib
mkdir -p web/styles

# Setup Python environment for ingest
echo "🐍 Setting up Python environment for ingest..."
cd ingest
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in ingest directory"
    exit 1
fi

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$python_version < 3.11" | bc -l)" -eq 1 ]; then
    echo "⚠️  Warning: Python 3.11+ recommended. Current version: $python_version"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f "config.json" ]; then
    echo "📝 Creating config.json from example..."
    cp config.example.json config.json
    echo "✅ Created config.json - please edit it with your Gmail settings"
fi

cd ..

# Setup Python environment for API
echo "🐍 Setting up Python environment for API..."
cd api
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in api directory"
    exit 1
fi

pip3 install -r requirements.txt
cd ..

# Setup Node.js environment for web
echo "📦 Setting up Node.js environment for web..."
cd web

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check Node.js version
node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current version: $(node --version)"
    exit 1
fi

# Install dependencies
if command -v pnpm &> /dev/null; then
    echo "📦 Installing dependencies with pnpm..."
    pnpm install
elif command -v yarn &> /dev/null; then
    echo "📦 Installing dependencies with yarn..."
    yarn install
else
    echo "📦 Installing dependencies with npm..."
    npm install
fi

# Create environment file
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local..."
    cp env.example .env.local
    echo "✅ Created .env.local - using default API URL"
fi

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. 🔐 Gmail API Setup:"
echo "   - Go to Google Cloud Console"
echo "   - Create a project and enable Gmail API"
echo "   - Download credentials.json to ingest/ directory"
echo "   - Edit ingest/config.json with your settings"
echo ""
echo "2. 🏃‍♂️ Run the system:"
echo "   # Terminal 1 - Start API server"
echo "   cd api && uvicorn app:app --reload --port 8000"
echo ""
echo "   # Terminal 2 - Run ingestion"
echo "   cd ingest && python main.py --since 60"
echo ""
echo "   # Terminal 3 - Start web app"
echo "   cd web && npm run dev"
echo ""
echo "3. 🌐 Open your browser:"
echo "   - Web app: http://localhost:3000"
echo "   - API docs: http://localhost:8000/docs"
echo ""
echo "📚 For detailed instructions, see the README files in each directory."
echo ""
echo "🎉 Happy event hunting!"

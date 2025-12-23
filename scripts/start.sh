#!/bin/bash

# SOC Agent Automation - Quick Start Script

echo "🚀 Starting SOC Agent Automation..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run scripts/setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python3 -c "import streamlit, mcp_use, langchain_groq, dotenv, apscheduler, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed. Please run scripts/setup.sh first."
    exit 1
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from src.database.models import init_db; init_db()"

# Start the application
echo "🌟 Launching SOC Agent Automation Platform..."
echo "🔗 The application will open in your default browser"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

streamlit run main.py
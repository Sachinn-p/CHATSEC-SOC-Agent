#!/bin/bash

# SOC Agent Automation - Development Setup Script

echo "🚀 Setting up SOC Agent Automation development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Python version: $python_version"

# Check if Python >= 3.10
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.10+ is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, installing basic dependencies..."
    pip install streamlit mcp-use langchain-groq python-dotenv apscheduler pandas
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install pytest pytest-asyncio black flake8 mypy pre-commit

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env file from .env.example"
        echo "⚠️ Please edit .env file with your configuration values"
    else
        echo "⚠️ .env.example file not found"
    fi
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p temp

# Run initial database setup
echo "🗄️ Initializing database..."
python3 -c "from src.database.models import init_db; init_db()" 2>/dev/null || echo "⚠️ Database initialization will be done on first run"

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'streamlit run main.py' to start the application"
echo ""
echo "🔧 Development commands:"
echo "- Format code: black ."
echo "- Lint code: flake8 ."
echo "- Type check: mypy ."
echo "- Run tests: pytest"
@echo off
REM SOC Agent Automation - Windows Development Setup Script

echo 🚀 Setting up SOC Agent Automation development environment...

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📦 Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt not found, installing basic dependencies...
    pip install streamlit mcp-use langchain-groq python-dotenv apscheduler pandas
)

REM Install development dependencies
echo 📦 Installing development dependencies...
pip install pytest pytest-asyncio black flake8 mypy pre-commit

REM Setup pre-commit hooks
echo 🔧 Setting up pre-commit hooks...
pre-commit install

REM Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo 📝 Created .env file from .env.example
        echo ⚠️ Please edit .env file with your configuration values
    ) else (
        echo ⚠️ .env.example file not found
    )
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

REM Run initial database setup
echo 🗄️ Initializing database...
python -c "from src.database.models import init_db; init_db()" 2>nul || echo ⚠️ Database initialization will be done on first run

echo ✅ Development environment setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run 'venv\Scripts\activate.bat' to activate the virtual environment
echo 3. Run 'streamlit run main.py' to start the application
echo.
echo 🔧 Development commands:
echo - Format code: black .
echo - Lint code: flake8 .
echo - Type check: mypy .
echo - Run tests: pytest

pause
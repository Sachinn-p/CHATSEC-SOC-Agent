#!/bin/bash

# SOC Agent Automation - Development Tools Script

echo "🔧 SOC Agent Automation Development Tools"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

case "$1" in
    "format")
        echo "🎨 Formatting code with Black..."
        black src/ config/ *.py
        echo "✅ Code formatting complete"
        ;;
    "lint")
        echo "🔍 Linting code with Flake8..."
        flake8 src/ config/ *.py
        echo "✅ Code linting complete"
        ;;
    "type-check")
        echo "📝 Type checking with MyPy..."
        mypy src/ config/ *.py
        echo "✅ Type checking complete"
        ;;
    "test")
        echo "🧪 Running tests with Pytest..."
        pytest tests/ -v
        echo "✅ Tests complete"
        ;;
    "test-cov")
        echo "🧪 Running tests with coverage..."
        pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term
        echo "✅ Tests with coverage complete"
        echo "📊 Coverage report generated in htmlcov/"
        ;;
    "clean")
        echo "🧹 Cleaning up temporary files..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find . -type f -name "*.pyc" -delete
        rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ dist/ build/ *.egg-info/
        echo "✅ Cleanup complete"
        ;;
    "deps")
        echo "📦 Installing/updating dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio black flake8 mypy pre-commit
        echo "✅ Dependencies updated"
        ;;
    "db-reset")
        echo "🗄️ Resetting database..."
        rm -f *.db *.sqlite *.sqlite3
        python3 -c "from src.database.models import init_db; init_db()"
        echo "✅ Database reset complete"
        ;;
    "all")
        echo "🚀 Running all checks..."
        echo ""
        
        echo "🎨 Formatting code..."
        black src/ config/ *.py
        echo ""
        
        echo "🔍 Linting code..."
        flake8 src/ config/ *.py
        echo ""
        
        echo "📝 Type checking..."
        mypy src/ config/ *.py
        echo ""
        
        echo "🧪 Running tests..."
        pytest tests/ -v
        echo ""
        
        echo "✅ All checks complete"
        ;;
    *)
        echo "Usage: $0 {format|lint|type-check|test|test-cov|clean|deps|db-reset|all}"
        echo ""
        echo "Commands:"
        echo "  format      - Format code with Black"
        echo "  lint        - Lint code with Flake8"
        echo "  type-check  - Type check with MyPy"
        echo "  test        - Run tests with Pytest"
        echo "  test-cov    - Run tests with coverage report"
        echo "  clean       - Clean up temporary files"
        echo "  deps        - Install/update dependencies"
        echo "  db-reset    - Reset database"
        echo "  all         - Run all checks (format, lint, type-check, test)"
        ;;
esac
# Makefile for SOC Agent Automation

.PHONY: help setup install dev test clean format lint type-check run all

# Default target
help:
	@echo "SOC Agent Automation - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  setup       - Set up development environment"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Install development dependencies"
	@echo "  run         - Run the application"
	@echo "  test        - Run tests"
	@echo "  test-cov    - Run tests with coverage report"
	@echo "  format      - Format code with Black"
	@echo "  lint        - Lint code with Flake8"
	@echo "  type-check  - Type check with MyPy"
	@echo "  clean       - Clean up temporary files"
	@echo "  all         - Run format, lint, type-check, and test"
	@echo ""

# Setup development environment
setup:
	@echo "🚀 Setting up development environment..."
	python3 -m venv venv
	@echo "✅ Virtual environment created"
	@echo "Run 'source venv/bin/activate' to activate it"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

# Install development dependencies
dev: install
	@echo "📦 Installing development dependencies..."
	pip install pytest pytest-asyncio black flake8 mypy pre-commit
	pre-commit install

# Run the application
run:
	@echo "🚀 Starting SOC Agent Automation..."
	streamlit run main.py

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/"

# Format code
format:
	@echo "🎨 Formatting code with Black..."
	black src/ config/ *.py

# Lint code
lint:
	@echo "🔍 Linting code with Flake8..."
	flake8 src/ config/ *.py

# Type check
type-check:
	@echo "📝 Type checking with MyPy..."
	mypy src/ config/ *.py

# Clean temporary files
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ dist/ build/ *.egg-info/
	@echo "✅ Cleanup complete"

# Run all checks
all: format lint type-check test
	@echo "✅ All checks completed successfully"

# Quick start for new developers
quick-start: setup install dev
	@echo ""
	@echo "🎉 Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Activate virtual environment: source venv/bin/activate"
	@echo "2. Copy environment file: cp .env.example .env"
	@echo "3. Edit .env with your configuration"
	@echo "4. Run the application: make run"
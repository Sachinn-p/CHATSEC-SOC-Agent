"""
Test configuration and fixtures for SOC Agent Automation tests.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock

from config.settings import TestConfig
from src.database.models import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        temp_db_path = tmp_file.name
    
    # Create database manager with temp DB
    db_manager = DatabaseManager(temp_db_path)
    db_manager.init_db()
    
    yield db_manager
    
    # Cleanup
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    agent = Mock()
    agent.run.return_value = "Test response from agent"
    return agent


@pytest.fixture
def test_config():
    """Create test configuration"""
    return TestConfig()


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing"""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with security monitoring?"},
        {"role": "assistant", "content": "Of course! I can help you monitor your security systems."}
    ]
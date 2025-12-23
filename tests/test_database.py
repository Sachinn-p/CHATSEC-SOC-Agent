"""
Tests for database models and operations.
"""
import pytest
from datetime import datetime

from src.database.models import DatabaseManager


def test_database_initialization(temp_db):
    """Test database initialization"""
    # Database should be initialized by fixture
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['messages', 'tools_log', 'preferences', 'proactive_agents']
        for table in expected_tables:
            assert table in tables


def test_save_and_get_messages(temp_db):
    """Test saving and retrieving messages"""
    # Save test messages
    message_id = temp_db.save_message("user", "Test message", "test_session")
    assert isinstance(message_id, int)
    
    # Retrieve messages
    messages = temp_db.get_all_messages("test_session")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test message"


def test_save_and_get_tool_logs(temp_db):
    """Test saving and retrieving tool logs"""
    # Save test tool log
    log_id = temp_db.save_tool_log("test_tool", "Test usage", "test_session")
    assert isinstance(log_id, int)
    
    # Retrieve tool logs
    logs = temp_db.get_all_tool_logs("test_session")
    assert len(logs) == 1
    assert logs[0]["tool_name"] == "test_tool"
    assert logs[0]["usage"] == "Test usage"


def test_user_preferences(temp_db):
    """Test user preferences operations"""
    # Get default preferences
    prefs = temp_db.get_user_preferences()
    assert "enabled" in prefs
    assert "interval" in prefs
    
    # Update preferences
    temp_db.update_user_preferences(False, 120)
    
    # Check updated preferences
    updated_prefs = temp_db.get_user_preferences()
    assert updated_prefs["enabled"] is False
    assert updated_prefs["interval"] == 120


def test_proactive_agents(temp_db):
    """Test proactive agent operations"""
    # Save proactive agent
    agent_id = temp_db.save_proactive_agent("test_agent", "Test prompt", 30)
    assert isinstance(agent_id, int)
    
    # Get proactive agents
    agents = temp_db.get_proactive_agents()
    assert len(agents) == 1
    assert agents[0]["name"] == "test_agent"
    assert agents[0]["prompt"] == "Test prompt"
    assert agents[0]["interval_minutes"] == 30
    
    # Update last run
    temp_db.update_proactive_agent_last_run("test_agent")
    
    # Check last run was updated
    updated_agents = temp_db.get_proactive_agents()
    assert updated_agents[0]["last_run"] is not None
    
    # Delete proactive agent
    temp_db.delete_proactive_agent("test_agent")
    
    # Check agent was deleted
    remaining_agents = temp_db.get_proactive_agents()
    assert len(remaining_agents) == 0
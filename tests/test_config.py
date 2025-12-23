"""
Tests for configuration settings.
"""
import pytest
import os
from unittest.mock import patch

from config.settings import Config, DevelopmentConfig, ProductionConfig, TestConfig, get_config


def test_config_initialization():
    """Test configuration class initialization"""
    config = Config()
    assert hasattr(config, 'DATABASE_FILE')
    assert hasattr(config, 'GROQ_API_KEY')
    assert hasattr(config, 'MAX_AGENT_STEPS')


def test_mcp_config_generation():
    """Test MCP configuration generation"""
    config = Config()
    mcp_config = config.get_mcp_config()
    
    assert "mcpServers" in mcp_config
    assert "wazuh" in mcp_config["mcpServers"]
    assert "command" in mcp_config["mcpServers"]["wazuh"]
    assert "env" in mcp_config["mcpServers"]["wazuh"]


@patch.dict(os.environ, {
    'GROQ_API_KEY': 'test_key',
    'MCP_COMMAND': 'test_command',
    'WAZUH_API_PASSWORD': 'test_password',
    'WAZUH_INDEXER_PASSWORD': 'test_password'
})
def test_config_validation():
    """Test configuration validation"""
    config = Config()
    assert config.validate_config() is True


def test_config_validation_failure():
    """Test configuration validation failure"""
    config = Config()
    with pytest.raises(ValueError):
        config.validate_config()


def test_development_config():
    """Test development configuration"""
    config = DevelopmentConfig()
    assert config.DEBUG is True


def test_production_config():
    """Test production configuration"""
    config = ProductionConfig()
    assert config.DEBUG is False


def test_test_config():
    """Test configuration for testing"""
    config = TestConfig()
    assert config.DEBUG is True
    assert config.DATABASE_FILE == ":memory:"


@patch.dict(os.environ, {'FLASK_ENV': 'production'})
def test_get_config():
    """Test getting configuration based on environment"""
    config = get_config()
    assert isinstance(config, ProductionConfig)
    
    config_dev = get_config('development')
    assert isinstance(config_dev, DevelopmentConfig)
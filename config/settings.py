"""
Configuration settings for the SOC Agent Automation application.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Main configuration class"""
    
    # Database settings
    DATABASE_FILE = os.getenv("DATABASE_FILE", "chat_logs.db")
    
    # Groq LLM settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
    
    # MCP settings  
    MCP_COMMAND = os.getenv("MCP_COMMAND")
    
    # Wazuh API settings
    WAZUH_API_HOST = os.getenv("WAZUH_API_HOST", "127.0.0.1")
    WAZUH_API_PORT = os.getenv("WAZUH_API_PORT", "55000")
    WAZUH_API_USERNAME = os.getenv("WAZUH_API_USERNAME", "admin")
    WAZUH_API_PASSWORD = os.getenv("WAZUH_API_PASSWORD")
    
    # Wazuh Indexer settings
    WAZUH_INDEXER_HOST = os.getenv("WAZUH_INDEXER_HOST", "127.0.0.1")
    WAZUH_INDEXER_PORT = os.getenv("WAZUH_INDEXER_PORT", "9200")
    WAZUH_INDEXER_USERNAME = os.getenv("WAZUH_INDEXER_USERNAME", "admin")
    WAZUH_INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD")
    
    # SSL and protocol settings
    WAZUH_VERIFY_SSL = os.getenv("WAZUH_VERIFY_SSL", "false")
    WAZUH_TEST_PROTOCOL = os.getenv("WAZUH_TEST_PROTOCOL", "http")
    
    # Logging
    RUST_LOG = os.getenv("RUST_LOG", "info")
    
    # Agent settings
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "10"))
    DEFAULT_PROACTIVE_INTERVAL = int(os.getenv("DEFAULT_PROACTIVE_INTERVAL", "60"))
    
    @classmethod
    def _resolve_command_path(cls) -> str:
        """Resolve MCP command path to absolute path if it's relative"""
        cmd = cls.MCP_COMMAND
        if not cmd:
            return cmd
        
        # Split command and arguments
        parts = cmd.split()
        if not parts:
            return cmd
        
        # Check if first part looks like a relative path to a Python script
        first_part = parts[0]
        if first_part.endswith('.py') and not os.path.isabs(first_part):
            # Resolve relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            abs_path = os.path.join(project_root, first_part)
            
            if os.path.exists(abs_path):
                # Reconstruct command with absolute path
                parts[0] = abs_path
                return ' '.join(parts)
        
        return cmd
    
    @classmethod
    def get_mcp_config(cls) -> Dict[str, Any]:
        """Get MCP server configuration"""
        resolved_command = cls._resolve_command_path()
        
        return {
            "mcpServers": {
                "wazuh": {
                    "command": resolved_command,
                    "args": [],
                    "env": {
                        "WAZUH_API_HOST": cls.WAZUH_API_HOST,
                        "WAZUH_API_PORT": cls.WAZUH_API_PORT,
                        "WAZUH_API_USERNAME": cls.WAZUH_API_USERNAME,
                        "WAZUH_API_PASSWORD": cls.WAZUH_API_PASSWORD,
                        "WAZUH_INDEXER_HOST": cls.WAZUH_INDEXER_HOST,
                        "WAZUH_INDEXER_PORT": cls.WAZUH_INDEXER_PORT,
                        "WAZUH_INDEXER_USERNAME": cls.WAZUH_INDEXER_USERNAME,
                        "WAZUH_INDEXER_PASSWORD": cls.WAZUH_INDEXER_PASSWORD,
                        "WAZUH_VERIFY_SSL": cls.WAZUH_VERIFY_SSL,
                        "WAZUH_TEST_PROTOCOL": cls.WAZUH_TEST_PROTOCOL,
                        "RUST_LOG": cls.RUST_LOG
                    }
                }
            }
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            cls.GROQ_API_KEY,
            cls.WAZUH_API_PASSWORD,
            cls.WAZUH_INDEXER_PASSWORD
        ]
        
        missing = [var for var in required_vars if not var]
        if missing:
            raise ValueError(f"Missing required configuration variables: {missing}")
        
        # MCP_COMMAND is optional
        if not cls.MCP_COMMAND:
            print("⚠️ MCP_COMMAND not set - Wazuh tools will not be available")
        
        return True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestConfig(Config):
    """Test configuration"""
    DEBUG = True
    DATABASE_FILE = ":memory:"  # Use in-memory database for tests


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,  
    'testing': TestConfig
}


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    env = env or os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)()
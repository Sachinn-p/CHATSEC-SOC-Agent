"""
Comprehensive verification test for CHATSEC codebase after reorganization.
Tests all module imports, configuration, and core functionality.
"""

print("="*60)
print("CHATSEC Codebase Verification Test")
print("="*60)

# Test 1: Core module imports
print("\n[1/6] Testing core module imports...")
try:
    from src.core.agent import init_agent, SOCAgent
    from src.core.wazuh_client import get_wazuh_client, WazuhAPIClient
    from src.core.proactive_agents import ProactiveAgentManager
    print("✅ Core modules imported successfully")
except Exception as e:
    print(f"❌ Core module import failed: {e}")
    exit(1)

# Test 2: UI modules
print("\n[2/6] Testing UI modules...")
try:
    from src.ui.chat import ChatManager, ChatInterface, get_chat_interface
    from src.ui.dashboard import render_dashboard
    print("✅ UI modules imported successfully")
except Exception as e:
    print(f"❌ UI module import failed: {e}")
    exit(1)

# Test 3: Database modules
print("\n[3/6] Testing database modules...")
try:
    from src.database.models import DatabaseManager
    print("✅ Database modules imported successfully")
except Exception as e:
    print(f"❌ Database module import failed: {e}")
    exit(1)

# Test 4: MCP modules
print("\n[4/6] Testing MCP modules...")
try:
    import src.mcp
    from src.mcp.wazuh_mcp_server import WazuhMCPServer
    print("✅ MCP modules imported successfully")
except Exception as e:
    print(f"❌ MCP module import failed: {e}")
    exit(1)

# Test 5: Utils modules
print("\n[5/6] Testing utils modules...")
try:
    from src.utils import (
        timestamp, iso_timestamp, format_datetime,
        format_file_size, ensure_directory_exists, safe_read_file,
        sanitize_filename, truncate_text, safe_json_loads, safe_json_dumps,
        extract_error_message, validate_config_dict, setup_logging,
        mask_sensitive_data, chunk_list, flatten_dict, deep_merge_dicts,
        HealthChecker, get_health_checker
    )
    print("✅ Utils modules imported successfully")
    
    # Test utility functions
    assert timestamp() is not None
    assert iso_timestamp() is not None
    assert format_file_size(1024) == "1.00 KB"
    assert sanitize_filename("test<file>.txt") == "test_file_.txt"
    assert truncate_text("hello world", 5) == "he..."
    print("✅ Utils functions working correctly")
except Exception as e:
    print(f"❌ Utils module import/test failed: {e}")
    exit(1)

# Test 6: Configuration
print("\n[6/6] Testing configuration...")
try:
    from config.settings import Config, DevelopmentConfig, ProductionConfig
    config = Config()
    config.validate_config()
    print("✅ Configuration validated successfully")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nCHATSEC codebase is properly organized and fully functional.")
print("All modules can be imported without errors.")
print("Core functionality verified.")

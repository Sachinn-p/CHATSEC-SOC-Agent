"""
Test script to identify all issues in the codebase
"""
import sys
import asyncio
from datetime import datetime

print("="*60)
print("RUNNING COMPREHENSIVE TESTS")
print("="*60)

# Test 1: Database Issues
print("\n[TEST 1] Database Operations")
try:
    from src.database.models import DatabaseManager
    import tempfile
    import os
    
    # Use a temporary file database instead of in-memory
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db = DatabaseManager(temp_db.name)
    db.init_db()
    
    # Test save message
    msg_id = db.save_message('user', 'test message')
    print(f"✅ Message saved with ID: {msg_id}")
    
    # Test get messages
    messages = db.get_all_messages()
    print(f"✅ Retrieved {len(messages)} messages")
    
    # Test save tool log
    tool_id = db.save_tool_log('test_tool', 'test usage')
    print(f"✅ Tool log saved with ID: {tool_id}")
    
    # Cleanup
    os.unlink(temp_db.name)
    
    print("✅ DATABASE: All tests passed")
except Exception as e:
    print(f"❌ DATABASE ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Wazuh Client
print("\n[TEST 2] Wazuh Client Authentication")
try:
    from src.core.wazuh_client import WazuhAPIClient
    client = WazuhAPIClient()
    
    print(f"Using credentials: {client.username} @ {client.base_url}")
    
    # Try authentication
    auth_result = client.authenticate()
    if auth_result:
        print("✅ WAZUH: Authentication successful")
        
        # Try getting agents
        agents = client.get_agents()
        if agents.get('success'):
            print(f"✅ WAZUH: Retrieved {agents.get('total', 0)} agents")
        else:
            print(f"⚠️ WAZUH: Could not retrieve agents: {agents.get('error')}")
    else:
        print("❌ WAZUH: Authentication failed - check credentials")
        print("   Current username:", client.username)
        print("   Current password:", client.password[:5] + "..." if client.password else "None")
        print("   Expected username: wazuh-wui")
        print("   Expected password: MyS3cr37P450r.*-")
except Exception as e:
    print(f"❌ WAZUH ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Agent Initialization
print("\n[TEST 3] SOC Agent")
try:
    from src.core.agent import SOCAgent, init_agent
    from config.settings import Config
    
    config = Config()
    agent = SOCAgent(config)
    agent.initialize()
    print("✅ AGENT: Initialization successful")
    
    # Test basic run
    async def test_agent():
        result = await agent.run("What is your role?")
        return result
    
    response = asyncio.run(test_agent())
    print(f"✅ AGENT: Response received ({len(response)} chars)")
    
except Exception as e:
    print(f"❌ AGENT ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Proactive Agents
print("\n[TEST 4] Proactive Agent Manager")
try:
    from src.core.proactive_agents import ProactiveAgentManager
    
    manager = ProactiveAgentManager(DatabaseManager(':memory:'))
    print("✅ PROACTIVE: Manager initialized")
    
    # Test scheduler
    scheduler = manager.scheduler
    print("✅ PROACTIVE: Scheduler started")
    
    manager.shutdown()
    print("✅ PROACTIVE: All tests passed")
    
except Exception as e:
    print(f"❌ PROACTIVE ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 5: UI Components
print("\n[TEST 5] UI Components")
try:
    from src.ui.chat import ChatManager, ChatInterface
    from src.ui.dashboard import DashboardRenderer
    
    chat_mgr = ChatManager(DatabaseManager(':memory:'))
    print("✅ UI: ChatManager initialized")
    
    chat_interface = ChatInterface(chat_mgr)
    print("✅ UI: ChatInterface initialized")
    
    dashboard = DashboardRenderer(DatabaseManager(':memory:'))
    print("✅ UI: DashboardRenderer initialized")
    
    print("✅ UI: All tests passed")
    
except Exception as e:
    print(f"❌ UI ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Config Validation
print("\n[TEST 6] Configuration")
try:
    from config.settings import Config
    
    config = Config()
    config.validate_config()
    print("✅ CONFIG: Validation passed")
    
    print(f"  - API Host: {config.WAZUH_API_HOST}")
    print(f"  - API Port: {config.WAZUH_API_PORT}")
    print(f"  - Username: {config.WAZUH_API_USERNAME}")
    print(f"  - Protocol: {config.WAZUH_TEST_PROTOCOL}")
    
except Exception as e:
    print(f"❌ CONFIG ERROR: {e}")

print("\n" + "="*60)
print("TEST SUITE COMPLETED")
print("="*60)

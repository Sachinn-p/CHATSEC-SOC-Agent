#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')

# Test the MCP server WazuhClient
from src.mcp.wazuh_mcp_server import wazuh_client

print("Testing WazuhClient from MCP server...")
print(f"Base URL: {wazuh_client.base_url}")
print(f"Username: {wazuh_client.username}")
print(f"Verify SSL: {wazuh_client.verify_ssl}")

if wazuh_client.authenticate():
    print("✓ Authentication successful!")
    
    agents = wazuh_client.get_agents()
    print(f"\nFound {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent.get('name')} (ID: {agent.get('id')}, Status: {agent.get('status')})")
    
    alerts = wazuh_client.get_alerts(hours=24)
    print(f"\nFound {len(alerts)} alerts in last 24 hours")
else:
    print("✗ Authentication failed!")

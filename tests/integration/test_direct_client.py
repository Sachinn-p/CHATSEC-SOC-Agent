#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')

# Import directly from wazuh_client
from src.core.wazuh_client import WazuhAPIClient

client = WazuhAPIClient()
if client.authenticate():
    print("✓ WazuhAPIClient Authentication successful!")
    
    # Get agents
    agents_result = client.get_agents()
    if isinstance(agents_result, dict):
        agents = agents_result.get("agents", [])
        print(f"Found {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent.get('name')} (Status: {agent.get('status')})")
    
    # Get critical alerts
    print("\nCritical alerts for win-001:")
    alerts_result = client.get_critical_alerts(agent_name='win-001', hours=24)
    if isinstance(alerts_result, dict):
        if alerts_result.get("success"):
            total = alerts_result.get("total_critical_alerts", 0)
            print(f"Found {total} critical alerts")
        else:
            print(f"Error: {alerts_result.get('error')}")
else:
    print("✗ Authentication failed")

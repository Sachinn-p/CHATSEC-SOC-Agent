#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')
from src.core.wazuh_client import WazuhAPIClient

client = WazuhAPIClient()
if client.authenticate():
    print('=' * 70)
    print('CRITICAL ALERTS FOR win-001 (Last 24 Hours)')
    print('=' * 70)
    
    result = client.get_critical_alerts(hours=24, agent_name='win-001')
    
    if 'error' in result:
        print(f'Error: {result["error"]}')
    else:
        alerts = result.get('data', {}).get('affected_items', [])
        total = result.get('data', {}).get('total_affected_items', 0)
        print(f'\nTotal Critical Alerts: {total}')
        
        if alerts:
            print(f'\nShowing first {len(alerts)} alerts:\n')
            for i, alert in enumerate(alerts[:10], 1):
                rule_id = alert.get('rule', {}).get('id', 'N/A')
                rule_level = alert.get('rule', {}).get('level', 'N/A')
                desc = alert.get('rule', {}).get('description', 'N/A')
                timestamp = alert.get('timestamp', 'N/A')
                agent_name = alert.get('agent', {}).get('name', 'N/A')
                
                print(f"{i}. Rule {rule_id} | Level {rule_level}")
                print(f"   Agent: {agent_name}")
                print(f"   Time: {timestamp}")
                print(f"   Description: {desc[:80]}")
                print()
        else:
            print('\nNo critical alerts found for win-001 in the last 24 hours.')
else:
    print('Authentication failed')

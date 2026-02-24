"""Test critical alerts query for win-001"""
from src.core.wazuh_client import get_wazuh_client

client = get_wazuh_client()

# Test authentication
auth_result = client.authenticate()
print(f"Authentication: {'SUCCESS' if auth_result else 'FAILED'}")

if auth_result:
    # Query critical alerts for win-001
    result = client.get_critical_alerts(hours=24, agent_name='win-001')
    
    print(f"\nSuccess: {result.get('success')}")
    print(f"Critical alerts for win-001: {result.get('total_critical', 0)}")
    
    if result.get('error'):
        print(f"Error: {result.get('error')}")
    
    if result.get('critical_alerts'):
        print(f"\nShowing first 3 alerts:")
        for i, alert in enumerate(result['critical_alerts'][:3], 1):
            rule = alert.get('rule', {})
            print(f"{i}. {rule.get('description', 'N/A')} (Level: {rule.get('level', 'N/A')})")

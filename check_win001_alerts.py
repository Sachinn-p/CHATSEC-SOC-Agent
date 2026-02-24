"""Quick test for win-001 alerts with correct credentials"""
import sys
sys.path.insert(0, 'C:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')

from src.core.wazuh_client import get_wazuh_client

print("Testing Wazuh connection and querying win-001 alerts...")

client = get_wazuh_client()

# Test authentication
auth_result = client.authenticate()
print(f"\nAuthentication: {'SUCCESS' if auth_result else 'FAILED'}")

if auth_result:
    # Query critical alerts for win-001
    result = client.get_critical_alerts(hours=24, agent_name='win-001')
    
    print(f"\n{'='*60}")
    print(f"CRITICAL ALERTS FOR WIN-001 (Last 24 hours)")
    print(f"{'='*60}")
    print(f"Success: {result.get('success')}")
    print(f"Total Critical Alerts: {result.get('total_critical', 0)}")
    
    if result.get('error'):
        print(f"Error: {result.get('error')}")
    
    if result.get('critical_alerts') and len(result['critical_alerts']) > 0:
        print(f"\n⚠️ Found {len(result['critical_alerts'])} critical alerts:")
        for i, alert in enumerate(result['critical_alerts'][:5], 1):
            rule = alert.get('rule', {})
            timestamp = alert.get('timestamp', 'N/A')
            print(f"\n  {i}. {rule.get('description', 'N/A')}")
            print(f"     Level: {rule.get('level', 'N/A')} | Time: {timestamp}")
    else:
        print(f"\n✅ No critical issues found for win-001!")
else:
    print("\n❌ Cannot query - authentication failed")
    print("Check that Wazuh services are running:")
    print("  docker exec single-node-wazuh.manager-1 /var/ossec/bin/wazuh-control status")

"""
Test script for the new CURL tool functionality
"""
import asyncio
from src.core.agent import SOCAgent
from config.settings import Config

print("="*60)
print("TESTING CURL TOOL")
print("="*60)

# Initialize agent
print("\n[1] Initializing SOC Agent...")
config = Config()
agent = SOCAgent(config)
agent.initialize()
print("[OK] Agent initialized")

# Test 1: Direct Wazuh API query
print("\n[2] Testing direct Wazuh API query...")
result = agent.query_wazuh_api('/agents')
if result.get('success'):
    print(f"[OK] API query successful")
    print(f"    Status Code: {result['status_code']}")
    if isinstance(result['data'], dict):
        total_agents = result['data'].get('data', {}).get('total_affected_items', 0)
        print(f"    Total Agents: {total_agents}")
else:
    print(f"[ERROR] API query failed: {result.get('error')}")

# Test 2: Query specific agent
print("\n[3] Testing query with parameters...")
result = agent.query_wazuh_api('/agents', {'status': 'active'})
if result.get('success'):
    print(f"[OK] Parameterized query successful")
    if isinstance(result['data'], dict):
        agents = result['data'].get('data', {}).get('affected_items', [])
        print(f"    Active Agents: {len(agents)}")
        for ag in agents[:3]:  # Show first 3
            print(f"    - {ag.get('name')} (ID: {ag.get('id')})")
else:
    print(f"[ERROR] Query failed: {result.get('error')}")

# Test 3: Execute custom curl
print("\n[4] Testing custom curl execution...")
base_url = f"{config.WAZUH_TEST_PROTOCOL}://{config.WAZUH_API_HOST}:{config.WAZUH_API_PORT}"
url = f"{base_url}/security/user/authenticate"
result = agent.execute_curl(
    url=url,
    method="GET",
    auth=(config.WAZUH_API_USERNAME, config.WAZUH_API_PASSWORD),
    verify_ssl=False
)
if result.get('success'):
    print(f"[OK] Authentication via curl successful")
    print(f"    Status Code: {result['status_code']}")
else:
    print(f"[ERROR] Curl failed: {result.get('error')}")

# Test 4: Test querying alerts for specific agent
print("\n[5] Testing alerts query for win-001...")
result = agent.query_wazuh_api('/alerts', {
    'agent_name': 'win-001',
    'limit': 10
})
if result.get('success'):
    print(f"[OK] Alerts query successful")
    print(f"    Status Code: {result['status_code']}")
    if isinstance(result['data'], dict):
        alerts = result['data'].get('data', {}).get('affected_items', [])
        print(f"    Found {len(alerts)} alerts")
else:
    print(f"[INFO] Alerts endpoint response: {result.get('status_code')}")
    print(f"    Note: May need indexer for alerts")

print("\n" + "="*60)
print("CURL TOOL TESTS COMPLETED")
print("="*60)
print("\nYou can now use these methods:")
print("  - agent.execute_curl(url, method, headers, auth)")
print("  - agent.query_wazuh_api(endpoint, params)")
print("\nExample for win-001 critical alerts:")
print("  result = agent.query_wazuh_api('/agents/001/alerts', {'severity': '4'})")

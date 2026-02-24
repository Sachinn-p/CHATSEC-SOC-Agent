#!/usr/bin/env python3
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import json

urllib3.disable_warnings()

def get_token():
    url = 'https://127.0.0.1:55000/security/user/authenticate'
    r = requests.get(
        url,
        auth=HTTPBasicAuth('wazuh-wui', 'MyS3cr37P450r.*-'),
        verify=False,
        timeout=5
    )
    if r.status_code == 200:
        return r.json()['data']['token']
    return None

token = get_token()
if not token:
    print("Failed to get token")
    exit(1)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get critical alerts for win-001 using correct endpoint
print("=" * 60)
print("CRITICAL ALERTS FOR win-001")
print("=" * 60)

# Try Elasticsearch query endpoint
url = 'https://127.0.0.1:55000/agents/win-001/events'
r = requests.get(
    url,
    headers=headers,
    verify=False,
    params={'limit': 10}
)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    events = data.get('data', {}).get('affected_items', [])
    if events:
        print(f"Found {len(events)} events")
        for event in events[:5]:
            rule_level = event.get('rule', {}).get('level', 'N/A')
            rule_id = event.get('rule', {}).get('id', 'N/A')
            desc = event.get('rule', {}).get('description', 'N/A')
            agent = event.get('agent', {}).get('name', 'N/A')
            timestamp = event.get('timestamp', 'N/A')
            print(f"\nTimestamp: {timestamp}")
            print(f"  Rule: {rule_id} (Level: {rule_level})")
            print(f"  Description: {desc[:80]}")
    else:
        print("No events found")
else:
    print(f"Response: {r.text[:500]}")

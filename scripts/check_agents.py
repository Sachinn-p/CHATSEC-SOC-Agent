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

# Get all agents
print("=" * 60)
print("AGENTS IN WAZUH")
print("=" * 60)
r = requests.get('https://127.0.0.1:55000/agents', headers=headers, verify=False)
if r.status_code == 200:
    data = r.json()
    agents = data.get('data', {}).get('affected_items', [])
    if agents:
        for agent in agents[:10]:  # Show first 10
            print(f"ID: {agent.get('id')}, Name: {agent.get('name')}, Status: {agent.get('status')}")
    else:
        print("No agents found")
else:
    print(f"Error: {r.status_code} - {r.text}")

# Get alerts for win-001
print("\n" + "=" * 60)
print("CRITICAL ALERTS FOR win-001")
print("=" * 60)
r = requests.get(
    'https://127.0.0.1:55000/alerts',
    headers=headers,
    verify=False,
    params={'agent_id': 'win-001', 'rule.level': '7,8,9,10', 'limit': 10}
)
if r.status_code == 200:
    data = r.json()
    alerts = data.get('data', {}).get('affected_items', [])
    if alerts:
        for alert in alerts:
            print(f"Rule ID: {alert.get('rule', {}).get('id')}, Level: {alert.get('rule', {}).get('level')}, Description: {alert.get('rule', {}).get('description')}")
    else:
        print("No critical alerts found for win-001")
else:
    print(f"Error: {r.status_code}")
    print(r.text[:500])

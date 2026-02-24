#!/usr/bin/env python3
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()

url = 'https://127.0.0.1:55000/security/user/authenticate'
try:
    r = requests.get(
        url,
        auth=HTTPBasicAuth('wazuh-wui', 'MyS3cr37P450r.*-'),
        verify=False,
        timeout=5
    )
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        print('✓ Authentication: SUCCESS')
        data = r.json()
        token = data.get('data', {}).get('token', 'No token')
        print(f'Token obtained: {token[:20]}...' if len(str(token)) > 20 else f'Token: {token}')
    else:
        print(f'✗ Error: {r.status_code}')
        print(f'Response: {r.text}')
except Exception as e:
    print(f'✗ Exception: {e}')

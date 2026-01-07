from src.core.agent import init_agent

agent = init_agent()
print('[OK] Agent initialized with CURL tool')

result = agent.query_wazuh_api('/agents', {'status': 'active'})
if result['success']:
    agents = result['data']['data']['affected_items']
    print(f'[OK] CURL tool working - found {len(agents)} active agents')
    for ag in agents:
        print(f'  - {ag["name"]} (ID: {ag["id"]})')

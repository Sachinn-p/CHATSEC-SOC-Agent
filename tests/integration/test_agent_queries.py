#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')

from src.core.agent import init_agent
from config.settings import Config

# Initialize the agent like the app does
config = Config()
agent = init_agent()

print("=" * 70)
print("Testing agent's Wazuh queries")
print("=" * 70)

# Test 1: Health check
print("\n1. Health Check:")
health = agent.wazuh_client.health_check()
print(f"   Success: {health.get('success')}")
print(f"   Connected: {health.get('connected')}")
if not health.get('success'):
    print(f"   Error: {health.get('error')}")

# Test 2: Get all agents
print("\n2. Get All Agents:")
agents = agent.wazuh_client.get_agents()
if agents.get('success'):
    agent_list = agents.get('agents', [])
    print(f"   Found {len(agent_list)} agents")
    for a in agent_list:
        print(f"     - {a.get('name')} (ID: {a.get('id')}, Status: {a.get('status')})")
else:
    print(f"   Error: {agents.get('error')}")

# Test 3: Get critical alerts for win-001
print("\n3. Critical Alerts for win-001:")
critical = agent.wazuh_client.get_critical_alerts(hours=24, agent_name='win-001')
if critical.get('success'):
    total = critical.get('total_critical_alerts', 0)
    print(f"   Found {total} critical alerts")
else:
    print(f"   Error: {critical.get('error')}")

# Test 4: Get agent by name
print("\n4. Get Agent Info (win-001):")
agent_info = agent.wazuh_client.get_agent_by_name('win-001')
if agent_info.get('success'):
    print(f"   Agent found: {agent_info.get('agent', {}).get('name')}")
else:
    print(f"   Error: {agent_info.get('error')}")

print("\n" + "=" * 70)

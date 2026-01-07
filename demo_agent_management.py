"""
Test script for Agent Management functionality
Demonstrates adding, listing, and removing Wazuh agents
"""
from src.core.agent import SOCAgent
from config.settings import Config

print("="*70)
print(" WAZUH AGENT MANAGEMENT DEMO")
print("="*70)

# Initialize agent
config = Config()
agent = SOCAgent(config)
agent.initialize()

# Test 1: List current agents
print("\n[1] Listing Current Agents")
print("-" * 70)
result = agent.get_all_agents_info()

if result.get('success'):
    agents = result.get('agents', [])
    print(f"Total agents: {len(agents)}\n")
    
    for ag in agents:
        print(f"ID: {ag.get('id')} | Name: {ag.get('name')} | IP: {ag.get('ip')} | Status: {ag.get('status')}")
else:
    print(f"[ERROR] {result.get('error')}")

# Test 2: Add a new agent
print("\n[2] Adding New Agent")
print("-" * 70)
print("Agent Details:")
print("  Name: test-server-01")
print("  IP: any (dynamic)")
print("  Groups: testing, development")

result = agent.add_new_agent(
    name="test-server-01",
    ip="any",
    groups=["testing", "development"]
)

if result.get('success'):
    print(f"\n[SUCCESS] {result.get('message')}")
    
    agent_info = result.get('agent', {})
    print(f"\nAgent Details:")
    print(f"  Agent ID: {agent_info.get('id')}")
    print(f"  Name: {agent_info.get('name')}")
    print(f"  IP: {agent_info.get('ip')}")
    print(f"  Status: {agent_info.get('status', 'pending')}")
    
    agent_key = agent_info.get('key')
    if agent_key:
        print(f"\n[AGENT KEY]")
        print(f"{agent_key}")
        print(f"\nTo register this agent on the target system:")
        print(f"  sudo /var/ossec/bin/agent-auth -k {agent_key}")
else:
    print(f"\n[ERROR] {result.get('error')}")

# Test 3: List agents again to see the new one
print("\n[3] Updated Agent List")
print("-" * 70)
result = agent.get_all_agents_info()

if result.get('success'):
    agents = result.get('agents', [])
    print(f"Total agents: {len(agents)}\n")
    
    for ag in agents:
        print(f"ID: {ag.get('id')} | Name: {ag.get('name')} | IP: {ag.get('ip')} | Status: {ag.get('status')}")
else:
    print(f"[ERROR] {result.get('error')}")

# Test 4: Remove the test agent (optional - uncomment to test removal)
print("\n[4] Agent Removal (Demo)")
print("-" * 70)
print("To remove an agent, use:")
print("  result = agent.remove_agent(agent_id='002', purge=False)")
print("\nSkipping removal in demo to keep the test agent...")

# Uncomment below to actually remove the test agent
"""
if agent_info and agent_info.get('id'):
    test_agent_id = agent_info.get('id')
    print(f"\nRemoving test agent {test_agent_id}...")
    
    result = agent.remove_agent(agent_id=test_agent_id, purge=True)
    
    if result.get('success'):
        print(f"[SUCCESS] {result.get('message')}")
    else:
        print(f"[ERROR] {result.get('error')}")
"""

print("\n" + "="*70)
print(" DEMO COMPLETE")
print("="*70)
print("\nAvailable Methods:")
print("  1. agent.add_new_agent(name, ip, groups)")
print("  2. agent.get_all_agents_info()")
print("  3. agent.remove_agent(agent_id, purge)")
print("\nThese methods are also available in the Streamlit app!")
print("Go to: Agent Management tab")
print("="*70)

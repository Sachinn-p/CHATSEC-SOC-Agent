#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, 'c:\\Users\\Infy12\\Desktop\\Codes\\CHATSEC')

from src.core.agent import init_agent

async def test_agent():
    agent = init_agent()
    
    print("=" * 70)
    print("Testing agent.run() with prompt about win-001")
    print("=" * 70)
    
    prompt = "Any critical issues in win-001?"
    
    print(f"\nPrompt: {prompt}\n")
    print("Agent response:")
    print("-" * 70)
    
    response = await agent.run(prompt, [])
    print(response)
    
    print("-" * 70)

if __name__ == "__main__":
    asyncio.run(test_agent())

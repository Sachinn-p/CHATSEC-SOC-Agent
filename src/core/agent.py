"""
Agent management module for MCP + Groq integration.
"""
import asyncio
from typing import List, Dict, Any, Optional

from mcp_use import MCPAgent, MCPClient
from langchain_groq import ChatGroq

from config.settings import Config


class SOCAgent:
    """SOC Agent wrapper for MCP + Groq integration"""
    
    def __init__(self, config: Config):
        self.config = config
        self._agent: Optional[MCPAgent] = None
        self._client: Optional[MCPClient] = None
        self._llm: Optional[ChatGroq] = None
        
    def _validate_config(self) -> None:
        """Validate required configuration"""
        if not self.config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        if not self.config.GROQ_MODEL:
            raise ValueError("GROQ_MODEL is required")
        if not self.config.MCP_COMMAND:
            raise ValueError("MCP_COMMAND is required")
    
    def initialize(self) -> MCPAgent:
        """Initialize the MCP agent with Groq LLM"""
        self._validate_config()
        
        # Initialize MCP client
        mcp_config = self.config.get_mcp_config()
        self._client = MCPClient.from_dict(mcp_config)
        
        # Initialize Groq LLM
        self._llm = ChatGroq(
            model=self.config.GROQ_MODEL,
            api_key=self.config.GROQ_API_KEY
        )
        
        # Initialize MCP Agent with max_steps
        self._agent = MCPAgent(
            llm=self._llm, 
            client=self._client, 
            max_steps=self.config.MAX_AGENT_STEPS
        )
        
        return self._agent
    
    @property
    def agent(self) -> MCPAgent:
        """Get the initialized agent"""
        if self._agent is None:
            return self.initialize()
        return self._agent
    
    async def run(self, prompt: str, previous_messages: List[Dict[str, str]] = None, 
                  max_steps: Optional[int] = None) -> str:
        """
        Run the agent with a given prompt and context.
        
        Args:
            prompt: The user prompt
            previous_messages: List of previous messages for context
            max_steps: Override max_steps for this run
            
        Returns:
            Agent response string
        """
        previous_messages = previous_messages or []
        max_steps = max_steps or self.config.MAX_AGENT_STEPS
        
        # Build context from previous messages
        context_prompt = "\\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in previous_messages
        ])
        
        # Construct full prompt with context
        full_prompt = f"{context_prompt}\\nUser: {prompt}\\nAssistant:" if context_prompt else prompt
        
        # Run the agent
        try:
            result = await self.agent.run(full_prompt, max_steps=max_steps)
            return result
        except Exception as e:
            raise RuntimeError(f"Agent execution failed: {str(e)}")


# Global agent instance (for backward compatibility)
_global_agent_instance = None


def init_agent() -> MCPAgent:
    """Initialize global agent instance (legacy function)"""
    global _global_agent_instance
    config = Config()
    soc_agent = SOCAgent(config)
    _global_agent_instance = soc_agent.initialize()
    return _global_agent_instance


async def run_agent(agent: MCPAgent, prompt: str, previous_messages: List[Dict[str, str]] = None) -> str:
    """Run agent with prompt (legacy function)"""
    previous_messages = previous_messages or []
    config = Config()
    
    # Build context from previous messages
    context_prompt = "\\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in previous_messages
    ])
    
    # Construct full prompt
    full_prompt = f"{context_prompt}\\nUser: {prompt}\\nAssistant:" if context_prompt else prompt
    
    # Run with configured max_steps
    result = await agent.run(full_prompt, max_steps=config.MAX_AGENT_STEPS)
    return result
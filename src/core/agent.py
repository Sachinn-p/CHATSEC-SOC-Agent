"""
Agent management module using FastMCP + Groq integration.
"""
import os
import sys
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.settings import Config
from src.core.wazuh_client import get_wazuh_client


class SOCAgent:
    """SOC Agent wrapper for Groq + Wazuh integration"""
    
    def __init__(self, config: Config):
        self.config = config
        self.wazuh_client = None
        self.llm: Optional[ChatGroq] = None
        
    def _validate_config(self) -> None:
        """Validate required configuration"""
        if not self.config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        if not self.config.GROQ_MODEL:
            raise ValueError("GROQ_MODEL is required")
    
    def initialize(self):
        """Initialize the SOC agent with Groq LLM and Wazuh client"""
        self._validate_config()
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=self.config.GROQ_MODEL,
            api_key=self.config.GROQ_API_KEY,
            temperature=0.1
        )
        
        # Initialize Wazuh client
        self.wazuh_client = get_wazuh_client()
        
        return self
    
    def execute_curl(self, url: str, method: str = "GET", headers: Dict[str, str] = None, 
                    data: str = None, auth: tuple = None, verify_ssl: bool = False) -> Dict[str, Any]:
        """Execute a curl command and return the response
        
        Args:
            url: The URL to query
            method: HTTP method (GET, POST, etc.)
            headers: Dictionary of headers
            data: Request body data
            auth: Tuple of (username, password) for basic auth
            verify_ssl: Whether to verify SSL certificates
            
        Returns:
            Dictionary with 'success', 'data', 'status_code', and 'error' fields
        """
        try:
            import requests
            
            # Prepare request parameters
            request_kwargs = {
                'verify': verify_ssl,
                'timeout': 30
            }
            
            # Add authentication if provided
            if auth:
                request_kwargs['auth'] = auth
            
            # Add headers if provided
            if headers:
                request_kwargs['headers'] = headers
            
            # Add data if provided
            if data:
                request_kwargs['data'] = data
            
            # Make the request
            if method.upper() == "GET":
                response = requests.get(url, **request_kwargs)
            elif method.upper() == "POST":
                response = requests.post(url, **request_kwargs)
            elif method.upper() == "PUT":
                response = requests.put(url, **request_kwargs)
            elif method.upper() == "DELETE":
                response = requests.delete(url, **request_kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response_data,
                "error": None if response.status_code < 400 else f"HTTP {response.status_code}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "status_code": None,
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None,
                "data": None
            }
    
    def query_wazuh_api(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query Wazuh API using curl-like requests
        
        Args:
            endpoint: API endpoint (e.g., '/alerts', '/agents')
            params: Query parameters
            
        Returns:
            Dictionary with query results
        """
        # Build URL
        base_url = f"{self.config.WAZUH_TEST_PROTOCOL}://{self.config.WAZUH_API_HOST}:{self.config.WAZUH_API_PORT}"
        url = f"{base_url}{endpoint}"
        
        # Add query parameters
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query_string}"
        
        # Get authentication token
        if not self.wazuh_client.token:
            auth_result = self.wazuh_client.authenticate()
            if not auth_result:
                return {
                    "success": False,
                    "error": "Failed to authenticate with Wazuh API"
                }
        
        # Execute curl with token
        headers = {
            "Authorization": f"Bearer {self.wazuh_client.token}",
            "Content-Type": "application/json"
        }
        
        result = self.execute_curl(
            url=url,
            method="GET",
            headers=headers,
            verify_ssl=self.config.WAZUH_VERIFY_SSL.lower() == "true"
        )
        
        return result
    
    def get_critical_alerts_for_agent(self, agent_id: str = "001", agent_name: str = "win-001", 
                                     severity: int = 4, hours: int = 24) -> Dict[str, Any]:
        """Get critical alerts for a specific agent using direct API query
        
        Args:
            agent_id: Agent ID (e.g., '001')
            agent_name: Agent name (e.g., 'win-001')
            severity: Minimum severity level (4 = critical)
            hours: Time range in hours
            
        Returns:
            Dictionary with alert count and details
        
        Example:
            result = agent.get_critical_alerts_for_agent("001", "win-001", severity=4)
            print(f"Critical alerts: {result['total']}")
        """
        # Use the indexer-based method which is more reliable
        return self.wazuh_client.get_critical_alerts(hours=hours, agent_name=agent_name)
    
    def add_new_agent(self, name: str, ip: str = "any", groups: List[str] = None) -> Dict[str, Any]:
        """Register a new agent in Wazuh
        
        Args:
            name: Agent hostname (e.g., 'srv-web-01', 'win-workstation-05')
            ip: Agent IP address (use 'any' for dynamic IP, default: 'any')
            groups: List of groups to assign (e.g., ['webservers', 'production'])
            
        Returns:
            Dictionary containing:
            - success: bool
            - agent: dict with agent details (id, name, ip, key)
            - message: success/error message
            
        Example:
            result = agent.add_new_agent(
                name="srv-web-01",
                ip="192.168.1.100",
                groups=["webservers", "production"]
            )
            if result['success']:
                print(f"Agent ID: {result['agent']['id']}")
                print(f"Agent Key: {result['agent']['key']}")
        """
        if not self.wazuh_client:
            return {
                "success": False,
                "error": "Wazuh client not initialized"
            }
        
        return self.wazuh_client.add_agent(name, ip, groups)
    
    def remove_agent(self, agent_id: str, purge: bool = False) -> Dict[str, Any]:
        """Remove an agent from Wazuh
        
        Args:
            agent_id: Agent ID to remove (e.g., '001', '005')
            purge: If True, completely remove from database (default: False)
            
        Returns:
            Dictionary with removal status
        """
        if not self.wazuh_client:
            return {
                "success": False,
                "error": "Wazuh client not initialized"
            }
        
        return self.wazuh_client.delete_agent(agent_id, purge)
    
    def get_all_agents_info(self) -> Dict[str, Any]:
        """Get detailed information about all agents
        
        Returns:
            Dictionary with all agents and their details
        """
        if not self.wazuh_client:
            return {
                "success": False,
                "error": "Wazuh client not initialized"
            }
        
        return self.wazuh_client.get_agents()
    
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
        if not self.llm:
            self.initialize()
            
        previous_messages = previous_messages or []
        prompt_lower = prompt.lower()
        
        # Check if we should fetch Wazuh data
        should_fetch_data = any(phrase in prompt_lower for phrase in [
            "go ahead", "fetch", "get", "show me", "pull", "retrieve", "check",
            "how many", "what", "tell me", "list", "find", "search", "yes", "do it",
            "curl", "query", "api call", "direct"
        ])
        
        if self.wazuh_client and should_fetch_data:
            # Extract agent name if mentioned
            agent_name = None
            for word in prompt.split():
                if "win-" in word.lower() or "srv-" in word.lower() or "agent" in word.lower():
                    agent_name = word.strip('.,!?')
                    break
            
            # Determine which data to fetch
            tool_results = []
            
            # Always check health first
            health = self.wazuh_client.health_check()
            if not health.get("success"):
                return f"❌ Cannot connect to Wazuh: {health.get('error', 'Unknown error')}"
            
            tool_results.append(("Health Check", json.dumps(health, indent=2)))
            
            # Fetch based on query intent
            if any(word in prompt_lower for word in ["critical", "severity", "high", "issue"]):
                # Get critical alerts for specific agent or all
                critical = self.wazuh_client.get_critical_alerts(hours=24, agent_name=agent_name)
                tool_results.append(("Critical Alerts", json.dumps(critical, indent=2)))
                
                # Get summary
                summary = self.wazuh_client.get_alert_summary(hours=24, agent_name=agent_name)
                tool_results.append(("Alert Summary", json.dumps(summary, indent=2)))
            
            if any(word in prompt_lower for word in ["alert", "recent", "latest", "event"]):
                alerts = self.wazuh_client.get_alerts_from_indexer(hours=24, limit=50, agent_name=agent_name)
                tool_results.append(("Recent Alerts", json.dumps(alerts, indent=2)))
            
            if any(word in prompt_lower for word in ["agent", "host", "machine", "server"]):
                if agent_name:
                    agent_info = self.wazuh_client.get_agent_by_name(agent_name)
                    tool_results.append((f"Agent {agent_name}", json.dumps(agent_info, indent=2)))
                else:
                    agents = self.wazuh_client.get_agents()
                    tool_results.append(("All Agents", json.dumps(agents, indent=2)))
            
            if any(word in prompt_lower for word in ["vulnerab", "cve", "exploit", "patch"]):
                vulns = self.wazuh_client.get_vulnerabilities(agent_name=agent_name, limit=20)
                tool_results.append(("Vulnerabilities", json.dumps(vulns, indent=2)))
            
            if any(word in prompt_lower for word in ["auth", "login", "password", "failed"]):
                auth = self.wazuh_client.get_failed_auth(hours=24, agent_name=agent_name, limit=50)
                tool_results.append(("Failed Authentication", json.dumps(auth, indent=2)))
            
            # If no specific queries matched but data fetch was requested
            if len(tool_results) == 1:  # Only health check
                # Default to getting summary and agents
                summary = self.wazuh_client.get_alert_summary(hours=24, agent_name=agent_name)
                tool_results.append(("Alert Summary", json.dumps(summary, indent=2)))
                
                if agent_name:
                    agent_info = self.wazuh_client.get_agent_by_name(agent_name)
                    tool_results.append((f"Agent {agent_name}", json.dumps(agent_info, indent=2)))
            
            # Format tool results
            tools_output = "\n\n".join([f"### {name}\n```json\n{data}\n```" for name, data in tool_results])
            
            # Create analysis prompt
            analysis_prompt = f"""User question: "{prompt}"

Here is the data from Wazuh:

{tools_output}

Please analyze this data and answer the user's question. Be specific:
- If asking about a specific agent (like win-001), extract data only for that agent
- Count actual numbers from the JSON data
- If critical issues are mentioned, report the exact count from "total_critical" field
- Format your response clearly with numbers and details"""

            messages = [
                SystemMessage(content="You are a SOC analyst. Analyze Wazuh data and provide clear, accurate answers with specific numbers."),
                HumanMessage(content=analysis_prompt)
            ]
            
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                return f"❌ Error analyzing data: {str(e)}\n\nRaw data:\n{tools_output}"
        
        # No data fetch needed, just respond
        messages = [
            SystemMessage(content="""You are a Security Operations Center (SOC) analyst assistant with access to Wazuh security monitoring.

You have the following capabilities:
1. Query Wazuh API directly using curl-like requests
2. Fetch alerts, agents, vulnerabilities, and authentication logs
3. Filter data by agent name, severity, time range
4. Analyze and summarize security data

When users ask about security data, acknowledge and confirm you can fetch it. When they confirm (say "go ahead", "yes", etc.), I'll retrieve the actual data from Wazuh using the appropriate API calls.""")
        ]
        
        # Add context
        for msg in previous_messages[-5:]:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"❌ Error: {str(e)}"


# Global agent instance
_global_agent_instance = None


def init_agent():
    """Initialize global agent instance"""
    global _global_agent_instance
    config = Config()
    soc_agent = SOCAgent(config)
    _global_agent_instance = soc_agent.initialize()
    return _global_agent_instance


async def run_agent(agent: SOCAgent, prompt: str, previous_messages: List[Dict[str, str]] = None) -> str:
    """Run agent with prompt"""
    return await agent.run(prompt, previous_messages)
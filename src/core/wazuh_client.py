"""
Direct Wazuh API client for querying agents, alerts, and security data.
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from config.settings import Config

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WazuhAPIClient:
    """Client for direct Wazuh API access"""
    
    def __init__(self):
        self.api_host = Config.WAZUH_API_HOST
        self.api_port = Config.WAZUH_API_PORT
        self.username = Config.WAZUH_API_USERNAME
        self.password = Config.WAZUH_API_PASSWORD
        
        # Wazuh API uses HTTPS by default
        self.protocol = "https"
        self.verify_ssl = False  # Disable SSL verification for self-signed certs
        
        self.indexer_host = Config.WAZUH_INDEXER_HOST
        self.indexer_port = Config.WAZUH_INDEXER_PORT
        self.indexer_username = Config.WAZUH_INDEXER_USERNAME
        self.indexer_password = Config.WAZUH_INDEXER_PASSWORD
        
        self.base_url = f"{self.protocol}://{self.api_host}:{self.api_port}"
        self.indexer_url = f"https://{self.indexer_host}:{self.indexer_port}"  # Also use HTTPS
        self.token = None
        
    def authenticate(self) -> bool:
        """Authenticate with Wazuh API and get token"""
        try:
            url = f"{self.base_url}/security/user/authenticate"
            print(f"[AUTH] Attempting to authenticate to: {url}")
            print(f"       Username: {self.username}")
            print(f"       Verify SSL: {self.verify_ssl}")
            
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                verify=self.verify_ssl,
                timeout=10
            )
            
            print(f"       Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.token = response.json()["data"]["token"]
                print(f"       [OK] Authentication successful")
                return True
            else:
                print(f"       [FAIL] Authentication failed: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"       [ERROR] Connection error: Cannot reach {self.base_url}")
            print(f"              Error details: {str(e)}")
            return False
        except requests.exceptions.Timeout:
            print(f"       [ERROR] Timeout: Wazuh API did not respond in 10 seconds")
            return False
        except Exception as e:
            print(f"       [ERROR] Authentication error: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"              Traceback: {traceback.format_exc()}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        if not self.token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Content-Type": "application/json"
        }
    
    def get_agents(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Get all Wazuh agents with optional status filter"""
        try:
            url = f"{self.base_url}/agents"
            params = {}
            if status:
                params["status"] = status
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                agents = data.get("affected_items", [])
                return {
                    "success": True,
                    "total": len(agents),
                    "agents": agents
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Failed to fetch agents"}
    
    def get_agent_by_name(self, agent_name: str) -> Dict[str, Any]:
        """Get specific agent by name"""
        result = self.get_agents()
        if result.get("success"):
            for agent in result.get("agents", []):
                if agent.get("name", "").lower() == agent_name.lower():
                    return {"success": True, "agent": agent}
        return {"success": False, "error": f"Agent {agent_name} not found"}
    
    def get_alerts_from_indexer(self, hours: int = 24, limit: int = 100, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get alerts from Wazuh indexer (Elasticsearch)"""
        try:
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"range": {"timestamp": {"gte": start_time}}}
                        ]
                    }
                },
                "size": limit,
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            # Filter by agent name if provided
            if agent_name:
                query["query"]["bool"]["must"].append({
                    "match": {"agent.name": agent_name}
                })
            
            response = requests.post(
                f"{self.indexer_url}/wazuh-alerts-*/_search",
                json=query,
                auth=HTTPBasicAuth(self.indexer_username, self.indexer_password),
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                alerts = [hit["_source"] for hit in hits]
                return {
                    "success": True,
                    "total": len(alerts),
                    "alerts": alerts,
                    "timeframe": f"last {hours} hours"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Failed to fetch alerts"}
    
    def get_critical_alerts(self, hours: int = 24, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get critical alerts (severity >= 13)"""
        alerts_result = self.get_alerts_from_indexer(hours=hours, limit=500, agent_name=agent_name)
        
        if not alerts_result.get("success"):
            return alerts_result
        
        critical_alerts = [
            alert for alert in alerts_result.get("alerts", [])
            if alert.get("rule", {}).get("level", 0) >= 13
        ]
        
        return {
            "success": True,
            "total_critical": len(critical_alerts),
            "critical_alerts": critical_alerts[:50],  # Limit return size
            "agent": agent_name,
            "timeframe": f"last {hours} hours"
        }
    
    def get_alert_summary(self, hours: int = 24, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get alert summary grouped by severity"""
        alerts_result = self.get_alerts_from_indexer(hours=hours, limit=1000, agent_name=agent_name)
        
        if not alerts_result.get("success"):
            return alerts_result
        
        summary = {
            "critical": 0,  # level >= 13
            "high": 0,      # level 8-12
            "medium": 0,    # level 4-7
            "low": 0        # level < 4
        }
        
        for alert in alerts_result.get("alerts", []):
            level = alert.get("rule", {}).get("level", 0)
            if level >= 13:
                summary["critical"] += 1
            elif level >= 8:
                summary["high"] += 1
            elif level >= 4:
                summary["medium"] += 1
            else:
                summary["low"] += 1
        
        return {
            "success": True,
            "summary": summary,
            "total_alerts": sum(summary.values()),
            "agent": agent_name,
            "timeframe": f"last {hours} hours"
        }
    
    def get_vulnerabilities(self, agent_name: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Get vulnerabilities detected"""
        alerts_result = self.get_alerts_from_indexer(hours=168, limit=1000, agent_name=agent_name)  # Last week
        
        if not alerts_result.get("success"):
            return alerts_result
        
        # Filter for vulnerability-related alerts
        vuln_keywords = ["vulnerability", "cve", "exploit", "vulnerable"]
        vuln_alerts = []
        
        for alert in alerts_result.get("alerts", []):
            rule_desc = alert.get("rule", {}).get("description", "").lower()
            if any(keyword in rule_desc for keyword in vuln_keywords):
                vuln_alerts.append(alert)
        
        # Group by CVE or description
        vuln_map = {}
        for alert in vuln_alerts:
            cve = alert.get("data", {}).get("vulnerability", {}).get("cve")
            if not cve:
                cve = alert.get("rule", {}).get("description", "Unknown")
            
            if cve not in vuln_map:
                vuln_map[cve] = {
                    "count": 0,
                    "severity": alert.get("rule", {}).get("level", 0),
                    "agents": set()
                }
            
            vuln_map[cve]["count"] += 1
            agent = alert.get("agent", {}).get("name")
            if agent:
                vuln_map[cve]["agents"].add(agent)
        
        # Convert to list
        vulnerabilities = [
            {
                "cve": cve,
                "count": data["count"],
                "severity": data["severity"],
                "affected_agents": list(data["agents"])[:5]
            }
            for cve, data in sorted(vuln_map.items(), key=lambda x: x[1]["count"], reverse=True)
        ][:limit]
        
        return {
            "success": True,
            "vulnerabilities": vulnerabilities,
            "total": len(vulnerabilities),
            "agent": agent_name
        }
    
    def get_failed_auth(self, hours: int = 24, agent_name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get failed authentication attempts"""
        alerts_result = self.get_alerts_from_indexer(hours=hours, limit=1000, agent_name=agent_name)
        
        if not alerts_result.get("success"):
            return alerts_result
        
        # Filter for auth-related alerts
        auth_keywords = ["authentication", "login", "auth", "failed", "invalid password"]
        auth_alerts = [
            alert for alert in alerts_result.get("alerts", [])
            if any(keyword in json.dumps(alert).lower() for keyword in auth_keywords)
        ][:limit]
        
        return {
            "success": True,
            "failed_auth_attempts": auth_alerts,
            "total": len(auth_alerts),
            "agent": agent_name,
            "timeframe": f"last {hours} hours"
        }
    
    def add_agent(self, name: str, ip: str = "any", groups: List[str] = None) -> Dict[str, Any]:
        """Add a new agent to Wazuh
        
        Args:
            name: Agent name (hostname)
            ip: Agent IP address (default: 'any' for dynamic IP)
            groups: List of groups to assign the agent to
            
        Returns:
            Dictionary with agent registration details including agent_id and key
        """
        try:
            url = f"{self.base_url}/agents"
            
            payload = {
                "name": name
            }
            
            # Add IP if not default
            if ip and ip.lower() != "any":
                payload["ip"] = ip
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                agent_info = data.get("affected_items", [{}])[0]
                
                # Get the agent key for installation
                agent_id = agent_info.get("id")
                if agent_id:
                    key_result = self.get_agent_key(agent_id)
                    agent_info["key"] = key_result.get("key")
                    
                    # Assign groups if specified (after agent creation)
                    if groups:
                        group_result = self.assign_agent_groups(agent_id, groups)
                        if group_result.get("success"):
                            agent_info["groups"] = groups
                
                return {
                    "success": True,
                    "agent": agent_info,
                    "message": f"Agent '{name}' added successfully with ID: {agent_id}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add agent: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error adding agent: {str(e)}"
            }
    
    def get_agent_key(self, agent_id: str) -> Dict[str, Any]:
        """Get the authentication key for an agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dictionary with the agent key
        """
        try:
            url = f"{self.base_url}/agents/{agent_id}/key"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                key = data.get("affected_items", [{}])[0].get("key")
                return {
                    "success": True,
                    "key": key
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get agent key: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting agent key: {str(e)}"
            }
    
    def delete_agent(self, agent_id: str, purge: bool = False) -> Dict[str, Any]:
        """Delete an agent from Wazuh
        
        Args:
            agent_id: Agent ID to delete
            purge: If True, completely remove agent from database
            
        Returns:
            Dictionary with deletion status
        """
        try:
            url = f"{self.base_url}/agents"
            params = {
                "agents_list": agent_id,
                "purge": "true" if purge else "false"
            }
            
            response = requests.delete(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete agent: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting agent: {str(e)}"
            }
    
    def update_agent_group(self, agent_id: str, groups: List[str]) -> Dict[str, Any]:
        """Update agent group membership
        
        Args:
            agent_id: Agent ID
            groups: List of group names
            
        Returns:
            Dictionary with update status
        """
        return self.assign_agent_groups(agent_id, groups)
    
    def assign_agent_groups(self, agent_id: str, groups: List[str]) -> Dict[str, Any]:
        """Assign groups to an agent
        
        Args:
            agent_id: Agent ID
            groups: List of group names
            
        Returns:
            Dictionary with update status
        """
        try:
            # Assign each group individually using PUT method
            for group in groups:
                url = f"{self.base_url}/agents/{agent_id}/group/{group}"
                
                response = requests.put(
                    url,
                    headers=self._get_headers(),
                    verify=self.verify_ssl,
                    timeout=10
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to assign group {group}: {response.text}"
                    }
            
            return {
                "success": True,
                "message": f"Groups assigned to agent {agent_id}"
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error assigning groups: {str(e)}"
            }
            return {
                "success": False,
                "error": f"Error updating groups: {str(e)}"
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check Wazuh connection health"""
        try:
            # Test authentication
            auth_result = self.authenticate()
            if not auth_result:
                return {
                    "success": False,
                    "error": f"Authentication failed to {self.base_url}. Check username/password.",
                    "connected": False,
                    "wazuh_api": self.base_url,
                    "wazuh_indexer": self.indexer_url
                }
            
            # Test getting agents
            agents_result = self.get_agents()
            
            if agents_result.get("success"):
                agents = agents_result.get("agents", [])
                active_count = len([a for a in agents if a.get("status") == "active"])
                
                return {
                    "success": True,
                    "wazuh_api": self.base_url,
                    "wazuh_indexer": self.indexer_url,
                    "connected": True,
                    "authenticated": True,
                    "total_agents": len(agents),
                    "active_agents": active_count
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get agents: {agents_result.get('error', 'Unknown error')}",
                    "connected": True,
                    "authenticated": True,
                    "wazuh_api": self.base_url
                }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "traceback": traceback.format_exc(),
                "connected": False,
                "wazuh_api": self.base_url,
                "wazuh_indexer": self.indexer_url
            }
        
        return {"success": False, "error": "Unknown failure", "connected": False}


# Global client instance
_wazuh_client = None


def get_wazuh_client() -> WazuhAPIClient:
    """Get or create global Wazuh client"""
    global _wazuh_client
    if _wazuh_client is None:
        _wazuh_client = WazuhAPIClient()
    return _wazuh_client

#!/usr/bin/env python3
"""
Mock Wazuh MCP Server using FastMCP.
Provides MCP tools for Wazuh agent management and alert querying.
"""
import os
from fastmcp import FastMCP
import json
from datetime import datetime, timedelta
import requests
from typing import Optional

mcp = FastMCP("wazuh-server")

# Wazuh Configuration
WAZUH_API_HOST = os.getenv("WAZUH_API_HOST", "127.0.0.1")
WAZUH_API_PORT = os.getenv("WAZUH_API_PORT", "55000")
WAZUH_API_USERNAME = os.getenv("WAZUH_API_USERNAME", "admin")
WAZUH_API_PASSWORD = os.getenv("WAZUH_API_PASSWORD", "")
WAZUH_INDEXER_HOST = os.getenv("WAZUH_INDEXER_HOST", "127.0.0.1")
WAZUH_INDEXER_PORT = os.getenv("WAZUH_INDEXER_PORT", "9200")
WAZUH_VERIFY_SSL = os.getenv("WAZUH_VERIFY_SSL", "false").lower() == "true"
WAZUH_TEST_PROTOCOL = os.getenv("WAZUH_TEST_PROTOCOL", "http")

# Create Wazuh API URL
WAZUH_URL = f"{WAZUH_TEST_PROTOCOL}://{WAZUH_API_HOST}:{WAZUH_API_PORT}"


class WazuhClient:
    """Client for Wazuh API"""
    
    def __init__(self):
        self.base_url = WAZUH_URL
        self.username = WAZUH_API_USERNAME
        self.password = WAZUH_API_PASSWORD
        self.token = None
        self.verify_ssl = WAZUH_VERIFY_SSL
        
    def authenticate(self):
        """Authenticate with Wazuh API"""
        try:
            auth = (self.username, self.password)
            response = requests.get(
                f"{self.base_url}/security/user/authenticate",
                auth=auth,
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                self.token = response.json()["data"]["token"]
                return True
        except Exception as e:
            print(f"Authentication failed: {e}")
        return False
    
    def get_headers(self):
        """Get request headers with authentication"""
        if not self.token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Content-Type": "application/json"
        }
    
    def get_agents(self) -> list:
        """Get list of Wazuh agents"""
        try:
            response = requests.get(
                f"{self.base_url}/agents",
                headers=self.get_headers(),
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json().get("data", {})
                return data.get("affected_items", [])
        except Exception as e:
            print(f"Error fetching agents: {e}")
        return []
    
    def get_alerts(self, hours: int = 24) -> list:
        """Get recent alerts from Wazuh"""
        try:
            # Since we're using Elasticsearch directly
            indexer_url = f"http://{WAZUH_INDEXER_HOST}:{WAZUH_INDEXER_PORT}"
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": start_time
                        }
                    }
                },
                "size": 100,
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            response = requests.post(
                f"{indexer_url}/wazuh-alerts-*/_search",
                json=query,
                auth=(WAZUH_API_USERNAME, WAZUH_API_PASSWORD),
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                return [hit["_source"] for hit in hits]
        except Exception as e:
            print(f"Error fetching alerts: {e}")
        
        return []
    
    def get_agent_stats(self, agent_id: str) -> dict:
        """Get statistics for a specific agent"""
        try:
            response = requests.get(
                f"{self.base_url}/agents/{agent_id}/stats/hourly",
                headers=self.get_headers(),
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("data", {})
        except Exception as e:
            print(f"Error fetching agent stats: {e}")
        return {}


# Initialize Wazuh client
wazuh_client = WazuhClient()


@mcp.tool()
def get_agents(status: Optional[str] = None) -> str:
    """
    Get list of Wazuh agents with optional filtering by status.
    
    Args:
        status: Optional status filter (active, inactive, never_connected, pending)
    
    Returns:
        JSON string with list of agents
    """
    agents = wazuh_client.get_agents()
    
    if status and agents:
        agents = [a for a in agents if a.get("status") == status]
    
    return json.dumps({
        "success": True,
        "total": len(agents),
        "agents": agents[:10] if agents else []
    }, indent=2)


@mcp.tool()
def get_recent_alerts(hours: int = 24, limit: int = 10) -> str:
    """
    Get recent alerts from Wazuh.
    
    Args:
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of alerts to return (default: 10)
    
    Returns:
        JSON string with recent alerts
    """
    alerts = wazuh_client.get_alerts(hours)[:limit]
    
    return json.dumps({
        "success": True,
        "total": len(alerts),
        "alerts": alerts,
        "hours_lookback": hours
    }, indent=2)


@mcp.tool()
def get_alert_summary() -> str:
    """
    Get a summary of recent alerts grouped by severity.
    
    Returns:
        JSON string with alert summary
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for alert in alerts:
        severity = alert.get("rule", {}).get("level", 0)
        if severity >= 13:
            summary["critical"] += 1
        elif severity >= 8:
            summary["high"] += 1
        elif severity >= 4:
            summary["medium"] += 1
        else:
            summary["low"] += 1
    
    return json.dumps({
        "success": True,
        "summary": summary,
        "total_alerts": len(alerts),
        "timeframe": "last 24 hours"
    }, indent=2)


@mcp.tool()
def get_agent_stats(agent_id: str) -> str:
    """
    Get statistics for a specific Wazuh agent.
    
    Args:
        agent_id: The ID of the agent
    
    Returns:
        JSON string with agent statistics
    """
    stats = wazuh_client.get_agent_stats(agent_id)
    
    return json.dumps({
        "success": True,
        "agent_id": agent_id,
        "stats": stats
    }, indent=2)


@mcp.tool()
def query_logs(query: str, hours: int = 24) -> str:
    """
    Query Wazuh logs with a search term.
    
    Args:
        query: Search query string
        hours: Number of hours to search back
    
    Returns:
        JSON string with matching logs
    """
    alerts = wazuh_client.get_alerts(hours)
    
    # Simple text search
    matching = [
        a for a in alerts 
        if query.lower() in json.dumps(a).lower()
    ][:10]
    
    return json.dumps({
        "success": True,
        "query": query,
        "total_matches": len(matching),
        "results": matching,
        "hours_lookback": hours
    }, indent=2)


@mcp.tool()
def get_critical_agents() -> str:
    """
    Get agents with critical vulnerabilities or issues.
    
    Returns:
        JSON string with critical agents
    """
    agents = wazuh_client.get_agents()
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Find agents with critical alerts
    agent_alert_count = {}
    for alert in alerts:
        agent_id = alert.get("agent", {}).get("id")
        severity = alert.get("rule", {}).get("level", 0)
        if severity >= 13 and agent_id:
            agent_alert_count[agent_id] = agent_alert_count.get(agent_id, 0) + 1
    
    critical_agents = [a for a in agents if a.get("id") in agent_alert_count]
    
    return json.dumps({
        "success": True,
        "critical_agents": critical_agents,
        "total_critical": len(critical_agents),
        "critical_alerts_by_agent": agent_alert_count
    }, indent=2)


@mcp.tool()
def get_top_vulnerabilities(limit: int = 10) -> str:
    """
    Get top vulnerabilities detected by Wazuh.
    
    Args:
        limit: Maximum number of vulnerabilities to return
    
    Returns:
        JSON string with top vulnerabilities
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    vuln_map = {}
    for alert in alerts:
        rule_desc = alert.get("rule", {}).get("description", "Unknown")
        severity = alert.get("rule", {}).get("level", 0)
        
        if rule_desc not in vuln_map:
            vuln_map[rule_desc] = {"count": 0, "severity": severity, "agents": set()}
        
        vuln_map[rule_desc]["count"] += 1
        agent_id = alert.get("agent", {}).get("id")
        if agent_id:
            vuln_map[rule_desc]["agents"].add(agent_id)
    
    # Sort by count and convert to list
    sorted_vulns = sorted(vuln_map.items(), key=lambda x: x[1]["count"], reverse=True)
    top_vulns = [
        {
            "description": desc,
            "count": data["count"],
            "severity": data["severity"],
            "affected_agents": list(data["agents"])[:5]
        }
        for desc, data in sorted_vulns[:limit]
    ]
    
    return json.dumps({
        "success": True,
        "top_vulnerabilities": top_vulns,
        "total": len(top_vulns)
    }, indent=2)


@mcp.tool()
def get_failed_authentications(limit: int = 20) -> str:
    """
    Get recent failed authentication attempts detected by Wazuh.
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        JSON string with failed authentication attempts
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for auth-related alerts
    auth_alerts = [
        a for a in alerts 
        if "auth" in json.dumps(a).lower() or "authentication" in json.dumps(a).lower()
    ][:limit]
    
    return json.dumps({
        "success": True,
        "failed_auth_attempts": auth_alerts,
        "total": len(auth_alerts),
        "timeframe": "last 24 hours"
    }, indent=2)


@mcp.tool()
def get_malware_detections() -> str:
    """
    Get recent malware detections from Wazuh.
    
    Returns:
        JSON string with malware detections
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for malware-related alerts
    malware_alerts = [
        a for a in alerts 
        if "malware" in json.dumps(a).lower() or "trojan" in json.dumps(a).lower() or "virus" in json.dumps(a).lower()
    ]
    
    return json.dumps({
        "success": True,
        "malware_detections": malware_alerts[:20],
        "total_detections": len(malware_alerts)
    }, indent=2)


@mcp.tool()
def get_file_integrity_changes(limit: int = 15) -> str:
    """
    Get recent file integrity monitoring (FIM) changes detected by Wazuh.
    
    Args:
        limit: Maximum number of changes to return
    
    Returns:
        JSON string with FIM changes
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for FIM alerts
    fim_alerts = [
        a for a in alerts 
        if "fim" in json.dumps(a).lower() or "file integrity" in json.dumps(a).lower()
    ][:limit]
    
    return json.dumps({
        "success": True,
        "fim_changes": fim_alerts,
        "total_changes": len(fim_alerts)
    }, indent=2)


@mcp.tool()
def get_network_connections(limit: int = 20) -> str:
    """
    Get suspicious network connections detected by Wazuh.
    
    Args:
        limit: Maximum number of connections to return
    
    Returns:
        JSON string with network connections
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for network-related alerts
    network_alerts = [
        a for a in alerts 
        if any(x in json.dumps(a).lower() for x in ["network", "connection", "firewall", "port"])
    ][:limit]
    
    return json.dumps({
        "success": True,
        "network_connections": network_alerts,
        "total": len(network_alerts)
    }, indent=2)


@mcp.tool()
def get_system_audit_logs(limit: int = 25) -> str:
    """
    Get system audit logs from Wazuh.
    
    Args:
        limit: Maximum number of logs to return
    
    Returns:
        JSON string with audit logs
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for audit-related alerts
    audit_alerts = [
        a for a in alerts 
        if "audit" in json.dumps(a).lower() or "syscall" in json.dumps(a).lower()
    ][:limit]
    
    return json.dumps({
        "success": True,
        "audit_logs": audit_alerts,
        "total": len(audit_alerts)
    }, indent=2)


@mcp.tool()
def get_compliance_status() -> str:
    """
    Get compliance status and policy violations from Wazuh.
    
    Returns:
        JSON string with compliance information
    """
    alerts = wazuh_client.get_alerts(hours=24)
    
    # Filter for compliance-related alerts
    compliance_alerts = [
        a for a in alerts 
        if any(x in json.dumps(a).lower() for x in ["compliance", "policy", "cis", "pci"])
    ]
    
    return json.dumps({
        "success": True,
        "compliance_violations": compliance_alerts[:15],
        "total_violations": len(compliance_alerts)
    }, indent=2)


@mcp.tool()
def health_check() -> str:
    """
    Check the health of Wazuh connection.
    
    Returns:
        JSON string with health status
    """
    agents = wazuh_client.get_agents()
    active_agents = [a for a in agents if a.get("status") == "active"] if agents else []
    
    return json.dumps({
        "success": len(agents) > 0,
        "wazuh_api": f"{WAZUH_URL}",
        "total_agents": len(agents),
        "active_agents": len(active_agents),
        "connected": len(agents) > 0
    }, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport="stdio")

#!/usr/bin/env python3
"""
Wrapper script for Wazuh MCP Server.
This allows the server to be called from anywhere.
"""
import sys
import os
import subprocess

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server = os.path.join(script_dir, "src", "mcp", "wazuh_mcp_server.py")

if __name__ == "__main__":
    # Run the actual MCP server
    result = subprocess.run([sys.executable, mcp_server])
    sys.exit(result.returncode)

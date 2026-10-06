import os
import json
import requests
from typing import Any, Dict, List, Optional

class MCPClient:
    """Client for communicating with the DEPLOYTOUR Model Context Protocol (MCP) server."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")).rstrip("/")
        self.rpc_url = f"{self.base_url}/mcp"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools via MCP JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        resp = requests.post(self.rpc_url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a tool via MCP JSON-RPC 2.0 protocol."""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        resp = requests.post(self.rpc_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"MCP tool call error: {data['error']}")
        
        content = data.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])
        return data.get("result", {})

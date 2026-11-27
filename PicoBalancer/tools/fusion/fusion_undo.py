"""Undo the most recent Fusion operation through the MCP server's fusion_mcp_update tool."""
import json
from fusion_mcp import post
sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "picobalancer", "version": "1"}}})
post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
_, out = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "fusion_mcp_update", "arguments": {"featureType": "undo"}}}, sid)
print(out[:400])

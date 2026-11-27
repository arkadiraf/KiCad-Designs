#!/usr/bin/env python3
"""Minimal client for the local Fusion 360 MCP server (default http://127.0.0.1:60594/mcp; override with FUSION_MCP_URL).

    python fusion_mcp.py <script.py> [--write]

Runs a Fusion API Python script (must define run(context) and call it). Scripts are sent with
readOnly=True unless --write is given; Fusion enforces read-only. Write access to the model was
granted by the user on 2026-11-27 for the placement-review component only.
"""
import json
import os
import sys
import urllib.request

URL = os.environ.get("FUSION_MCP_URL", "http://127.0.0.1:60594/mcp")   # the port changes when Fusion restarts


def post(body, sid=None):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
         "MCP-Protocol-Version": "2025-06-18"}
    if sid:
        h["MCP-Session-Id"] = sid
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), h), timeout=300)
    return r.headers.get("MCP-Session-Id"), r.read().decode()


def run_script(script, write=False):
    sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "picobalancer", "version": "1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    _, out = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "fusion_mcp_execute",
        "arguments": {"featureType": "script", "object": {"script": script, "readOnly": not write}}}}, sid)
    return json.loads(out)


if __name__ == "__main__":
    d = run_script(open(sys.argv[1], encoding="utf8").read(), "--write" in sys.argv)
    for c in d.get("result", {}).get("content", []):
        t = c.get("text", "")
        try:
            j = json.loads(t)
            print(j.get("message") or j.get("error") or t)
        except Exception:
            print(t)
    if "error" in d:
        print(d["error"])

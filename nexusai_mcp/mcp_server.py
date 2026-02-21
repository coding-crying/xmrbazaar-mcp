#!/usr/bin/env python3
"""
Simple MCP Server Wrapper
Exposes the NexusAI tools via the Model Context Protocol
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import our tools
from nexusai_mcp.server import (
    search_market,
    get_item_details,
    get_vendor_rating,
    handle_tool_call
)

# ============================================================================
# MCP Manifest
# ============================================================================

MCP_MANIFEST = {
    "name": "nexusai",
    "version": "0.1.0",
    "description": "Multi-tool marketplace research assistant",
    "tools": [
        {
            "name": "search_market",
            "description": "Search marketplace listings for products",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"},
                    "marketplace": {"type": "string", "description": "Target marketplace"},
                    "max_results": {"type": "number", "description": "Max results"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_item_details", 
            "description": "Get full product details from a listing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Product page URL"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "get_vendor_rating",
            "description": "Check seller reputation and trust score",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vendor_url": {"type": "string", "description": "Vendor profile URL"}
                },
                "required": ["vendor_url"]
            }
        }
    ]
}


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="NexusAI MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "NexusAI MCP Server",
        "version": "0.1.0",
        "tools": [t["name"] for t in MCP_MANIFEST["tools"]]
    }


@app.get("/tools")
async def list_tools():
    return MCP_MANIFEST


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict = {}):
    """Call a specific tool with arguments."""
    try:
        result = await handle_tool_call(tool_name, arguments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/completions")
async def chat_completions(request: dict):
    """
    OpenAI-compatible chat completions endpoint.
    The LLM uses tools automatically via the MCP protocol.
    """
    messages = request.get("messages", [])
    tools = request.get("tools", None)
    
    # This is a simplified implementation
    # In production, you'd integrate with actual LLM reasoning
    # to chain tools automatically
    
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Use /tools endpoint to call NexusAI research tools"
            }
        }]
    }


# ============================================================================
# Direct CLI (for testing)
# ============================================================================

async def cli():
    """Run tool directly from command line."""
    if len(sys.argv) < 3:
        print("Usage: python mcp_server.py <tool_name> <args_json>")
        print(f"Available tools: {[t['name'] for t in MCP_MANIFEST['tools']]}")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    result = await handle_tool_call(tool_name, args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(cli())
    else:
        uvicorn.run(app, host="0.0.0.0", port=8765)

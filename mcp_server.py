#!/usr/bin/env python3
"""
NexusAI MCP Server - Model Context Protocol Server
==================================================
Exposes marketplace research tools to any MCP-compatible LLM.

Tools:
1. search_market  - Find listings matching user interest
2. get_item_details - Deep dive into specific listings  
3. get_vendor_rating - Verify seller trustworthiness
4. analyze_match - Score listing against user requirements
"""

import asyncio
import json
import re
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Import our tools
import sys
sys.path.insert(0, str(Path(__file__).parent))

from nexusai_mcp.server import (
    search_market,
    get_item_details, 
    get_vendor_rating,
    analyze_match,
    config
)


# ============================================================================
# MCP Server Setup
# ============================================================================

app = Server("nexusai-marketplace")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Define available tools with detailed descriptions for LLM guidance."""
    
    return [
        Tool(
            name="search_market",
            description="""Search marketplace for product listings.

**WHEN TO USE:**
- User asks about products in a category ("any ThinkPads for sale?")
- Initial research to discover what's available
- User provides general interest area

**HOW TO USE:**
1. Use broad search terms matching user's interest
2. Review returned titles and prices
3. Identify candidates worth investigating further
4. Call get_item_details on promising listings

**EXAMPLE:**
User: "I need a laptop for coding"
→ Call: search_market(query="laptop", max_results=10)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword (e.g., 'thinkpad', 'laptop', 'graphics card')"},
                    "marketplace": {"type": "string", "description": "Marketplace to search", "default": "xmrbazaar.com"},
                    "max_results": {"type": "integer", "description": "Max listings to return", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_item_details",
            description="""Get detailed information about a specific listing.

**WHEN TO USE:**
- After search_market returns candidates
- User asks about specific listing details
- Need to verify specs, condition, shipping
- User expresses interest in an item

**HOW TO USE:**
1. Pass the URL from search_market results
2. Review description, condition, seller info
3. Check vendor rating if available
4. Use analyze_match to score against user needs

**EXAMPLE:**
search_market returned: ThinkPad X1 Carbon for $200
→ Call: get_item_details(url="https://xmrbazaar.com/listing/...")
→ Review: condition, specs, shipping, seller""",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL of the listing page"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_vendor_rating",
            description="""Verify seller reputation and trustworthiness.

**WHEN TO USE:**
- Before recommending any listing to user
- User asks "is this seller trustworthy?"
- Large purchase or first-time transaction
- Any time you want to verify credibility

**HOW TO USE:**
1. Get vendor_url from get_item_details response
2. Check rating (4+ stars = good)
3. Verify trade count (more = more experienced)
4. Review trust level indicators

**EXAMPLE:**
get_item_details returned: seller "techdeals" with vendor_url
→ Call: get_vendor_rating(vendor_url="https://xmrbazaar.com/user/techdeals")
→ Review: rating 4.8, 150 trades, member since 2023""",
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_url": {"type": "string", "description": "URL of seller's profile page"}
                },
                "required": ["vendor_url"]
            }
        ),
        Tool(
            name="analyze_match",
            description="""Analyze how well a listing matches user requirements.

**WHEN TO USE:**
- After getting item details
- Before presenting results to user
- User has specific needs (budget, condition, features)
- Multiple candidates and need to rank/filter

**HOW TO USE:**
1. Get item details from get_item_details
2. Ask user for their requirements (budget, condition, features)
3. Pass both to analyze_match
4. Present ranked results with match reasoning

**EXAMPLE:**
User: "Need laptop under $500, good condition"
→ get_item_details → {title: "ThinkPad X1", price: "$450", condition: "Good"}
→ Call: analyze_match(item_details={...}, user_requirements={budget_max: 500, condition: "good"})
→ Result: Score 85/100 - "Highly recommended" """,
            inputSchema={
                "type": "object",
                "properties": {
                    "item_details": {"type": "object", "description": "Output from get_item_details"},
                    "user_requirements": {"type": "object", "description": "User needs: budget_max, category, condition, features"}
                },
                "required": ["item_details", "user_requirements"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to appropriate handlers."""
    
    try:
        if name == "search_market":
            result = await search_market(
                query=arguments.get("query", ""),
                marketplace=arguments.get("marketplace", "xmrbazaar.com"),
                max_results=arguments.get("max_results", 10)
            )
            
        elif name == "get_item_details":
            result = await get_item_details(
                url=arguments.get("url", "")
            )
            
        elif name == "get_vendor_rating":
            result = await get_vendor_rating(
                vendor_url=arguments.get("vendor_url", "")
            )
            
        elif name == "analyze_match":
            result = analyze_match(
                item_details=arguments.get("item_details", {}),
                user_requirements=arguments.get("user_requirements", {})
            )
            
        else:
            result = {"error": f"Unknown tool: {name}"}
            
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

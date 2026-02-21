# NexusAI + Claude Code Integration

This directory contains the multi-tool MCP server for NexusAI marketplace research.

## Quick Start

```bash
# 1. Install dependencies
cd /home/will/Desktop/NexusAI/mcp-server
pip install -r requirements.txt
playwright install chromium

# 2. Start the server
python -m nexusai_mcp.mcp_server

# 3. Configure Claude Code (or OpenCode)
# Add to your claude settings:
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LLM (Claude/GPT)                        │
│  "Find me a Thinkpad under 4 XMR from a trusted seller"  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Protocol Layer                       │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │search_market │  │get_item_details │  │get_vendor_   │ │
│  │              │──▶│                 │──▶│   rating     │ │
│  └──────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Playwright Browser Automation                   │
│   - Headless Chrome scraping                               │
│   - Dynamic content handling                                │
└─────────────────────────────────────────────────────────────┘
```

## Example: Finding a Thinkpad

```python
# The LLM automatically chains these tools:

# Step 1: Search
search_market(query="thinkpad", max_results=15)
# Returns: [{"title": "Thinkpad T480", "price": "3.5 XMR", "url": "..."}]

# Step 2: Deep dive  
get_item_details(url="https://xmr.bazaar/listing/123")
# Returns: {specs: {RAM: "16GB", SSD: "512GB"}, condition: "Excellent"}

# Step 3: Vendor check
get_vendor_rating(vendor_url="https://xmr.bazaar/user/john")
# Returns: {rating: "4.8", trades: 523, trust_level: "HIGH"}

# Step 4: LLM responds with recommendation
```

## Files

```
mcp-server/
├── README.md              # This file
├── package.json          # Node-style metadata
├── requirements.txt       # Python dependencies
└── nexusai_mcp/
    ├── __init__.py       # Package init
    ├── server.py         # Core tools (search, details, vendor)
    └── mcp_server.py     # FastAPI MCP wrapper
```

## Extending

Add more marketplaces by extending `server.py`:
- eBay (clearnet)
- Agora (darknet example)
- Cryptomarkets (various coins)

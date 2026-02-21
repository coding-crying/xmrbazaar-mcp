# XMRBazaar MCP Server

Connects your LLM to XMRBazaar marketplace so you can search listings, check product details, verify sellers, and get AI-powered recommendations.

## What is this?

An MCP (Model Context Protocol) server that gives your LLM tools to shop on XMRBazaar:

- **search_market** — Find products
- **get_item_details** — Full product info
- **get_vendor_rating** — Check seller trust
- **analyze_match** — Score against your needs

## Quick Start

### Docker

```bash
docker run -p 8765:8765 whywillwizardry/xmrbazaar-mcp
```

### Python

```bash
pip install -r requirements.txt
python mcp_server.py
```

## Connect to Your LLM

### Claude Desktop

```json
{
  "mcpServers": {
    "xmrbazaar": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "whywillwizardry/xmrbazaar-mcp"]
    }
  }
}
```

### Gemini CLI

```bash
gemini mcp add xmrbazaar "docker run --rm -i whywillwizardry/xmrbazaar-mcp"
```

### OpenWebUI

Add as "OAI Tools" at `http://localhost:8765/v1`

### LM Studio

Connect to `http://localhost:8765`

## Works With Any MCP LLM

- **Local:** Ollama, LM Studio, LocalAI
- **Cloud:** Claude, Gemini, GPT-4

## Example

```
You: Find me a ThinkPad under $100

LLM → search_market("thinkpad")
LLM → get_item_details(url)
LLM → analyze_match({price: $80}, {budget: 100})
LLM: Found one! ThinkPad X1 Carbon, $80, good condition
```

## Image

```
whywillwizardry/xmrbazaar-mcp:latest
```

https://hub.docker.com/r/whywillwizardry/xmrbazaar-mcp

# XMRBazaar MCP Server

An MCP (Model Context Protocol) server that gives LLMs tools to research products on XMRBazaar marketplace.

## Features

- **search_market** — Find listings matching user interests
- **get_item_details** — Deep dive into specific listings
- **get_vendor_rating** — Verify seller trustworthiness
- **analyze_match** — Score listings against user requirements

## Quick Start

### Docker (Recommended)

```bash
# Pull and run
docker run -p 8765:8765 whywillwizardry/xmrbazaar-mcp

# Or build locally
docker build -t xmrbazaar-mcp .
docker run -p 8765:8765 xmrbazaar-mcp
```

### Python Directly

```bash
pip install -r requirements.txt
python mcp_server.py
```

## Docker Image

```
whywillwizardry/xmrbazaar-mcp:latest
```

Published on Docker Hub: https://hub.docker.com/r/whywillwizardry/xmrbazaar-mcp

## Connecting to LLMs

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "xmrbazaar": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "xmrbazaar/xmrbazaar-mcp"]
    }
  }
}
```

### OpenWebUI

1. Go to **Settings → Admin Panel → OpenAI/API**
2. Add new "OAI Tools" connection:
   - URL: `http://localhost:8765/v1`
   - API Key: any (not required for local)

### Gemini CLI

```bash
gemini mcp add xmrbazaar "docker run --rm -i xmrbazaar/xmrbazaar-mcp"
```

### LM Studio, Codex CLI, and others

Start the HTTP server:
```bash
docker run -p 8765:8765 xmrbazaar/xmrbazaar-mcp
```

Then connect using the HTTP endpoint: `http://localhost:8765`

## Compatible with Local Models

This MCP server works with **any LLM that supports MCP**, including:

### Local Models (Ollama, LM Studio, etc.)

- **Ollama** — Run locally with Ollama, connect via OpenWebUI
- **LM Studio** — Add MCP server URL directly
- **LocalAI** — Connect via OpenAI-compatible API

### Cloud Models

- **Claude** (Anthropic)
- **Gemini** (Google)
- **GPT-4** (OpenAI)

The MCP protocol is model-agnostic — the LLM just needs MCP client support.

## Usage Example

```
User: "Find me ThinkPads under $100 on XMRBazaar"

LLM → search_market("thinkpad")
LLM → get_item_details(url)  
LLM → analyze_match({price: $80}, {budget: 100})
LLM → "Found one! ThinkPad X1 Carbon, $80, matches your budget"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MCP_MODE | stdio | `stdio` (Claude Desktop) or `http` (remote) |
| HEADLESS | true | Run browser headless |
| CACHE_TTL | 3600 | Cache duration in seconds |

## Architecture

```
User → LLM → MCP Server → XMRBazaar (scraped)
         ↓
    Tools:
    • search_market      → Playwright scraper
    • get_item_details   → Playwright scraper  
    • get_vendor_rating → Playwright scraper
    • analyze_match      → Local scoring
```

## For Developers

```bash
# Build
docker build -t xmrbazaar-mcp .

# Push to Docker Hub
docker push xmrbazaar/xmrbazaar-mcp:latest

# Run with custom config
docker run -e CACHE_TTL=7200 -p 8765:8765 xmrbazaar-mcp
```

## License

MIT

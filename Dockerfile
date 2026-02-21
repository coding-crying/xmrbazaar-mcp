# NexusAI MCP Server
# A marketplace research assistant for LLMs

FROM python:3.11-slim

WORKDIR /app

# Install Playwright + Chromium
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY nexusai_mcp/ ./nexusai_mcp/
COPY mcp_server.py .

# Run MCP server (stdio mode for local, can expose HTTP for remote)
CMD ["python", "-u", "mcp_server.py"]

# Expose HTTP port (optional, for remote connections)
EXPOSE 8765

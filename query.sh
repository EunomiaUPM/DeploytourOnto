#!/usr/bin/env bash
set -euo pipefail

# Check if MCP server is running
if ! docker compose ps mcp-server 2>/dev/null | grep -q "Up\|healthy"; then
  echo "[!] Infrastructure is not running. Starting infrastructure first..."
  ./start_infra.sh
fi

TTY_FLAG=""
if [ -t 0 ]; then
  TTY_FLAG="-it"
fi

if [ $# -gt 0 ]; then
  # Single query mode
  docker compose run --rm ${TTY_FLAG} gemma-agent python3 -m gemma_agent.cli "$@"
else
  # Interactive mode
  docker compose run --rm ${TTY_FLAG} gemma-agent python3 -m gemma_agent.cli
fi

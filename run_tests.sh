#!/usr/bin/env bash
set -euo pipefail

# Check if MCP server is running
if ! docker compose ps mcp-server 2>/dev/null | grep -q "Up\|healthy"; then
  echo "[!] Infrastructure is not running. Starting infrastructure first..."
  ./start_infra.sh
fi

echo "================================================================================"
echo "  DEPLOYTOUR: Running Integration & Gemma Agent Test Suite"
echo "================================================================================"

docker compose run --rm verifier

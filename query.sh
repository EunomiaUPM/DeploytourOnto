#!/usr/bin/env bash

# Copyright 2024-2026 Universidad Politécnica de Madrid / Deploytour
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

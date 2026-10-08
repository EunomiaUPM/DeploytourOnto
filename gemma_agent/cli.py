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

import sys
from .agent import GemmaAgent
from .mcp_client import MCPClient

BANNER = """
================================================================================
   DEPLOYTOUR — Google Gemma LLM Agent (Cross-Ontology MCP Interface)
================================================================================
 Connected to: Model Context Protocol (MCP) server with Apache Ossie & DuckDB
 Ontology A  : FIWARE Smart Data Models (Accommodations, Bed Capacity)
 Ontology B  : SEGITTUR / Schema.org (Destinations, Footfall, Spend)
================================================================================
Type your natural language questions, or type 'exit', 'quit', or 'q' to end.

Sample Queries:
  1. "Which municipality has the highest tourism pressure index?"
  2. "Compare Girona and Barcelona accommodation bed capacity."
  3. "What datasets and metrics are registered in Apache Ossie?"
  4. "How do FIWARE categories map to SEGITTUR spaces?"
  5. "What is the tourism pressure in Madrid?"
  6. "Find municipalities where monthly visitors exceed capacity by more than 50x."
--------------------------------------------------------------------------------
"""

def handle_query(agent: GemmaAgent, query: str):
    print(f"\n[USER QUERY]: {query}")
    print("-" * 70)
    result = agent.execute(query)

    print(f"\n[GEMMA PROMPT (Gemma-2 Template)]:\n{result['gemma_prompt']}")
    print(f"\n[GEMMA THOUGHT PROCESS]:\n{result['thought']}")
    tool_call = result.get("tool_call")
    if tool_call:
        print(f"\n[MCP TOOL INVOCATION]:\n`{tool_call['name']}` with arguments: {tool_call.get('arguments', {})}")
    print(f"\n[GEMMA RESPONSE]:\n{result['response']}\n")
    print("=" * 70)

def main():
    agent = GemmaAgent(mcp_client=MCPClient())

    # Mode 1: One-shot query provided via CLI arguments
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        handle_query(agent, query)
        return

    # Mode 2: Interactive REPL loop
    print(BANNER)
    while True:
        try:
            user_input = input("DEPLOYTOUR (Gemma Agent) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! Exiting Gemma Agent session.")
                break
            handle_query(agent, user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()

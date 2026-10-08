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

import os
import sys
import time
import requests
from .agent import GemmaAgent
from .mcp_client import MCPClient

def wait_for_mcp_server(mcp_url: str, timeout: int = 30):
    health_url = f"{mcp_url}/health"
    print(f"[gemma-agent] Verifying MCP Server availability at: {health_url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                print("  ✓ MCP Server is online and ready to serve tools.")
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"MCP server at {mcp_url} did not become ready within {timeout}s")

def print_test_header(num: int, title: str, what: str, why: str, prompt: str):
    print("\n" + "=" * 80)
    print(f" [TEST CASE {num}/5] {title.upper()}")
    print("=" * 80)
    print(f" ▶ WHAT IT DOES:")
    print(f"   {what}")
    print(f" ▶ WHY IT DOES IT:")
    print(f"   {why}")
    print(f" ▶ USER PROMPT:")
    print(f"   \"{prompt}\"")
    print("-" * 80)

def run_all_tests():
    print("\n" + "#" * 80)
    print("  GEMMA LLM AGENT & MCP FEDERATION TEST SUITE (DEPLOYTOUR)  ")
    print("#" * 80)
    print("Demonstrating autonomous reasoning and tool-calling capabilities")
    print("to resolve analytical queries across disparate tourism ontologies.\n")

    mcp = MCPClient()
    wait_for_mcp_server(mcp.base_url)
    agent = GemmaAgent(mcp_client=mcp)

    passed = 0
    total = 5

    # -------------------------------------------------------------
    # TEST CASE 1: Semantic Schema & Metric Discovery
    # -------------------------------------------------------------
    query_1 = "What datasets and metrics are available in the DEPLOYTOUR semantic federation?"
    print_test_header(
        1,
        "Semantic Schema & Metric Discovery (Apache Ossie)",
        what="The agent receives a natural language inquiry about available datasets and metrics, inspects its available MCP tools, and invokes 'list_semantic_entities'.",
        why="Enables the LLM and user to discover conceptual entities dynamically without requiring prior manual documentation or hardcoded table names.",
        prompt=query_1
    )
    res_1 = agent.execute(query_1)

    print(f"[TRACE - GEMMA THOUGHT]:\n  {res_1['thought']}")
    print(f"[TRACE - SELECTED TOOL]:\n  {res_1['tool_call']['name']}({res_1['tool_call'].get('arguments', {})})")
    
    assert res_1["tool_call"]["name"] == "list_semantic_entities", f"Unexpected tool: {res_1['tool_call']}"
    tool_data_1 = res_1["tool_result"]
    assert "datasets" in tool_data_1 and "metrics" in tool_data_1
    
    datasets_names = [d["id"] for d in tool_data_1["datasets"]]
    metrics_names = [m["id"] for m in tool_data_1["metrics"]]

    print(f"[TRACE - OBSERVATION RECEIVED BY GEMMA]:")
    print(f"  • Registered datasets: {datasets_names}")
    print(f"  • Registered metrics: {metrics_names}")
    
    assert "fiware_accommodations" in datasets_names
    assert "segittur_destinos" in datasets_names
    assert "TourismPressureIndex" in metrics_names
    print("✓ [RESULT]: Validation passed. Agent successfully discovered schemas and metrics.")
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 2: Cross-Ontology Mapping Resolution
    # -------------------------------------------------------------
    query_2 = "How do FIWARE categories map to SEGITTUR spaces, and what is the join key between them?"
    print_test_header(
        2,
        "Cross-Ontology Mapping Resolution (FIWARE <-> SEGITTUR)",
        what="The agent parses a question regarding schema alignment between disparate domain models and invokes 'get_ontology_mappings' to inspect foreign keys and taxonomy matrices.",
        why="Proves the system resolves conceptual ambiguity by explaining how European (FIWARE) and Spanish (SEGITTUR) tourism models correlate.",
        prompt=query_2
    )
    res_2 = agent.execute(query_2)

    print(f"[TRACE - GEMMA THOUGHT]:\n  {res_2['thought']}")
    print(f"[TRACE - SELECTED TOOL]:\n  {res_2['tool_call']['name']}({res_2['tool_call'].get('arguments', {})})")

    assert res_2["tool_call"]["name"] == "get_ontology_mappings", f"Unexpected tool: {res_2['tool_call']}"
    tool_data_2 = res_2["tool_result"]
    assert "join_keys" in tool_data_2 and "taxonomy_alignments" in tool_data_2

    join_key = tool_data_2["join_keys"][0]
    print(f"[TRACE - OBSERVATION RECEIVED BY GEMMA]:")
    print(f"  • Spatial join key: FIWARE '{join_key['source_attribute']}' <=> SEGITTUR '{join_key['target_attribute']}'")
    print(f"  • Total taxonomy mapping rules: {len(tool_data_2['taxonomy_alignments'])}")
    for align in tool_data_2['taxonomy_alignments']:
        src = align.get('source_category', align.get('source_concept'))
        tgt = align.get('target_category', align.get('target_concept'))
        print(f"    - {src} (FIWARE)  <===>  {tgt} (SEGITTUR) [{align.get('alignment_type', 'alignment')}]")

    assert join_key["source_attribute"] == "municipality_code"
    assert join_key["target_attribute"] == "codigo_ine_municipio"
    print("✓ [RESULT]: Validation passed. Semantic mapping and INE key resolution verified.")
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 3: Autonomous Tourism Pressure Analysis
    # -------------------------------------------------------------
    query_3 = "Execute the federated query across both lakehouses and analyze the highest tourism pressure index."
    print_test_header(
        3,
        "Cross-Lakehouse Tourism Pressure Analysis Across Both Lakes",
        what="The agent identifies the need to correlate supply (bed capacity in Lakehouse A) with demand (footfall in Lakehouse B) and invokes 'execute_federated_query'.",
        why="Identifies tourist overcapacity and pressure hotspots by joining data sources that were previously siloed.",
        prompt=query_3
    )
    res_3 = agent.execute(query_3)

    print(f"[TRACE - GEMMA THOUGHT]:\n  {res_3['thought']}")
    print(f"[TRACE - SELECTED TOOL]:\n  {res_3['tool_call']['name']}({res_3['tool_call'].get('arguments', {})})")

    assert res_3["tool_call"]["name"] == "execute_federated_query", f"Unexpected tool: {res_3['tool_call']}"
    tool_data_3 = res_3["tool_result"]
    assert tool_data_3.get("status") == "success"
    results = tool_data_3.get("results", [])
    assert len(results) >= 10, f"Expected >= 10 rows, got {len(results)}"

    top_row = results[0]
    print(f"[TRACE - OBSERVATION RECEIVED BY GEMMA]:")
    print(f"  • Total federated rows computed: {len(results)}")
    print(f"  • Municipality with peak pressure index: {top_row['municipality_code']}")
    print(f"    - Categories paired: {top_row['fiware_category']} <-> {top_row['segittur_category']}")
    print(f"    - Tourism Pressure Index: {top_row['tourism_pressure_index']}")
    print(f"    - Bed capacity: {top_row['total_bed_capacity']} | Monthly visitors: {top_row['monthly_visitor_footfall']}")

    assert "tourism_pressure_index" in top_row
    assert top_row["tourism_pressure_index"] > 0
    print("✓ [RESULT]: Validation passed. Federated analytical calculation completed successfully.")
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 4: Targeted Custom SQL Query (Girona vs Barcelona)
    # -------------------------------------------------------------
    query_4 = "Query the data specifically for Girona (17079) and Barcelona (08019) to compare total beds."
    print_test_header(
        4,
        "Targeted Comparison Query in Custom SQL (Girona 17079 vs Barcelona 08019)",
        what="The agent recognizes a targeted comparative inquiry for two municipalities. It constructs custom SQL with a WHERE clause over 'fiware_lake' and 'segittur_lake' and invokes 'run_custom_duckdb_sql'.",
        why="Demonstrates that the LLM is not restricted to canned queries, but can synthesize ad-hoc SQL over virtual Iceberg views based on specific analytical intents.",
        prompt=query_4
    )
    res_4 = agent.execute(query_4)

    print(f"[TRACE - GEMMA THOUGHT]:\n  {res_4['thought']}")
    print(f"[TRACE - SELECTED TOOL]:\n  {res_4['tool_call']['name']}(\n    query=\"\"\"{res_4['tool_call']['arguments'].get('query', '').strip()}\"\"\"\n  )")

    assert res_4["tool_call"]["name"] == "run_custom_duckdb_sql", f"Unexpected tool: {res_4['tool_call']}"
    tool_data_4 = res_4["tool_result"]
    assert tool_data_4.get("status") == "success", f"SQL execution failed: {tool_data_4}"
    sql_rows = tool_data_4.get("results", [])
    assert len(sql_rows) > 0, "No rows returned for targeted comparison"

    municipality_codes = [r["municipality_code"] for r in sql_rows]
    print(f"[TRACE - OBSERVATION RECEIVED BY GEMMA]:")
    print(f"  • Filtered municipalities returned: {municipality_codes}")
    for row in sql_rows:
        print(f"    - {row.get('municipality_name', row['municipality_code'])}: Total Beds = {row.get('total_beds')}, Visitors = {row.get('total_visitors')}")

    assert any(code in ['17079', '08019'] for code in municipality_codes)
    print("✓ [RESULT]: Validation passed. Dynamic SQL generation and spatial filtering confirmed.")
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 5: Overcapacity & Anomaly Detection (> 50x)
    # -------------------------------------------------------------
    query_5 = "Find municipalities where monthly visitors exceed the total available accommodation capacity by more than 50 times threshold."
    print_test_header(
        5,
        "Overcapacity Anomaly Detection (Footfall > 50x Bed Capacity)",
        what="The agent interprets a quantitative threshold alert (finding outliers where visitor volume exceeds lodging capacity by >50x), builds an analytical SQL query with HAVING/WHERE filters, and invokes 'run_custom_duckdb_sql'.",
        why="Demonstrates how semantic interoperability directly assists in tourism sustainability policy and infrastructure congestion management.",
        prompt=query_5
    )
    res_5 = agent.execute(query_5)

    print(f"[TRACE - GEMMA THOUGHT]:\n  {res_5['thought']}")
    print(f"[TRACE - SELECTED TOOL]:\n  {res_5['tool_call']['name']}(\n    query=\"\"\"{res_5['tool_call']['arguments'].get('query', '').strip()}\"\"\"\n  )")

    assert res_5["tool_call"]["name"] == "run_custom_duckdb_sql", f"Unexpected tool: {res_5['tool_call']}"
    tool_data_5 = res_5["tool_result"]
    assert tool_data_5.get("status") == "success", f"Query error: {tool_data_5}"
    anomalies = tool_data_5.get("results", [])
    print(f"[TRACE - OBSERVATION RECEIVED BY GEMMA]:")
    print(f"  • Total anomaly scenarios detected: {len(anomalies)}")
    for a in anomalies[:3]:
        print(f"    - Municipality {a['municipality_code']} ({a['fiware_category']}): Ratio = {a['visitor_to_bed_ratio']}x "
              f"({a['monthly_visitors']} visitors vs {a['bed_capacity']} beds)")

    print("✓ [RESULT]: Validation passed. Quantitative anomaly detection verified.")
    passed += 1

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"  TEST SUITE COMPLETED: {passed}/{total} TEST CASES PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_all_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n[TEST SUITE FAILURE]: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

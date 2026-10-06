import os
import sys
import time
import requests
from .agent import GemmaAgent
from .mcp_client import MCPClient

def wait_for_mcp_server(mcp_url: str, timeout: int = 30):
    health_url = f"{mcp_url}/health"
    print(f"[gemma-agent] Waiting for MCP Server at {health_url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                print("[gemma-agent] MCP Server is ready!")
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"MCP server at {mcp_url} did not become ready within {timeout}s")

def run_all_tests():
    print("=" * 70)
    print("  GEMMA LLM AGENT & MCP FEDERATION TEST SUITE (DEPLOYTOUR)  ")
    print("=" * 70)

    mcp = MCPClient()
    wait_for_mcp_server(mcp.base_url)
    agent = GemmaAgent(mcp_client=mcp)

    passed = 0
    total = 5

    # -------------------------------------------------------------
    # TEST CASE 1: Semantic Schema & Metric Discovery
    # -------------------------------------------------------------
    print("\n[TEST CASE 1/5] Semantic Schema Discovery via Apache Ossie (OSI)")
    query_1 = "What datasets and metrics are available in the DEPLOYTOUR semantic federation?"
    res_1 = agent.execute(query_1)

    assert res_1["tool_call"]["name"] == "list_semantic_entities", f"Unexpected tool: {res_1['tool_call']}"
    tool_data_1 = res_1["tool_result"]
    assert "datasets" in tool_data_1, "Missing datasets in result"
    assert "metrics" in tool_data_1, "Missing metrics in result"
    datasets_names = [d["id"] for d in tool_data_1["datasets"]]
    metrics_names = [m["id"] for m in tool_data_1["metrics"]]

    print(f"✓ Gemma Thought: {res_1['thought']}")
    print(f"✓ Discovered Datasets: {datasets_names}")
    print(f"✓ Discovered Metrics: {metrics_names}")
    assert "fiware_accommodations" in datasets_names
    assert "segittur_destinos" in datasets_names
    assert "TourismPressureIndex" in metrics_names
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 2: Cross-Ontology Mapping Resolution
    # -------------------------------------------------------------
    print("\n[TEST CASE 2/5] Cross-Ontology Mapping Resolution (FIWARE <-> SEGITTUR)")
    query_2 = "How do FIWARE categories map to SEGITTUR spaces, and what is the join key between them?"
    res_2 = agent.execute(query_2)

    assert res_2["tool_call"]["name"] == "get_ontology_mappings", f"Unexpected tool: {res_2['tool_call']}"
    tool_data_2 = res_2["tool_result"]
    assert "join_keys" in tool_data_2, "Missing join_keys"
    assert "taxonomy_alignments" in tool_data_2, "Missing taxonomy_alignments"

    join_key = tool_data_2["join_keys"][0]
    print(f"✓ Gemma Thought: {res_2['thought']}")
    print(f"✓ Join Key: FIWARE '{join_key['source_attribute']}' <=> SEGITTUR '{join_key['target_attribute']}'")
    print(f"✓ Alignments count: {len(tool_data_2['taxonomy_alignments'])}")
    assert join_key["source_attribute"] == "municipality_code"
    assert join_key["target_attribute"] == "codigo_ine_municipio"
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 3: Autonomous Cross-Lakehouse Tourism Pressure Query
    # -------------------------------------------------------------
    print("\n[TEST CASE 3/5] Cross-Lakehouse Tourism Pressure Analysis")
    query_3 = "Execute the federated query across both lakehouses and analyze the highest tourism pressure index."
    res_3 = agent.execute(query_3)

    assert res_3["tool_call"]["name"] == "execute_federated_query", f"Unexpected tool: {res_3['tool_call']}"
    tool_data_3 = res_3["tool_result"]
    assert tool_data_3.get("status") == "success"
    results = tool_data_3.get("results", [])
    assert len(results) >= 10, f"Expected >= 10 rows, got {len(results)}"

    top_row = results[0]
    print(f"✓ Gemma Thought: {res_3['thought']}")
    print(f"✓ Rows analyzed: {len(results)}")
    print(f"✓ Top Pressure Location: Municipality {top_row['municipality_code']} "
          f"({top_row['fiware_category']} <-> {top_row['segittur_category']}) "
          f"with Pressure Index = {top_row['tourism_pressure_index']}")
    assert "tourism_pressure_index" in top_row
    assert top_row["tourism_pressure_index"] > 0
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 4: Targeted Custom DuckDB SQL Query (Girona & Barcelona)
    # -------------------------------------------------------------
    print("\n[TEST CASE 4/5] Targeted Comparison Query for Girona (17079) and Barcelona (08019)")
    query_4 = "Query the data specifically for Girona (17079) and Barcelona (08019) to compare total beds."
    res_4 = agent.execute(query_4)

    assert res_4["tool_call"]["name"] == "run_custom_duckdb_sql", f"Unexpected tool: {res_4['tool_call']}"
    tool_data_4 = res_4["tool_result"]
    assert tool_data_4.get("status") == "success", f"SQL failed: {tool_data_4}"
    sql_rows = tool_data_4.get("results", [])
    assert len(sql_rows) > 0, "No rows returned for targeted query"

    municipality_codes = [r["municipality_code"] for r in sql_rows]
    print(f"✓ Gemma Thought: {res_4['thought']}")
    print(f"✓ Returned Municipalities: {municipality_codes}")
    for row in sql_rows:
        print(f"  - {row.get('municipality_name', row['municipality_code'])}: Total Beds = {row.get('total_beds')}, "
              f"Visitors = {row.get('total_visitors')}")
    assert any(code in ['17079', '08019'] for code in municipality_codes)
    passed += 1

    # -------------------------------------------------------------
    # TEST CASE 5: Overcapacity & Anomaly Threshold Detection
    # -------------------------------------------------------------
    print("\n[TEST CASE 5/5] Overcapacity Anomaly Detection (Visitors > 50x Capacity)")
    query_5 = "Find municipalities where monthly visitors exceed the total available accommodation capacity by more than 50 times threshold."
    res_5 = agent.execute(query_5)

    assert res_5["tool_call"]["name"] == "run_custom_duckdb_sql", f"Unexpected tool: {res_5['tool_call']}"
    tool_data_5 = res_5["tool_result"]
    assert tool_data_5.get("status") == "success", f"Query error: {tool_data_5}"
    anomalies = tool_data_5.get("results", [])
    print(f"✓ Gemma Thought: {res_5['thought']}")
    print(f"✓ Identified {len(anomalies)} overcapacity anomaly scenarios:")
    for a in anomalies[:3]:
        print(f"  - Municipality {a['municipality_code']} ({a['fiware_category']}): Ratio = {a['visitor_to_bed_ratio']}x "
              f"({a['monthly_visitors']} visitors vs {a['bed_capacity']} beds)")
    passed += 1

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"  TEST SUITE COMPLETED: {passed}/{total} TEST CASES PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_all_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n[TEST SUITE FAILURE]: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

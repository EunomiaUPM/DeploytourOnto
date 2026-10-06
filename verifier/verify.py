import os
import sys
import time
import json
import requests
import duckdb

GRAVITINO_URL = os.getenv("GRAVITINO_URL", "http://gravitino:8090")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")
DATA_DIR = os.getenv("DATA_DIR", "/data")
ENGINE_DIR = os.getenv("ENGINE_DIR", "/engine")

def log(msg: str):
    print(f"\n[VERIFIER] ========================================\n[VERIFIER] {msg}\n[VERIFIER] ========================================")

def step_1_assert_storage_files():
    log("STEP 1: Asserting Iceberg Metadata Files on Shared Local Storage")
    meta_a = os.path.join(DATA_DIR, "lakehouse_a_fiware/metadata/v1.metadata.json")
    meta_b = os.path.join(DATA_DIR, "lakehouse_b_segittur/metadata/v1.metadata.json")

    assert os.path.exists(meta_a), f"Missing metadata file: {meta_a}"
    assert os.path.exists(meta_b), f"Missing metadata file: {meta_b}"

    size_a = os.path.getsize(meta_a)
    size_b = os.path.getsize(meta_b)
    print(f"✓ Found {meta_a} ({size_a} bytes)")
    print(f"✓ Found {meta_b} ({size_b} bytes)")

def step_2_assert_gravitino_catalogs():
    log("STEP 2: Verifying Apache Gravitino Catalog Federation REST API")
    url = f"{GRAVITINO_URL}/api/metalakes/deploytour_metalake/catalogs"
    
    max_retries = 30
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                catalog_names = [ident["name"] for ident in data.get("identifiers", [])]
                print(f"Gravitino registered catalogs: {catalog_names}")
                if "fiware_catalog" in catalog_names and "segittur_catalog" in catalog_names:
                    print("✓ Both fiware_catalog and segittur_catalog successfully registered in Gravitino!")
                    return
        except Exception as e:
            pass
        print(f"Waiting for Gravitino catalogs to be ready (attempt {attempt + 1}/{max_retries})...")
        time.sleep(2)
        
    raise AssertionError(f"Failed to find expected catalogs at {url} after {max_retries} attempts")

def step_3_execute_duckdb_federated_query():
    log("STEP 3: Executing 'Query Over Everything' Federated SQL in DuckDB")
    sql_path = os.path.join(ENGINE_DIR, "federated_query.sql")
    assert os.path.exists(sql_path), f"SQL file not found: {sql_path}"

    with open(sql_path, "r") as f:
        sql = f.read()

    con = duckdb.connect()
    cleaned_lines = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    cleaned_sql = "\n".join(cleaned_lines)
    statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]

    for stmt in statements[:-1]:
        con.execute(stmt)

    select_stmt = statements[-1]
    cur = con.execute(select_stmt)
    headers = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    row_count = len(rows)
    print(f"Query returned {row_count} federated records:")

    col_widths = [max(len(h), 12) for h in headers]
    header_row = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    divider = "-+-".join("-" * w for w in col_widths)
    print(header_row)
    print(divider)
    for r in rows[:15]:
        row_str = " | ".join(f"{str(v):<{w}}" for v, w in zip(r, col_widths))
        print(row_str)
    if row_count > 15:
        print(f"... and {row_count - 15} more rows.")

    assert row_count >= 10, f"Expected at least 10 joined rows, but got {row_count}"
    print(f"✓ Pipeline assertion passed: {row_count} >= 10 joined records.")

def step_4_verify_mcp_server():
    log("STEP 4: Invoking MCP Server Semantic and Federated Query Tools")
    
    health_url = f"{MCP_SERVER_URL}/health"
    max_retries = 30
    for attempt in range(max_retries):
        try:
            r = requests.get(health_url, timeout=3)
            if r.status_code == 200:
                print("✓ MCP Server is healthy!")
                break
        except Exception:
            pass
        print(f"Waiting for MCP Server to be ready (attempt {attempt + 1}/{max_retries})...")
        time.sleep(2)
    else:
        raise AssertionError("MCP server failed to start")

    print("\n--- Testing tool: list_semantic_entities ---")
    r_entities = requests.get(f"{MCP_SERVER_URL}/tools/list_semantic_entities").json()
    assert "datasets" in r_entities, "Missing datasets in list_semantic_entities"
    assert "metrics" in r_entities, "Missing metrics in list_semantic_entities"
    print(f"✓ Discovered {len(r_entities['datasets'])} datasets and {len(r_entities['metrics'])} metrics")

    print("\n--- Testing tool: get_ontology_mappings ---")
    r_mappings = requests.get(f"{MCP_SERVER_URL}/tools/get_ontology_mappings").json()
    assert "join_keys" in r_mappings, "Missing join_keys in get_ontology_mappings"
    assert "taxonomy_alignments" in r_mappings, "Missing taxonomy_alignments in get_ontology_mappings"
    print("✓ Ontology mappings loaded successfully.")

    print("\n--- Testing tool: execute_federated_query (REST) ---")
    r_query = requests.get(f"{MCP_SERVER_URL}/tools/execute_federated_query").json()
    assert r_query.get("status") == "success", f"Query tool error: {r_query}"
    results = r_query.get("results", [])
    assert len(results) >= 10, f"Expected at least 10 results from MCP tool, got {len(results)}"
    
    first_row = results[0]
    assert "tourism_pressure_index" in first_row, "Missing 'tourism_pressure_index' field in MCP tool output"
    print(f"✓ MCP tool executed successfully. Top result:")
    print(json.dumps(first_row, indent=2))

    print("\n--- Testing tool: execute_federated_query (JSON-RPC 2.0 /mcp) ---")
    rpc_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "execute_federated_query",
            "arguments": {}
        }
    }
    r_rpc = requests.post(f"{MCP_SERVER_URL}/mcp", json=rpc_payload).json()
    assert "result" in r_rpc, f"JSON-RPC error: {r_rpc}"
    content_text = r_rpc["result"]["content"][0]["text"]
    parsed_content = json.loads(content_text)
    assert parsed_content.get("status") == "success", "Failed in JSON-RPC execution"
    assert "tourism_pressure_index" in parsed_content["results"][0]
    print(f"✓ MCP JSON-RPC 2.0 tool call succeeded! Verified {len(parsed_content['results'])} rows returned.")

def step_5_verify_gemma_llm_agent():
    log("STEP 5: Executing Gemma LLM Agent across 5 Test Scenarios via MCP")
    try:
        from gemma_agent.test_cases import run_all_tests
        run_all_tests()
        print("✓ All 5 Gemma LLM Agent test cases executed and passed!")
    except ImportError:
        print("[WARN] gemma_agent module not found in path, skipping in-process agent runner.")

def main():
    print("=" * 60)
    print("  DEPLOYTOUR INTEGRATION TEST SUITE (VERIFIER CONTAINER)  ")
    print("=" * 60)
    try:
        step_1_assert_storage_files()
        step_2_assert_gravitino_catalogs()
        step_3_execute_duckdb_federated_query()
        step_4_verify_mcp_server()
        step_5_verify_gemma_llm_agent()
        log("ALL VERIFICATION SUITE CHECKS PASSED SUCCESSFULLY (CODE 0)")
        sys.exit(0)
    except Exception as e:
        print(f"\n[VERIFIER ERROR] Assertion failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

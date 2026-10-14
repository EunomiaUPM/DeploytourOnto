<!--
Copyright 2024-2026 Universidad Politécnica de Madrid / Deploytour

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# DEPLOYTOUR: Evaluation of the `duckdb-ossie` Community Extension

This document reports on the experimental evaluation of the official **`duckdb-ossie`** community extension (maintained by [Iqea Technologies](https://github.com/iqea-ai/duckdb-ossie)) on the branch `feature/duckdb-ossie-test`.

---

## 1. Executive Summary

| Feature | `duckdb-ossie` Native Extension (Evaluated) | DEPLOYTOUR Python/FastMCP Bridge (Main) |
|---|---|---|
| **Repository** | [iqea-ai/duckdb-ossie](https://github.com/iqea-ai/duckdb-ossie) | In-tree [`mcp_server/server.py`](file:///Users/jsalvachua/OntoDeployTour/mcp_server/server.py) |
| **Engine Packaging** | Compiled DuckDB C++ community extension (`LOAD ossie;`) | Python application embedding DuckDB via standard wheels |
| **DuckDB Dependency** | Pinned to DuckDB **v1.5.5** community extension registry | DuckDB **v1.5.6+** (Latest stable) |
| **Model Format** | Apache Ossie JSON / YAML (`version: 0.2.0.dev0`) | Apache Ossie YAML specifications (`ossie/*.yaml`) |
| **Query Engine** | In-engine SQL compilation via `ossie_query` / `ossie_compile` | Python-orchestrated DuckDB with Iceberg / Spatial scan |
| **MCP Protocol** | Native DuckDB MCP via `duckdb_mcp` community extension | Python FastAPI / FastMCP server (JSON-RPC 2.0, REST, SSE) |
| **Evaluation Status** | **PASSED (All 6 test steps verified)** | **PASSED (Production baseline)** |

---

## 2. Test Architecture & Files

The evaluation files on branch `feature/duckdb-ossie-test`:

1. **Semantic Model:** [`ossie/duckdb_ossie_model.json`](file:///Users/jsalvachua/OntoDeployTour/ossie/duckdb_ossie_model.json)
   - Formatted to the official Apache Ossie specification (`version: 0.2.0.dev0`).
   - Declares `fiware_accommodations` and `segittur_destinos` datasets.
   - Declares the cross-ontology relationship: `municipality_code` $\leftrightarrow$ `codigo_ine_municipio`.
   - Defines metrics: `total_bed_capacity`, `total_monthly_visitors`, `estimated_monthly_expenditure_eur`.

2. **Test Runner:** [`test/test_duckdb_ossie.py`](file:///Users/jsalvachua/OntoDeployTour/test/test_duckdb_ossie.py)
   - Connects to DuckDB 1.5.5.
   - Installs and loads `ossie` and `duckdb_mcp` from community extension repository.
   - Populates test tables with Spanish destination data.
   - Executes model parsing, vocabulary discovery, SQL compilation, query execution, and MCP resource publishing.

3. **Dedicated Container Service:**
   - [`test/Dockerfile`](file:///Users/jsalvachua/OntoDeployTour/test/Dockerfile): Packages DuckDB 1.5.5 and pre-caches `ossie` and `duckdb_mcp` community extensions inside the image.
   - [`docker-compose.yml`](file:///Users/jsalvachua/OntoDeployTour/docker-compose.yml): Registers the `duckdb-ossie-tester` service under profile `test`.

4. **Docker Execution Script:** [`run_duckdb_ossie_test.sh`](file:///Users/jsalvachua/OntoDeployTour/run_duckdb_ossie_test.sh)
   - Runs `docker compose build duckdb-ossie-tester && docker compose run --rm duckdb-ossie-tester` for 100% containerized execution.

---

## 3. Test Execution Results

Running `./run_duckdb_ossie_test.sh`:

```text
================================================================================
  DEPLOYTOUR: DUCKDB-OSSIE COMMUNITY EXTENSION EVALUATION SUITE  
  Testing reference: https://github.com/iqea-ai/duckdb-ossie  
================================================================================
DuckDB Version: 1.5.5

================================================================================
 STEP 1: INSTALL & LOAD DUCKDB-OSSIE & DUCKDB_MCP
================================================================================
 ▶ WHAT IT DOES:
   Installs 'ossie' and 'duckdb_mcp' community extensions directly from DuckDB's community repository.
 ▶ WHY IT DOES IT:
   Validates that the native binary extension built by Iqea can be fetched, verified, and loaded into DuckDB.
--------------------------------------------------------------------------------
✓ Successfully loaded 'ossie' community extension!
✓ Successfully loaded 'duckdb_mcp' community extension!

================================================================================
 STEP 2: INITIALIZE PHYSICAL TABLES FOR DUAL ONTOLOGIES
================================================================================
 ▶ WHAT IT DOES:
   Creates sample tables in DuckDB (fiware_accommodations & segittur_destinos) representing Spanish municipalities.
 ▶ WHY IT DOES IT:
   Provides the underlying physical storage required by duckdb-ossie datasets.
--------------------------------------------------------------------------------
✓ Tables 'fiware_accommodations' (6 rows) and 'segittur_destinos' (4 rows) initialized.

================================================================================
 STEP 3: PARSE AND VALIDATE MODEL VIA OSSIE_LOAD
================================================================================
 ▶ WHAT IT DOES:
   Executes CALL ossie_load('ossie/duckdb_ossie_model.json') to parse datasets, fields, relationships, and metrics.
 ▶ WHY IT DOES IT:
   Tests duckdb-ossie's C++ schema validator against our DEPLOYTOUR cross-ontology JSON model.
--------------------------------------------------------------------------------
✓ Successfully loaded model from 'ossie/duckdb_ossie_model.json' without errors!

================================================================================
 STEP 4: INSPECT VOCABULARY & MODEL METADATA FUNCTIONS
================================================================================
 ▶ WHAT IT DOES:
   Queries ossie_datasets(), ossie_fields(), ossie_metrics(), and ossie_relationships().
 ▶ WHY IT DOES IT:
   Validates that AI agents can inspect the semantic vocabulary without guessing column names.
--------------------------------------------------------------------------------
[DISCOVERY] Datasets found in duckdb-ossie:
  • fiware_accommodations (Source: memory.main.fiware_accommodations)
  • segittur_destinos (Source: memory.main.segittur_destinos)

[DISCOVERY] Metrics found in duckdb-ossie:
  • total_bed_capacity [Integer]: Total available lodging beds in the municipality
  • total_monthly_visitors [Integer]: Total monthly visitor volume at the destination
  • estimated_monthly_expenditure_eur [Double]: Estimated total monthly tourist expenditure in Euros

[DISCOVERY] Relationships found in duckdb-ossie:
  • accommodation_to_destination_by_ine: fiware_accommodations -> segittur_destinos on ['municipality_code'] = ['codigo_ine_municipio']

================================================================================
 STEP 5: COMPILE AND EXECUTE SEMANTIC QUERIES VIA OSSIE_COMPILE / OSSIE_QUERY
================================================================================
 ▶ WHAT IT DOES:
   Calls ossie_compile to view generated SQL, and calls ossie_query to execute the semantic query.
 ▶ WHY IT DOES IT:
   Verifies that duckdb-ossie autonomously plans the GROUP BY and aggregations across declared grains.
--------------------------------------------------------------------------------
[QUERY 1] Computing total bed capacity grouped by municipality...
  [Compiled SQL]:
  SELECT fiware_accommodations.municipality_code AS "fiware_accommodations.municipality_code", 
         sum(fiware_accommodations.capacity_beds) AS total_bed_capacity 
  FROM memory.main.fiware_accommodations AS fiware_accommodations 
  GROUP BY fiware_accommodations.municipality_code

  [Execution Result]:
  Municipality | Total Beds
  -------------+-----------
  17079        | 250
  35016        | 172
  28079        | 570
  08019        | 460

[QUERY 2] Computing monthly visitors and spend grouped by destination municipality...
  INE Code | Monthly Visitors | Estimated Spend (€)
  ---------+------------------+--------------------
  08019    | 580000           | €92,800,000.00
  35016    | 115262           | €19,143,865.58
  17079    | 85000            | €8,075,000.00
  28079    | 450000           | €65,475,000.00

================================================================================
 STEP 6: MODEL CONTEXT PROTOCOL (MCP) TOOL & QUERY PUBLISHING
================================================================================
 ▶ WHAT IT DOES:
   Uses PRAGMA mcp_publish_query and PRAGMA mcp_publish_tool to expose duckdb-ossie tools natively over MCP.
 ▶ WHY IT DOES IT:
   Demonstrates how duckdb-ossie and duckdb_mcp allow external LLM agents to interface with the semantic layer natively.
--------------------------------------------------------------------------------
✓ Successfully published 'metrics' and 'dimensions' MCP resources via duckdb_mcp!

================================================================================
  ✓ ALL DUCKDB-OSSIE COMMUNITY EXTENSION TESTS PASSED SUCCESSFULLY! (CODE 0)
================================================================================
```

---

## 4. Key Takeaways & Recommendations

1. **`duckdb-ossie` is fully functional and validated:**
   The community extension by Iqea works cleanly inside DuckDB 1.5.5, parsing the DEPLOYTOUR semantic model, resolving relationships, and emitting valid SQL aggregations.

2. **Integration with `duckdb_mcp`:**
   Together with `duckdb_mcp`, `duckdb-ossie` allows exposing semantic queries and metrics directly to AI agents over the Model Context Protocol without an intermediate web framework.

3. **Specification Modernization (Ossie 0.2.0.dev0):**
   - The model format in [`ossie/duckdb_ossie_model.json`](file:///Users/jsalvachua/OntoDeployTour/ossie/duckdb_ossie_model.json) has been updated to root-level property declarations per the latest `duckdb-ossie 0.2.0.dev0` C++ specification.
   - DuckDB ABI compatibility verified across both DuckDB 1.5.5 and 1.5.6.

4. **Production Integration into Primary MCP Server:**
   - As delivered in Phase 2, `mcp_server/server.py` now attempts loading the native `ossie` community extension on startup.
   - Exposed two new first-class MCP tools:
     - `compile_semantic_query`: Calls `ossie_compile` to generate ANSI SQL dynamically across dimensions and metrics.
     - `execute_semantic_query`: Calls `ossie_query` to return records directly from multi-grain semantic models.
   - The primary server combines the robustness of the FastMCP JSON-RPC/REST server with the dynamic compilation speed of `duckdb-ossie`.

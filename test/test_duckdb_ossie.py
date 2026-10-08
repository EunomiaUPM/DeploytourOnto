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
import json
import duckdb

def log_step(title, what, why):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)
    print(f" ▶ WHAT IT DOES:")
    print(f"   {what}")
    print(f" ▶ WHY IT DOES IT:")
    print(f"   {why}")
    print("-" * 80)

def main():
    print("=" * 80)
    print("  DEPLOYTOUR: DUCKDB-OSSIE COMMUNITY EXTENSION EVALUATION SUITE  ")
    print("  Testing reference: https://github.com/iqea-ai/duckdb-ossie  ")
    print("=" * 80)
    print(f"DuckDB Version: {duckdb.__version__}")

    model_path = os.getenv("OSSIE_MODEL_PATH", "ossie/duckdb_ossie_model.json")
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at: {model_path}", file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect()

    # Step 1: Install & Load Community Extensions
    log_step(
        "Step 1: Install & Load duckdb-ossie & duckdb_mcp",
        what="Installs 'ossie' and 'duckdb_mcp' community extensions directly from DuckDB's community repository.",
        why="Validates that the native binary extension built by Iqea can be fetched, verified, and loaded into DuckDB."
    )
    con.execute("INSTALL ossie FROM community; LOAD ossie;")
    print("✓ Successfully loaded 'ossie' community extension!")
    con.execute("INSTALL duckdb_mcp FROM community; LOAD duckdb_mcp;")
    print("✓ Successfully loaded 'duckdb_mcp' community extension!")

    # Step 2: Populate In-Memory Tables
    log_step(
        "Step 2: Initialize Physical Tables for Dual Ontologies",
        what="Creates sample tables in DuckDB (fiware_accommodations & segittur_destinos) representing Spanish municipalities.",
        why="Provides the underlying physical storage required by duckdb-ossie datasets."
    )
    con.execute("""
    CREATE TABLE fiware_accommodations (
        id VARCHAR PRIMARY KEY,
        municipality_code VARCHAR,
        category VARCHAR,
        capacity_beds INTEGER,
        occupancy_rate DOUBLE
    );
    INSERT INTO fiware_accommodations VALUES
        ('acc-001', '28079', 'Hotel', 450, 0.85),
        ('acc-002', '28079', 'Apartment', 120, 0.70),
        ('acc-003', '08019', 'Hotel', 380, 0.90),
        ('acc-004', '08019', 'Hostal', 80, 0.65),
        ('acc-005', '17079', 'Camping', 250, 0.50),
        ('acc-006', '35016', 'Hostal', 172, 0.95);
    """)

    con.execute("""
    CREATE TABLE segittur_destinos (
        id_destino VARCHAR PRIMARY KEY,
        codigo_ine_municipio VARCHAR,
        tipo_espacio VARCHAR,
        visitantes_mensuales INTEGER,
        gasto_medio_diario_eur DOUBLE
    );
    INSERT INTO segittur_destinos VALUES
        ('dest-001', '28079', 'RecursoCultural', 450000, 145.50),
        ('dest-002', '08019', 'RecursoCultural', 580000, 160.00),
        ('dest-003', '17079', 'EspacioNatural', 85000, 95.00),
        ('dest-004', '35016', 'RecursoCultural', 115262, 166.09);
    """)
    print("✓ Tables 'fiware_accommodations' (6 rows) and 'segittur_destinos' (4 rows) initialized.")

    # Step 3: Load Model via ossie_load
    log_step(
        "Step 3: Parse and Validate Model via ossie_load",
        what=f"Executes CALL ossie_load('{model_path}') to parse datasets, fields, relationships, and metrics.",
        why="Tests duckdb-ossie's C++ schema validator against our DEPLOYTOUR cross-ontology JSON model."
    )
    con.execute(f"CALL ossie_load('{model_path}');")
    print(f"✓ Successfully loaded model from '{model_path}' without errors!")

    # Step 4: Verify Discovery Functions
    log_step(
        "Step 4: Inspect Vocabulary & Model Metadata Functions",
        what="Queries ossie_datasets(), ossie_fields(), ossie_metrics(), and ossie_relationships().",
        why="Validates that AI agents can inspect the semantic vocabulary without guessing column names."
    )
    
    # Datasets
    datasets = con.execute("SELECT name, source FROM ossie_datasets()").fetchall()
    print("[DISCOVERY] Datasets found in duckdb-ossie:")
    for d in datasets:
        print(f"  • {d[0]} (Source: {d[1]})")
    assert len(datasets) == 2, f"Expected 2 datasets, got {len(datasets)}"

    # Metrics
    metrics = con.execute("SELECT name, datatype, description FROM ossie_metrics()").fetchall()
    print("\n[DISCOVERY] Metrics found in duckdb-ossie:")
    for m in metrics:
        print(f"  • {m[0]} [{m[1]}]: {m[2]}")
    assert len(metrics) == 3, f"Expected 3 metrics, got {len(metrics)}"

    # Relationships
    rels = con.execute("SELECT name, from_dataset, to_dataset, from_columns, to_columns FROM ossie_relationships()").fetchall()
    print("\n[DISCOVERY] Relationships found in duckdb-ossie:")
    for r in rels:
        print(f"  • {r[0]}: {r[1]} -> {r[2]} on {r[3]} = {r[4]}")
    assert len(rels) >= 1, "Expected at least 1 relationship"

    # Step 5: Test ossie_compile & ossie_query
    log_step(
        "Step 5: Compile and Execute Semantic Queries via ossie_compile / ossie_query",
        what="Calls ossie_compile to view generated SQL, and calls ossie_query to execute the semantic query.",
        why="Verifies that duckdb-ossie autonomously plans the GROUP BY and aggregations across declared grains."
    )

    # 5a. Query single-dataset metric
    print("[QUERY 1] Computing total bed capacity grouped by municipality...")
    compile_res = con.execute("SELECT ossie_compile(['total_bed_capacity'], ['fiware_accommodations.municipality_code'], [])").fetchone()[0]
    print(f"  [Compiled SQL]:\n  {compile_res.strip()}")

    query_res = con.execute("SELECT * FROM ossie_query(['total_bed_capacity'], ['fiware_accommodations.municipality_code'], [])").fetchall()
    print("\n  [Execution Result]:")
    print("  Municipality | Total Beds")
    print("  -------------+-----------")
    for r in query_res:
        print(f"  {r[0]:<12} | {r[1]}")
    assert len(query_res) > 0, "Expected query results"

    # 5b. Query destination metrics
    print("\n[QUERY 2] Computing monthly visitors and spend grouped by destination municipality...")
    query_res_2 = con.execute("SELECT * FROM ossie_query(['total_monthly_visitors', 'estimated_monthly_expenditure_eur'], ['segittur_destinos.codigo_ine_municipio'], [])").fetchall()
    print("  INE Code | Monthly Visitors | Estimated Spend (€)")
    print("  ---------+------------------+--------------------")
    for r in query_res_2:
        print(f"  {r[0]:<8} | {r[1]:<16} | €{r[2]:,.2f}")
    assert len(query_res_2) > 0

    # Step 6: Test duckdb_mcp publishing
    log_step(
        "Step 6: Model Context Protocol (MCP) Tool & Query Publishing",
        what="Uses PRAGMA mcp_publish_query and PRAGMA mcp_publish_tool to expose duckdb-ossie tools natively over MCP.",
        why="Demonstrates how duckdb-ossie and duckdb_mcp allow external LLM agents to interface with the semantic layer natively."
    )
    con.execute("PRAGMA mcp_publish_query('metrics', 'SELECT name, description FROM ossie_metrics()');")
    con.execute("PRAGMA mcp_publish_query('dimensions', 'SELECT dataset, name, datatype FROM ossie_fields()');")
    print("✓ Successfully published 'metrics' and 'dimensions' MCP resources via duckdb_mcp!")

    print("\n" + "=" * 80)
    print("  ✓ ALL DUCKDB-OSSIE COMMUNITY EXTENSION TESTS PASSED SUCCESSFULLY! (CODE 0)")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[TEST FAILED]: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

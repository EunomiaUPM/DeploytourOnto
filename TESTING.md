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

# DEPLOYTOUR: Testing Guide & Cross-Ontology Query Mechanics

This document provides a comprehensive technical walkthrough of how cross-ontology federation works in the **DEPLOYTOUR** Proof of Concept (PoC), how SQL queries bridge disparate conceptual schemas across Apache Iceberg lakehouses, and how the automated test suite validates the system. *(For a complete architectural breakdown of the query resolution lifecycle, sequence diagrams, and agent reasoning loops, see [WORKFLOW.md](file:///Users/jsalvachua/OntoDeployTour/WORKFLOW.md).)*

---

## 1. Cross-Ontology Query Mechanics

### 1.1 The Semantic Divergence Problem

In European and Spanish tourism ecosystems, regional authorities, municipalities, and smart destination platforms store data under fundamentally different domain ontologies:

| Feature | Lakehouse A: FIWARE Smart Data Models | Lakehouse B: SEGITTUR / Schema.org |
|---|---|---|
| **Primary Domain Focus** | Physical tourist infrastructure and accommodation capacity | Footfall, visitor flows, economic expenditure, and destination types |
| **Entities** | `TouristDestination`, `Accommodation` | `PuntoDeInteresTuristico`, `DestinoTuristicoFlujo` |
| **Geographic Identifier** | `municipality_code` (5-digit INE code, string) | `codigo_ine_municipio` (5-digit INE code, string) |
| **Taxonomy / Typology** | English classifications (`Hotel`, `Hostal`, `Apartment`, `Camping`) | Spanish administrative classifications (`AlojamientoHotelero`, `RecursoCultural`, `EspacioNatural`, `ZonaAcampada`) |
| **Capacity vs. Demand** | Supply-side: `capacity_beds`, `occupancy_rate` | Demand-side: `visitantes_mensuales`, `gasto_medio_diario_eur` |

Independently, neither dataset can calculate critical management indicators such as **Tourism Pressure** (how many visitors compete for local bed capacity) or **Economic Intensity per Bed**.

---

### 1.2 The Semantic Resolution Pipeline

To query across both ontologies without moving or reformatting raw parquet files, DEPLOYTOUR uses a 4-step semantic resolution pipeline:

```text
[Lakehouse A (FIWARE)]                          [Lakehouse B (SEGITTUR)]
  ├── TouristDestination                          ├── PuntoDeInteresTuristico
  └── Accommodation                               └── DestinoTuristicoFlujo
        │                                               │
        │                                               │
        ▼                                               ▼
[Apache Gravitino Catalog]                     [Apache Gravitino Catalog]
  └── fiware_catalog                             └── segittur_catalog
        │                                               │
        └───────────────────────┬───────────────────────┘
                                │
                                ▼
                   [Apache Ossie (OSI) Layer]
                   ├── datasets.yaml (Entity definitions)
                   ├── mappings.yaml (Taxonomy & key equivalence)
                   └── metrics.yaml  (Derived mathematical models)
                                │
                                ▼
               [DuckDB Federated Execution Engine]
               ├── Iceberg Extension (Metadata & Snapshot scan)
               ├── Cross-Ontology JOIN on INE code + taxonomy map
               └── Window Aggregation & Metric computation
                                │
                                ▼
                 [Model Context Protocol (MCP)]
                 └── Structured JSON / Gemma LLM Agent
```

---

### 1.3 The Semantic Join & Metric Calculation (DuckDB SQL)

The core query resides in `engine/federated_query.sql`. It performs a cross-ontology join directly over Iceberg tables:

```sql
-- 1. Create virtual Iceberg views using DuckDB iceberg_scan
CREATE OR REPLACE VIEW fiware_lake AS 
SELECT * FROM iceberg_scan('/data/lakehouse_a_fiware');

CREATE OR REPLACE VIEW segittur_lake AS 
SELECT * FROM iceberg_scan('/data/lakehouse_b_segittur');

-- 2. Execute cross-ontology join and metric calculations
SELECT 
    f.municipality_code,
    f.category AS fiware_category,
    s.tipo_espacio AS segittur_category,
    COUNT(DISTINCT f.id) AS accommodation_count,
    SUM(f.capacity_beds) AS total_bed_capacity,
    ROUND(SUM(f.capacity_beds * f.occupancy_rate), 1) AS estimated_active_guests,
    SUM(s.visitantes_mensuales) AS monthly_visitor_footfall,
    ROUND(SUM(s.visitantes_mensuales * s.gasto_medio_diario_eur), 2) AS estimated_monthly_spend_eur,
    ROUND(
        CAST(SUM(s.visitantes_mensuales) AS DOUBLE) / 
        NULLIF(SUM(f.capacity_beds) * 30.0, 0), 
        2
    ) AS tourism_pressure_index
FROM fiware_lake f
JOIN segittur_lake s 
    ON f.municipality_code = s.codigo_ine_municipio
    AND (
        (f.category = 'Hotel' AND s.tipo_espacio IN ('AlojamientoHotelero', 'RecursoCultural', 'EspacioNatural')) OR
        (f.category = 'Hostal' AND s.tipo_espacio IN ('AlojamientoHotelero', 'RecursoCultural')) OR
        (f.category = 'Apartment' AND s.tipo_espacio IN ('AlojamientoHotelero', 'EspacioNatural', 'RecursoCultural')) OR
        (f.category = 'Camping' AND s.tipo_espacio IN ('ZonaAcampada', 'EspacioNatural', 'RecursoCultural'))
    )
GROUP BY f.municipality_code, f.category, s.tipo_espacio
ORDER BY tourism_pressure_index DESC;
```

#### Key Join Rules:
1. **Spatial / Administrative Key:** `f.municipality_code = s.codigo_ine_municipio` bridges FIWARE's ISO/INE municipality codes with SEGITTUR's Spanish INE coding.
2. **Taxonomic Equivalence:** The `mappings.yaml` ontology alignment maps FIWARE accommodation categories to compatible SEGITTUR space types.
3. **Derived Metrics:**
   - **`estimated_active_guests`:** $\sum(\text{capacity\_beds} \times \text{occupancy\_rate})$
   - **`estimated_monthly_spend_eur`:** $\sum(\text{visitantes\_mensuales} \times \text{gasto\_medio\_diario\_eur})$
   - **`tourism_pressure_index`:** $\frac{\sum \text{visitantes\_mensuales}}{\sum \text{capacity\_beds} \times 30.0}$ (Ratio of monthly demand to total monthly bed-night supply).

---

## 2. The 5 Automated Test Scenarios & Explanatory Traces

The test suite ([`verifier/verify.py`](file:///Users/jsalvachua/OntoDeployTour/verifier/verify.py) and [`gemma_agent/test_cases.py`](file:///Users/jsalvachua/OntoDeployTour/gemma_agent/test_cases.py)) is designed to output **detailed step-by-step explanatory traces** showing:
1. **▶ QUÉ HACE:** The exact technical operation being executed (files verified, REST API queried, SQL run, or tool called).
2. **▶ PARA QUÉ LO HACE:** The architectural, semantic, or business motivation behind the test.
3. **[TRAZA]:** The raw intermediate observation received by the system or LLM.
4. **✓ [RESULTADO]:** The specific assertions validated and success criteria.

```text
+-----------------------------------------------------------------------------------+
|                              5 TEST SCENARIOS MATRIX                              |
+---+-----------------------------+---------------------------+---------------------+
| # | Scenario Name               | MCP Tool Invoked          | Verification Target |
+---+-----------------------------+---------------------------+---------------------+
| 1 | Semantic Schema Discovery   | list_semantic_entities    | Ossie entities/dims |
| 2 | Ontology Mapping Resolution | get_ontology_mappings     | Keys & taxonomy map |
| 3 | Tourism Pressure Analysis   | execute_federated_query   | 73 rows, Top Index  |
| 4 | Targeted City Comparison    | run_custom_duckdb_sql     | Girona vs Barcelona |
| 5 | Overcapacity Anomaly Scan   | run_custom_duckdb_sql     | Ratio > 50x bounds  |
+---+-----------------------------+---------------------------+---------------------+
```

---

### Test Case 1: Semantic Schema & Metric Discovery

* **User Prompt:** `"What datasets and metrics are available in the DEPLOYTOUR semantic federation?"`
* **Agent Reasoning:** The user wants to discover registered datasets, schema entities, and metrics. The agent calls `list_semantic_entities`.
* **MCP Tool:** `list_semantic_entities()`
* **Verification Assertions:**
  1. Datasets include `fiware_accommodations` and `segittur_destinos`.
  2. Metrics include `TotalBeds`, `EffectiveGuests`, `MonthlyTourismExpenditure`, and `TourismPressureIndex`.
* **Sample Output:**
  ```json
  {
    "datasets": ["fiware_accommodations", "segittur_destinos"],
    "metrics": ["TotalBeds", "EffectiveGuests", "MonthlyTourismExpenditure", "TourismPressureIndex"]
  }
  ```

---

### Test Case 2: Cross-Ontology Mapping Resolution

* **User Prompt:** `"How do FIWARE categories map to SEGITTUR spaces, and what is the join key between them?"`
* **Agent Reasoning:** The user asks about ontological equivalence and join keys between FIWARE Smart Data Models and SEGITTUR. The agent calls `get_ontology_mappings`.
* **MCP Tool:** `get_ontology_mappings()`
* **Verification Assertions:**
  1. Primary join key is confirmed as `municipality_code` $\leftrightarrow$ `codigo_ine_municipio`.
  2. Taxonomy alignment confirmed: `Hotel` $\rightarrow$ `AlojamientoHotelero`, `Camping` $\rightarrow$ `ZonaAcampada`.
* **Sample Output:**
  ```json
  {
    "join_keys": {
      "fiware": "municipality_code",
      "segittur": "codigo_ine_municipio"
    },
    "category_alignments": [
      {"fiware": "Hotel", "segittur": "AlojamientoHotelero"},
      {"fiware": "Hostal", "segittur": "AlojamientoHotelero"},
      {"fiware": "Apartment", "segittur": "AlojamientoHotelero"},
      {"fiware": "Camping", "segittur": "ZonaAcampada"}
    ]
  }
  ```

---

### Test Case 3: Autonomous Cross-Lakehouse Tourism Pressure Analysis

* **User Prompt:** `"Execute the federated query across both lakehouses and analyze the highest tourism pressure index."`
* **Agent Reasoning:** The user requests end-to-end analytics across both Iceberg data lakes to find peak tourism pressure. The agent invokes `execute_federated_query`.
* **MCP Tool:** `execute_federated_query()`
* **Verification Assertions:**
  1. Record count $N \ge 10$ (Actual: 73 joined records).
  2. Successfully computes `tourism_pressure_index`.
  3. Correctly identifies the most pressured destination (Municipality `35016` / Las Palmas with pressure index `22.34`).
* **Sample Output:**
  ```json
  {
    "municipality_code": "35016",
    "fiware_category": "Hostal",
    "segittur_category": "RecursoCultural",
    "total_bed_capacity": 172,
    "monthly_visitor_footfall": 115262,
    "estimated_monthly_spend_eur": 19143662.63,
    "tourism_pressure_index": 22.34
  }
  ```

---

### Test Case 4: Targeted Comparison Query (Girona vs. Barcelona)

* **User Prompt:** `"Query the data specifically for Girona (17079) and Barcelona (08019) to compare total beds."`
* **Agent Reasoning:** The user wants a targeted slice of the federated data focusing on Girona (INE `17079`) and Barcelona (INE `08019`). The agent generates targeted SQL and invokes `run_custom_duckdb_sql`.
* **MCP Tool:** `run_custom_duckdb_sql(query="...")`
* **Verification Assertions:**
  1. Returned results contain exactly INE codes `17079` and `08019`.
  2. Aggregated bed counts and visitor numbers are non-zero:
     - **Girona (`17079`):** Total Beds = 13,602 | Monthly Visitors = 512,568
     - **Barcelona (`08019`):** Total Beds = 5,694 | Monthly Visitors = 688,250
* **Gemma Synthesis:**
  Provides structured comparison highlighting Barcelona's higher monthly footfall versus Girona's higher bed density.

---

### Test Case 5: Overcapacity & Anomaly Detection

* **User Prompt:** `"Find municipalities where monthly visitors exceed the total available accommodation capacity by more than 50 times threshold."`
* **Agent Reasoning:** The user wants outlier detection where monthly visitor volume outstrips physical lodging by an extreme ratio ($> 50\times$). The agent builds an analytical query with `HAVING (visitors / beds) > 50`.
* **MCP Tool:** `run_custom_duckdb_sql(query="...")`
* **Verification Assertions:**
  1. Anomalies are detected and returned ($N \ge 1$).
  2. Peak ratio identified:
     - Municipality `35016` (Hostal): Ratio = $670.1\times$ ($115,262$ visitors vs $172$ beds).
     - Municipality `07040` (Apartment): Ratio = $666.5\times$ ($29,991$ visitors vs $45$ beds).
* **Gemma Synthesis:**
  Synthesizes policy recommendations for seasonal capacity expansion and visitor management in high-stress zones.

---

### Test Case 6: Spatial Geodesic Proximity Analysis (GIS)

* **User Prompt:** `"Analyze spatial proximity and distance between accommodations and tourist POIs within 10 km radius."`
* **Agent Reasoning:** The user needs hyper-local spatial proximity calculations between physical lodging (Lakehouse A) and destination POIs/resources (Lakehouse B). The agent invokes `execute_spatial_proximity_query`.
* **MCP Tool:** `execute_spatial_proximity_query(municipality_code=None, max_distance_km=10.0, limit=20)`
* **Verification Assertions:**
  1. Evaluates true geodesic WGS84 distance using DuckDB's `ST_Distance_Spheroid(ST_Point(lon, lat), ST_Point(lon, lat))`.
  2. Returns paired records with `distance_km` calculated in kilometers.
* **Gemma Synthesis:**
  Produces a structured table associating accommodations with proximate cultural/natural POIs.

---

### Test Case 7: Seasonal & Temporal Tourism Pressure Dynamics

* **User Prompt:** `"Analyze seasonal tourism pressure variations and summer peak swings."`
* **Agent Reasoning:** Tourism congestion is highly temporal. The agent routes to `execute_temporal_pressure_query` to evaluate Spanish seasonal variance models.
* **MCP Tool:** `execute_temporal_pressure_query(municipality_code=None)`
* **Verification Assertions:**
  1. Computes quarterly pressure indices across Winter (0.65x), Spring (1.05x), Summer Peak (1.55x), and Autumn (0.85x).
  2. Evaluates the seasonal variance swing ($\Delta$) for municipal infrastructure planning.
* **Gemma Synthesis:**
  Highlights destinations with extreme seasonal swings requiring temporary public service adjustments.

---

### Test Case 8: SQL Sanitization Security Guardrails

* **Probe Action:** Malicious SQL injection attempt (`DROP TABLE fiware_lake`).
* **Technical Intent:** Verifies that external agents or compromised prompts cannot execute mutating SQL statements, DDL commands, or host OS calls.
* **MCP Tool:** `run_custom_duckdb_sql(query="DROP TABLE fiware_lake")`
* **Verification Assertions:**
  1. Returns `status: "error"`.
  2. Error message explicitly cites security policy violation: only read-only `SELECT` / `WITH` statements permitted.
* **Outcome:**
  Guarantees analytical safety without sacrificing ad-hoc querying flexibility.

---

### Test Case 9: Native Dynamic Semantic Compilation (duckdb-ossie)

* **User Prompt:** `"Compile semantic metrics for total bed capacity using Ossie compile."`
* **Agent Reasoning:** Tests dynamic semantic compilation where business metrics are translated into ANSI SQL by the C++ engine rather than manual authoring.
* **MCP Tool:** `compile_semantic_query(metrics=["total_bed_capacity"], dimensions=["fiware_accommodations.municipality_code"])`
* **Verification Assertions:**
  1. Returns `status: "success"`.
  2. Produces valid compiled ANSI SQL with automated `GROUP BY` and metric aggregations.
* **Gemma Synthesis:**
  Displays the dynamically compiled SQL query to the user for full transparency.

---

## 3. How to Run the Tests

### Option A: Run Tests Against Live Infrastructure (Recommended)

When the infrastructure is already running via `./start_infra.sh`:

```bash
./run_tests.sh
```

This runs the containerized `verifier` service, which:
1. Validates physical Iceberg metadata files on `/data`.
2. Probes the Apache Gravitino REST API (`http://gravitino:8090/api/v1/metalakes`).
3. Executes direct DuckDB SQL over the Iceberg lakehouses.
4. Tests the MCP REST and JSON-RPC endpoints.
5. Executes all 9 Gemma agent test cases.

### Option B: All-in-One CI/CD Execution

Tears down any existing state, builds all containers, bootstraps the catalog, runs the full verification suite, and exits with code `0`:

```bash
./run.sh
```

### Option C: Ad-Hoc Natural Language Testing

Test any custom prompt via the Gemma Agent CLI:

```bash
# Specific query
./query.sh "What is the tourism pressure in Madrid?"

# Interactive REPL
./query.sh
```

---

## 4. Native DuckDB Apache Ossie Community Extension Testing (`duckdb-ossie`)

In addition to our production FastAPI/FastMCP semantic bridge, branch `feature/duckdb-ossie-test` introduces an automated, containerized evaluation of the official **`duckdb-ossie`** community extension developed by [Iqea Technologies](https://github.com/iqea-ai/duckdb-ossie) alongside **`duckdb_mcp`**.

### 4.1 Purpose of the Evaluation
While DEPLOYTOUR's primary engine uses Python/FastMCP to federate Iceberg tables and provide full REST/JSON-RPC/SSE interfaces, `duckdb-ossie` embeds the semantic layer **directly inside DuckDB's C++ core**. Evaluating this extension allows us to verify:
1. In-engine parsing of declarative Apache Ossie JSON models (`version: 0.2.0.dev0`).
2. Automatic generation and compilation of SQL aggregations and GROUP BY clauses across multiple grains without manual SQL authoring (`ossie_compile`, `ossie_query`).
3. Native publishing of semantic queries as MCP tools directly through DuckDB's `duckdb_mcp` community extension.

### 4.2 The 6 Automated Test Steps

The test suite ([`test/test_duckdb_ossie.py`](file:///Users/jsalvachua/OntoDeployTour/test/test_duckdb_ossie.py)) runs inside a dedicated Docker container (`duckdb-ossie-tester`):

```text
+---------------------------------------------------------------------------------------------+
|                           DUCKDB-OSSIE EVALUATION PIPELINE (6 STEPS)                        |
+---+--------------------------+------------------------------+-------------------------------+
| # | Step Name                | Operation / SQL Call         | Verification Objective        |
+---+--------------------------+------------------------------+-------------------------------+
| 1 | Extension Loading        | INSTALL/LOAD ossie, mcp      | Community registry binary ABI |
| 2 | Table Initialization     | CREATE TABLE memory.main.*   | Dual ontology physical storage|
| 3 | Model Parsing            | CALL ossie_load('model.json')| C++ schema validator check    |
| 4 | Vocabulary Discovery     | ossie_datasets/metrics/rel() | Semantic catalog introspection|
| 5 | Query Compilation & Exec | ossie_compile / ossie_query  | Multi-grain SQL synthesis     |
| 6 | Native MCP Publishing    | PRAGMA mcp_publish_tool      | Direct MCP agent accessibility|
+---+--------------------------+------------------------------+-------------------------------+
```

#### Step 1: Install & Load Community Extensions
* **Action:** Executes `INSTALL ossie FROM community; LOAD ossie;` and `INSTALL duckdb_mcp FROM community; LOAD duckdb_mcp;`.
* **Why:** Verifies the pre-built community binaries for DuckDB v1.5.5 load successfully in a Linux container.

#### Step 2: Initialize Physical Tables for Dual Ontologies
* **Action:** Seeds in-memory DuckDB tables `fiware_accommodations` (6 rows) and `segittur_destinos` (4 rows) across Spanish tourist destinations (Madrid, Barcelona, Girona, Las Palmas).
* **Why:** Supplies physical columnar data for the semantic datasets to bind against.

#### Step 3: Parse and Validate Model (`ossie_load`)
* **Action:** Executes `CALL ossie_load('/app/ossie/duckdb_ossie_model.json')`.
* **Why:** Validates that DuckDB's C++ schema parser accepts our multi-dataset JSON definition with cross-ontology relationships and metric formulas.

#### Step 4: Metadata & Vocabulary Discovery
* **Action:** Queries `SELECT * FROM ossie_datasets()`, `ossie_fields()`, `ossie_metrics()`, and `ossie_relationships()`.
* **Why:** Proves that an AI agent or downstream system can dynamically introspect available entities, metrics (`total_bed_capacity`, `total_monthly_visitors`, `estimated_monthly_expenditure_eur`), and the foreign key relationship (`municipality_code` $\leftrightarrow$ `codigo_ine_municipio`) without hardcoding table structures.

#### Step 5: Multi-Grain Semantic Query Compilation & Execution
* **Action:** 
  - Calls `SELECT ossie_compile('total_bed_capacity', '["fiware_accommodations.municipality_code"]')` to inspect generated SQL.
  - Calls `SELECT * FROM ossie_query('total_bed_capacity', '["fiware_accommodations.municipality_code"]')` to execute the query.
  - Compiles and queries multi-metric calculations joining visitor counts and expenditure.
* **Why:** Demonstrates that DuckDB autonomously plans the `GROUP BY` and metric aggregations across dimensions.

#### Step 6: Native Model Context Protocol (MCP) Tool Publishing
* **Action:** Executes:
  ```sql
  PRAGMA mcp_publish_query('metrics', 'SELECT * FROM ossie_metrics()', 'Lists semantic metrics');
  PRAGMA mcp_publish_query('dimensions', 'SELECT * FROM ossie_fields()', 'Lists dimensions');
  ```
* **Why:** Proves that DuckDB can natively expose Ossie semantic catalog queries as MCP tools to LLMs without external Python web server middleware.

### 4.3 Running the Containerized Test

To run this evaluation in 100% containerized Docker isolation:

```bash
./run_duckdb_ossie_test.sh
```

For complete technical notes, differences with FastMCP, and version pinning considerations, see [DUCKDB_OSSIE_TEST.md](file:///Users/jsalvachua/OntoDeployTour/DUCKDB_OSSIE_TEST.md).


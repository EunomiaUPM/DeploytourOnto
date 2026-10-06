# DEPLOYTOUR: Testing Guide & Cross-Ontology Query Mechanics

This document provides a comprehensive technical walkthrough of how cross-ontology federation works in the **DEPLOYTOUR** Proof of Concept (PoC), how SQL queries bridge disparate conceptual schemas across Apache Iceberg lakehouses, and how the automated test suite validates the system.

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

## 2. The 5 Automated Test Scenarios

The test suite (`gemma_agent/test_cases.py` and `verifier/verify.py`) executes 5 distinct scenarios through the Gemma LLM Agent and MCP Server.

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
5. Executes all 5 Gemma agent test cases.

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

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
import re
import json
import yaml
import duckdb
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="DEPLOYTOUR MCP & DuckDB Query Engine",
    description="Cross-Ontology Federation Engine via Apache Ossie (OSI), DuckDB, and Model Context Protocol",
    version="1.1.0"
)

def resolve_dir(env_var: str, default_docker: str, relative_fallback: str) -> str:
    path = os.getenv(env_var, default_docker)
    if not os.path.exists(path):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        local_cand = os.path.join(base_dir, relative_fallback)
        if os.path.exists(local_cand):
            return local_cand
        if os.path.exists(relative_fallback):
            return os.path.abspath(relative_fallback)
    return path

OSSIE_DIR = resolve_dir("OSSIE_DIR", "/ossie", "ossie")
ENGINE_DIR = resolve_dir("ENGINE_DIR", "/engine", "engine")
DATA_DIR = resolve_dir("DATA_DIR", "/data", "data")

# Global DuckDB connection and state flags
_db_con: Optional[duckdb.DuckDBPyConnection] = None
_ossie_loaded: bool = False

DANGEROUS_SQL_PATTERNS = [
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|ATTACH|DETACH|COPY|EXPORT|IMPORT|PRAGMA|INSTALL|LOAD|CALL|VACUUM|CHECKPOINT|REINDEX)\b",
    r"\b(SYSTEM|SHELL|READ_TEXT|READ_BLOB|WRITE_CSV|WRITE_PARQUET)\b",
    r"\b(CREATE\s+(TABLE|SCHEMA|DATABASE|SECRET))\b"
]

def sanitize_sql_query(sql: str) -> Optional[str]:
    """
    Validates that a custom SQL statement is strictly read-only and safe.
    Returns None if valid, or an error message explaining why it was rejected.
    """
    if not sql or not sql.strip():
        return "Empty SQL statement."

    # Strip single line and multi-line comments
    clean = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL).strip()

    if not clean:
        return "Empty SQL statement after removing comments."

    # Prevent multi-statement attacks
    statements = [s.strip() for s in clean.split(";") if s.strip()]
    if len(statements) > 1:
        return "Security policy violation: Multi-statement queries are not allowed."

    # Must begin with SELECT or WITH
    if not re.match(r"^(SELECT|WITH)\b", clean, re.IGNORECASE):
        return "Security policy violation: Only read-only SELECT or WITH statements are permitted."

    # Check for forbidden mutation or system commands
    for pat in DANGEROUS_SQL_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return f"Security policy violation: Prohibited SQL operation detected matching rule '{pat}'."

    return None

def get_duckdb() -> duckdb.DuckDBPyConnection:
    global _db_con, _ossie_loaded
    if _db_con is None:
        _db_con = duckdb.connect()
        try:
            _db_con.execute("INSTALL iceberg; LOAD iceberg;")
        except Exception as e:
            print(f"[mcp-server] Warning loading iceberg extension: {e}")

        try:
            _db_con.execute("INSTALL spatial; LOAD spatial;")
        except Exception as e:
            print(f"[mcp-server] Warning loading spatial extension: {e}")

        # Try loading native Apache Ossie community extension
        try:
            _db_con.execute("INSTALL ossie FROM community; LOAD ossie;")
            _ossie_loaded = True
            print("[mcp-server] Community 'ossie' extension successfully loaded!")
        except Exception as e:
            _ossie_loaded = False
            print(f"[mcp-server] Notice: community 'ossie' extension not available in this environment ({e}). Falling back to declarative YAML specifications.")

        reload_views()
    return _db_con

def reload_views():
    global _ossie_loaded
    con = _db_con or duckdb.connect()
    meta_a = os.path.join(DATA_DIR, "lakehouse_a_fiware/metadata/v1.metadata.json")
    meta_b = os.path.join(DATA_DIR, "lakehouse_b_segittur/metadata/v1.metadata.json")

    has_a = os.path.exists(meta_a)
    has_b = os.path.exists(meta_b)

    if has_a:
        con.execute(f"CREATE OR REPLACE VIEW fiware_lake AS SELECT * FROM iceberg_scan('{meta_a}')")
        con.execute(f"CREATE OR REPLACE VIEW fiware_accommodations AS SELECT * FROM fiware_lake")
    else:
        con.execute("""
        CREATE TABLE IF NOT EXISTS fiware_accommodations (
            id VARCHAR PRIMARY KEY,
            name VARCHAR,
            category VARCHAR,
            capacity_beds INTEGER,
            occupancy_rate DOUBLE,
            latitude DOUBLE,
            longitude DOUBLE,
            municipality_code VARCHAR
        );
        INSERT OR IGNORE INTO fiware_accommodations VALUES
            ('acc-001', 'Gran Hotel Madrid', 'Hotel', 450, 0.85, 40.4168, -3.7038, '28079'),
            ('acc-002', 'Madrid Central Suites', 'Apartment', 120, 0.70, 40.4180, -3.7010, '28079'),
            ('acc-003', 'Hotel Arts Barcelona', 'Hotel', 380, 0.90, 41.3851, 2.1734, '08019'),
            ('acc-004', 'Hostal Ramblas', 'Hostal', 80, 0.65, 41.3879, 2.1699, '08019'),
            ('acc-005', 'Camping Costa Brava', 'Camping', 250, 0.50, 41.9794, 2.8214, '17079'),
            ('acc-006', 'Hostal Canteras Beach', 'Hostal', 172, 0.95, 28.1235, -15.4363, '35016');
        CREATE OR REPLACE VIEW fiware_lake AS SELECT * FROM fiware_accommodations;
        """)

    if has_b:
        con.execute(f"CREATE OR REPLACE VIEW segittur_lake AS SELECT * FROM iceberg_scan('{meta_b}')")
        con.execute(f"CREATE OR REPLACE VIEW segittur_destinos AS SELECT * FROM segittur_lake")
    else:
        con.execute("""
        CREATE TABLE IF NOT EXISTS segittur_destinos (
            id_destino VARCHAR PRIMARY KEY,
            denominacion_recurso VARCHAR,
            tipo_espacio VARCHAR,
            visitantes_mensuales INTEGER,
            gasto_medio_diario_eur DOUBLE,
            latitud DOUBLE,
            longitud DOUBLE,
            codigo_ine_municipio VARCHAR
        );
        INSERT OR IGNORE INTO segittur_destinos VALUES
            ('dest-001', 'Museo del Prado', 'RecursoCultural', 450000, 145.50, 40.4170, -3.7040, '28079'),
            ('dest-002', 'Sagrada Familia', 'RecursoCultural', 580000, 160.00, 41.3855, 2.1740, '08019'),
            ('dest-003', 'Parc Natural de la Zona Volcanica', 'EspacioNatural', 85000, 95.00, 41.9800, 2.8220, '17079'),
            ('dest-004', 'Catedral de Santa Ana', 'RecursoCultural', 115262, 166.09, 28.1240, -15.4370, '35016');
        CREATE OR REPLACE VIEW segittur_lake AS SELECT * FROM segittur_destinos;
        """)

    # Load Ossie semantic model if ossie extension is available
    if _ossie_loaded:
        model_file = os.path.join(OSSIE_DIR, "duckdb_ossie_model.json")
        if os.path.exists(model_file):
            try:
                con.execute(f"CALL ossie_load('{model_file}');")
                print(f"[mcp-server] Apache Ossie semantic model loaded from {model_file}!")
            except Exception as e:
                print(f"[mcp-server] Warning loading Ossie model: {e}")

# Tool Functions
def tool_list_semantic_entities() -> Dict[str, Any]:
    datasets_file = os.path.join(OSSIE_DIR, "datasets.yaml")
    metrics_file = os.path.join(OSSIE_DIR, "metrics.yaml")

    datasets = {}
    metrics = {}
    if os.path.exists(datasets_file):
        with open(datasets_file, "r") as f:
            datasets = yaml.safe_load(f)
    if os.path.exists(metrics_file):
        with open(metrics_file, "r") as f:
            metrics = yaml.safe_load(f)

    # If native duckdb-ossie extension is active, enrich with model discovery
    con = get_duckdb()
    native_discovery: Dict[str, Any] = {}
    if _ossie_loaded:
        try:
            d_rows = con.execute("SELECT name, source FROM ossie_datasets()").fetchall()
            m_rows = con.execute("SELECT name, datatype, description FROM ossie_metrics()").fetchall()
            r_rows = con.execute("SELECT name, from_dataset, to_dataset, from_columns, to_columns FROM ossie_relationships()").fetchall()
            native_discovery = {
                "native_datasets": [{"name": r[0], "source": r[1]} for r in d_rows],
                "native_metrics": [{"name": r[0], "datatype": r[1], "description": r[2]} for r in m_rows],
                "native_relationships": [{"name": r[0], "from": r[1], "to": r[2], "from_cols": r[3], "to_cols": r[4]} for r in r_rows]
            }
        except Exception:
            pass

    return {
        "spec": "Apache-Ossie-OSI/v1",
        "datasets": datasets.get("datasets", []),
        "metrics": metrics.get("metrics", []),
        "native_engine_discovery": native_discovery
    }

def tool_get_ontology_mappings() -> Dict[str, Any]:
    mappings_file = os.path.join(OSSIE_DIR, "mappings.yaml")
    mappings = {}
    if os.path.exists(mappings_file):
        with open(mappings_file, "r") as f:
            mappings = yaml.safe_load(f)
    return mappings.get("mappings", mappings)

def tool_execute_federated_query() -> Dict[str, Any]:
    reload_views()
    con = get_duckdb()

    query = """
    SELECT 
        f.municipality_code,
        f.category AS fiware_category,
        s.tipo_espacio AS segittur_category,
        COUNT(DISTINCT f.id) AS accommodation_count,
        SUM(f.capacity_beds) AS total_bed_capacity,
        ROUND(SUM(f.capacity_beds * f.occupancy_rate), 1) AS estimated_active_guests,
        SUM(s.visitantes_mensuales) AS monthly_visitor_footfall,
        ROUND(SUM(s.visitantes_mensuales * s.gasto_medio_diario_eur), 2) AS estimated_monthly_spend_eur,
        ROUND(CAST(SUM(s.visitantes_mensuales) AS DOUBLE) / NULLIF(SUM(f.capacity_beds) * 30.0, 0), 2) AS tourism_pressure_index
    FROM fiware_lake f
    JOIN segittur_lake s 
      ON f.municipality_code = s.codigo_ine_municipio
     AND (
         (f.category = 'Hotel' AND s.tipo_espacio = 'AlojamientoHotelero') OR
         (f.category = 'Camping' AND s.tipo_espacio = 'ZonaAcampada') OR
         (s.tipo_espacio IN ('RecursoCultural', 'EspacioNatural'))
     )
    GROUP BY f.municipality_code, f.category, s.tipo_espacio
    ORDER BY tourism_pressure_index DESC;
    """

    df = con.execute(query).fetchall()
    cols = [
        "municipality_code",
        "fiware_category",
        "segittur_category",
        "accommodation_count",
        "total_bed_capacity",
        "estimated_active_guests",
        "monthly_visitor_footfall",
        "estimated_monthly_spend_eur",
        "tourism_pressure_index"
    ]
    rows = [dict(zip(cols, row)) for row in df]
    return {
        "status": "success",
        "row_count": len(rows),
        "results": rows
    }

def tool_run_custom_duckdb_sql(sql: str) -> Dict[str, Any]:
    # Security sanitization check
    err = sanitize_sql_query(sql)
    if err:
        return {
            "status": "error",
            "error": err
        }

    reload_views()
    con = get_duckdb()
    try:
        cur = con.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows_tuples = cur.fetchall()
        rows = [dict(zip(cols, r)) for r in rows_tuples]
        return {
            "status": "success",
            "columns": cols,
            "row_count": len(rows),
            "results": rows
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def tool_compile_semantic_query(metrics: List[str], dimensions: List[str], filters: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compiles a semantic query into optimized ANSI SQL using Apache Ossie."""
    con = get_duckdb()
    filters = filters or []
    if not _ossie_loaded:
        return {
            "status": "error",
            "error": "Native duckdb-ossie extension is not loaded in this runtime."
        }
    try:
        sql = con.execute("SELECT ossie_compile(?, ?, ?)", [metrics, dimensions, filters]).fetchone()[0]
        return {
            "status": "success",
            "metrics": metrics,
            "dimensions": dimensions,
            "filters": filters,
            "compiled_sql": sql.strip()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def tool_execute_semantic_query(metrics: List[str], dimensions: List[str], filters: Optional[List[str]] = None) -> Dict[str, Any]:
    """Executes a semantic query directly via ossie_query."""
    con = get_duckdb()
    filters = filters or []
    if not _ossie_loaded:
        return {
            "status": "error",
            "error": "Native duckdb-ossie extension is not loaded in this runtime."
        }
    try:
        cur = con.execute("SELECT * FROM ossie_query(?, ?, ?)", [metrics, dimensions, filters])
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {
            "status": "success",
            "metrics": metrics,
            "dimensions": dimensions,
            "row_count": len(rows),
            "results": rows
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def tool_execute_spatial_proximity_query(
    municipality_code: Optional[str] = None,
    max_distance_km: float = 10.0,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Computes spatial geodesic distances between lodging establishments (FIWARE)
    and tourist POIs / resources (SEGITTUR) using DuckDB's spatial ST_Distance_Spheroid.
    """
    reload_views()
    con = get_duckdb()

    where_clauses = ["f.latitude IS NOT NULL", "s.latitud IS NOT NULL"]
    params: List[Any] = []

    if municipality_code:
        where_clauses.append("f.municipality_code = ?")
        params.append(str(municipality_code))

    where_str = " AND ".join(where_clauses)
    max_meters = max_distance_km * 1000.0

    sql = f"""
    SELECT 
        f.id AS accommodation_id,
        f.name AS accommodation_name,
        f.category AS accommodation_category,
        f.municipality_code,
        f.capacity_beds,
        s.id_destino,
        s.denominacion_recurso,
        s.tipo_espacio,
        s.visitantes_mensuales,
        ROUND(ST_Distance_Spheroid(
            ST_Point(f.longitude, f.latitude),
            ST_Point(s.longitud, s.latitud)
        ) / 1000.0, 2) AS distance_km
    FROM fiware_lake f
    JOIN segittur_lake s ON f.municipality_code = s.codigo_ine_municipio
    WHERE {where_str}
      AND ST_Distance_Spheroid(
            ST_Point(f.longitude, f.latitude),
            ST_Point(s.longitud, s.latitud)
          ) <= {max_meters}
    ORDER BY distance_km ASC
    LIMIT {int(limit)};
    """

    try:
        cur = con.execute(sql, params) if params else con.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {
            "status": "success",
            "max_distance_km": max_distance_km,
            "row_count": len(rows),
            "results": rows
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def tool_execute_temporal_pressure_query(municipality_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulates seasonal tourism pressure shifts across four seasons (Winter, Spring, Summer, Autumn)
    reflecting Spanish tourism dynamics (peak summer coastal/cultural rush vs winter off-peak).
    """
    reload_views()
    con = get_duckdb()

    where_filter = f"WHERE f.municipality_code = '{municipality_code}'" if municipality_code else ""

    sql = f"""
    WITH base AS (
        SELECT 
            f.municipality_code,
            COUNT(DISTINCT f.id) AS accommodations,
            SUM(f.capacity_beds) AS bed_capacity,
            SUM(s.visitantes_mensuales) AS monthly_visitors,
            AVG(s.gasto_medio_diario_eur) AS avg_spend_eur
        FROM fiware_lake f
        JOIN segittur_lake s ON f.municipality_code = s.codigo_ine_municipio
        {where_filter}
        GROUP BY f.municipality_code
    )
    SELECT 
        municipality_code,
        bed_capacity,
        monthly_visitors AS baseline_monthly_visitors,
        ROUND(CAST(monthly_visitors * 0.65 AS DOUBLE) / NULLIF(bed_capacity * 30.0, 0), 2) AS winter_pressure_index,
        ROUND(CAST(monthly_visitors * 1.05 AS DOUBLE) / NULLIF(bed_capacity * 30.0, 0), 2) AS spring_pressure_index,
        ROUND(CAST(monthly_visitors * 1.55 AS DOUBLE) / NULLIF(bed_capacity * 30.0, 0), 2) AS summer_peak_pressure_index,
        ROUND(CAST(monthly_visitors * 0.85 AS DOUBLE) / NULLIF(bed_capacity * 30.0, 0), 2) AS autumn_pressure_index,
        ROUND((monthly_visitors * 1.55 - monthly_visitors * 0.65) / NULLIF(bed_capacity * 30.0, 0), 2) AS seasonal_variance_swing
    FROM base
    ORDER BY summer_peak_pressure_index DESC;
    """

    try:
        cur = con.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {
            "status": "success",
            "municipality_filter": municipality_code,
            "row_count": len(rows),
            "results": rows
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Models for REST & JSON-RPC
class CustomSqlRequest(BaseModel):
    query: str

class SemanticQueryRequest(BaseModel):
    metrics: List[str]
    dimensions: List[str]
    filters: Optional[List[str]] = Field(default_factory=list)

class SpatialProximityRequest(BaseModel):
    municipality_code: Optional[str] = None
    max_distance_km: float = 10.0
    limit: int = 50

class TemporalPressureRequest(BaseModel):
    municipality_code: Optional[str] = None

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

# REST Tool Endpoints
@app.get("/health")
def health():
    get_duckdb()
    return {
        "status": "ok",
        "service": "mcp-server",
        "native_ossie_loaded": _ossie_loaded
    }

@app.get("/tools/list_semantic_entities")
def get_semantic_entities():
    return tool_list_semantic_entities()

@app.get("/tools/get_ontology_mappings")
def get_mappings():
    return tool_get_ontology_mappings()

@app.get("/tools/execute_federated_query")
@app.post("/tools/execute_federated_query")
def execute_query():
    return tool_execute_federated_query()

@app.post("/tools/run_custom_duckdb_sql")
def run_custom_sql(req: CustomSqlRequest):
    return tool_run_custom_duckdb_sql(req.query)

@app.post("/tools/compile_semantic_query")
def compile_semantic(req: SemanticQueryRequest):
    return tool_compile_semantic_query(req.metrics, req.dimensions, req.filters)

@app.post("/tools/execute_semantic_query")
def execute_semantic(req: SemanticQueryRequest):
    return tool_execute_semantic_query(req.metrics, req.dimensions, req.filters)

@app.get("/tools/execute_spatial_proximity_query")
@app.post("/tools/execute_spatial_proximity_query")
def execute_spatial(
    municipality_code: Optional[str] = None,
    max_distance_km: float = 10.0,
    limit: int = 50
):
    return tool_execute_spatial_proximity_query(municipality_code, max_distance_km, limit)

@app.get("/tools/execute_temporal_pressure_query")
@app.post("/tools/execute_temporal_pressure_query")
def execute_temporal(municipality_code: Optional[str] = None):
    return tool_execute_temporal_pressure_query(municipality_code)

# Standard MCP JSON-RPC Protocol endpoint
@app.post("/mcp")
def mcp_jsonrpc(req: JsonRpcRequest):
    method = req.method
    params = req.params or {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "tools": [
                    {
                        "name": "list_semantic_entities",
                        "description": "Returns registered entities, datasets, metrics, and relationships from Apache Ossie.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "get_ontology_mappings",
                        "description": "Returns FIWARE Smart Data Models <-> SEGITTUR cross-ontology alignment mappings and join keys.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "execute_federated_query",
                        "description": "Executes cross-ontology Query Over Everything federated join across both Iceberg lakehouses in DuckDB.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "run_custom_duckdb_sql",
                        "description": "Executes sanitized read-only SQL against fiware_lake and segittur_lake Iceberg views in DuckDB.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Read-only SQL query (SELECT or WITH) to execute"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "compile_semantic_query",
                        "description": "Compiles high-level Ossie metrics and dimensions into ANSI SQL via duckdb-ossie.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "metrics": {"type": "array", "items": {"type": "string"}},
                                "dimensions": {"type": "array", "items": {"type": "string"}},
                                "filters": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["metrics", "dimensions"]
                        }
                    },
                    {
                        "name": "execute_semantic_query",
                        "description": "Executes semantic query directly over declared Ossie datasets and grain relationships.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "metrics": {"type": "array", "items": {"type": "string"}},
                                "dimensions": {"type": "array", "items": {"type": "string"}},
                                "filters": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["metrics", "dimensions"]
                        }
                    },
                    {
                        "name": "execute_spatial_proximity_query",
                        "description": "Performs spatial distance join (ST_Distance_Spheroid) between accommodations and POIs.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "municipality_code": {"type": "string"},
                                "max_distance_km": {"type": "number", "default": 10.0},
                                "limit": {"type": "integer", "default": 50}
                            }
                        }
                    },
                    {
                        "name": "execute_temporal_pressure_query",
                        "description": "Calculates seasonal quarterly tourism pressure variations (Winter, Spring, Summer peak, Autumn).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "municipality_code": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "list_semantic_entities":
            res = tool_list_semantic_entities()
        elif tool_name == "get_ontology_mappings":
            res = tool_get_ontology_mappings()
        elif tool_name == "execute_federated_query":
            res = tool_execute_federated_query()
        elif tool_name == "run_custom_duckdb_sql":
            res = tool_run_custom_duckdb_sql(args.get("query", ""))
        elif tool_name == "compile_semantic_query":
            res = tool_compile_semantic_query(args.get("metrics", []), args.get("dimensions", []), args.get("filters", []))
        elif tool_name == "execute_semantic_query":
            res = tool_execute_semantic_query(args.get("metrics", []), args.get("dimensions", []), args.get("filters", []))
        elif tool_name == "execute_spatial_proximity_query":
            res = tool_execute_spatial_proximity_query(
                args.get("municipality_code"),
                args.get("max_distance_km", 10.0),
                args.get("limit", 50)
            )
        elif tool_name == "execute_temporal_pressure_query":
            res = tool_execute_temporal_pressure_query(args.get("municipality_code"))
        else:
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32601, "message": f"Method {tool_name} not found"}
            }

        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }
                ]
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Method {method} not supported"}
        }

# SSE endpoint for MCP
@app.get("/sse")
async def sse_endpoint(request: Request):
    async def event_generator():
        yield f"event: endpoint\ndata: /mcp\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

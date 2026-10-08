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
import json
import yaml
import duckdb
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="DEPLOYTOUR MCP & DuckDB Query Engine",
    description="Cross-Ontology Federation Engine via Apache Ossie (OSI), DuckDB, and Model Context Protocol",
    version="1.0.0"
)

OSSIE_DIR = os.getenv("OSSIE_DIR", "/ossie")
ENGINE_DIR = os.getenv("ENGINE_DIR", "/engine")
DATA_DIR = os.getenv("DATA_DIR", "/data")

# Global DuckDB connection
_db_con: Optional[duckdb.DuckDBPyConnection] = None

def get_duckdb() -> duckdb.DuckDBPyConnection:
    global _db_con
    if _db_con is None:
        _db_con = duckdb.connect()
        _db_con.execute("INSTALL iceberg; LOAD iceberg;")
        _db_con.execute("INSTALL spatial; LOAD spatial;")
        
        # Verify and create views
        meta_a = os.path.join(DATA_DIR, "lakehouse_a_fiware/metadata/v1.metadata.json")
        meta_b = os.path.join(DATA_DIR, "lakehouse_b_segittur/metadata/v1.metadata.json")
        
        if os.path.exists(meta_a):
            _db_con.execute(f"CREATE OR REPLACE VIEW fiware_lake AS SELECT * FROM iceberg_scan('{meta_a}')")
        if os.path.exists(meta_b):
            _db_con.execute(f"CREATE OR REPLACE VIEW segittur_lake AS SELECT * FROM iceberg_scan('{meta_b}')")
    return _db_con

def reload_views():
    con = get_duckdb()
    meta_a = os.path.join(DATA_DIR, "lakehouse_a_fiware/metadata/v1.metadata.json")
    meta_b = os.path.join(DATA_DIR, "lakehouse_b_segittur/metadata/v1.metadata.json")
    if os.path.exists(meta_a):
        con.execute(f"CREATE OR REPLACE VIEW fiware_lake AS SELECT * FROM iceberg_scan('{meta_a}')")
    if os.path.exists(meta_b):
        con.execute(f"CREATE OR REPLACE VIEW segittur_lake AS SELECT * FROM iceberg_scan('{meta_b}')")

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
            
    return {
        "spec": "Apache-Ossie-OSI/v1",
        "datasets": datasets.get("datasets", []),
        "metrics": metrics.get("metrics", [])
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

# Models for REST & JSON-RPC
class CustomSqlRequest(BaseModel):
    query: str

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

# REST Tool Endpoints
@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp-server"}

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
                        "description": "Returns registered entities and metric dimensions from Apache Ossie specifications.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "get_ontology_mappings",
                        "description": "Returns FIWARE Smart Data Models <-> SEGITTUR cross-ontology alignment mappings.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "execute_federated_query",
                        "description": "Executes cross-ontology Query Over Everything federated join across both Iceberg lakehouses in DuckDB.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "run_custom_duckdb_sql",
                        "description": "Executes custom SQL against fiware_lake and segittur_lake Iceberg views in DuckDB.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "SQL query to execute"}
                            },
                            "required": ["query"]
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

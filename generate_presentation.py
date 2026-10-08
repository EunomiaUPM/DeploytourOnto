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
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="DEPLOYTOUR_PoC_Architecture_and_Testing.pptx"):
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    C_NAVY = RGBColor(15, 23, 42)       # Slate 900
    C_BLUE = RGBColor(30, 58, 138)      # Blue 900
    C_SKY = RGBColor(14, 165, 233)      # Sky 500
    C_EMERALD = RGBColor(16, 185, 129)  # Emerald 500
    C_BG_CARD = RGBColor(248, 250, 252) # Slate 50
    C_BORDER = RGBColor(226, 232, 240)  # Slate 200
    C_TEXT = RGBColor(30, 41, 59)       # Slate 800
    C_MUTED = RGBColor(100, 116, 139)   # Slate 500
    C_WHITE = RGBColor(255, 255, 255)

    def add_header(slide, title_text, category_text="DEPLOYTOUR ARCHITECTURE & TESTING"):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_SKY

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = C_NAVY

        # Subtle bottom line under header
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = C_BORDER
        line.line.color.rgb = C_BORDER

    def add_card(slide, left, top, width, height, title, items, badge="", border_color=C_BORDER, bg_color=C_BG_CARD):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(height - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        # Card Title
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = C_BLUE

        if badge:
            p_badge = tf.add_paragraph()
            p_badge.text = f"[{badge}]"
            p_badge.font.size = Pt(10)
            p_badge.font.bold = True
            p_badge.font.color.rgb = C_SKY

        for item in items:
            p = tf.add_paragraph()
            p.space_before = Pt(6)
            p.font.size = Pt(11.5)
            p.font.color.rgb = C_TEXT
            if isinstance(item, tuple):
                p.text = f"• {item[0]}: "
                p.font.bold = True
                run = p.add_run()
                run.text = item[1]
                run.font.bold = False
            else:
                p.text = f"• {item}"

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_NAVY
    bg1.line.color.rgb = C_NAVY

    # Decorative banner
    accent1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1.8), Inches(0.15), Inches(3.8))
    accent1.fill.solid()
    accent1.fill.fore_color.rgb = C_SKY
    accent1.line.color.rgb = C_SKY

    tb1 = s1.shapes.add_textbox(Inches(1.4), Inches(1.7), Inches(10.5), Inches(4.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "DEPLOYTOUR"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    p = tf1.add_paragraph()
    p.text = "Cross-Ontology Federation via Apache Ossie, Apache Gravitino, DuckDB & MCP"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = C_SKY
    p.space_before = Pt(8)

    p = tf1.add_paragraph()
    p.text = "Bridging Spanish Tourism Ontologies (FIWARE Smart Data Models ↔ SEGITTUR / Schema.org) with Autonomous Google Gemma LLM Intelligence"
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_before = Pt(14)

    p = tf1.add_paragraph()
    p.text = "100% Fully Containerized Proof of Concept | Local Filesystem Architecture"
    p.font.size = Pt(12)
    p.font.color.rgb = C_EMERALD
    p.font.bold = True
    p.space_before = Pt(24)

    # =========================================================================
    # SLIDE 2: Executive Summary & Core Objectives
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Executive Summary & Core Project Objectives", "Strategic Overview")

    add_card(s2, 0.8, 1.8, 3.6, 5.0, "1. Zero-ETL Federation", [
        ("Core Problem", "Data resides in isolated lakes under conflicting semantics without unified schemas."),
        ("Solution", "Query across independent Apache Iceberg lakes without data movement or transformation pipelines."),
        ("Key Value", "Preserves autonomy of regional platforms while enabling macro-level analytics.")
    ], badge="Architecture")

    add_card(s2, 4.8, 1.8, 3.6, 5.0, "2. Standards-Based Stack", [
        ("Lakehouse Format", "Apache Iceberg table format with strict schema/snapshot management."),
        ("Catalog Governance", "Apache Gravitino metalake federating dual REST catalogs."),
        ("Semantic Layer", "Apache Ossie (OSI) declarative entities, mappings, and metrics."),
        ("Engine", "In-process vector execution via DuckDB with native extensions.")
    ], badge="Open Source")

    add_card(s2, 8.8, 1.8, 3.6, 5.0, "3. LLM & Agent Access", [
        ("Standard Interface", "Model Context Protocol (MCP) exposing tools over JSON-RPC & REST."),
        ("Reasoning Agent", "Google Gemma LLM with Gemma-2 turn templates and function calling."),
        ("Autonomous Insights", "Translates natural language questions directly into federated joins.")
    ], badge="Intelligence")

    # =========================================================================
    # SLIDE 3: The Interoperability Challenge
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "The Semantic Divergence Challenge in Tourism", "Domain Problem")

    add_card(s3, 0.8, 1.8, 5.6, 5.0, "Lakehouse A: FIWARE Smart Data Models", [
        ("Domain Focus", "Physical lodging infrastructure, capacity, and accommodations."),
        ("Entities", "TouristDestination, Accommodation."),
        ("Spatial Key", "municipality_code (5-digit INE code, e.g., '17079')."),
        ("Taxonomy", "English classifications: Hotel, Hostal, Apartment, Camping."),
        ("Supply Metrics", "capacity_beds, occupancy_rate, active guests."),
        ("Limitation", "Has accommodation supply, but ZERO data on visitor footfall or daily spend.")
    ], badge="Supply-Side Semantics")

    add_card(s3, 6.8, 1.8, 5.6, 5.0, "Lakehouse B: SEGITTUR / Schema.org", [
        ("Domain Focus", "Points of interest, tourism demand, footfall, and economy."),
        ("Entities", "PuntoDeInteresTuristico, DestinoTuristicoFlujo."),
        ("Spatial Key", "codigo_ine_municipio (5-digit INE code)."),
        ("Taxonomy", "Spanish classifications: AlojamientoHotelero, RecursoCultural, EspacioNatural, ZonaAcampada."),
        ("Demand Metrics", "visitantes_mensuales, gasto_medio_diario_eur."),
        ("Limitation", "Tracks tourism demand and spend, but has NO data on local bed capacity.")
    ], badge="Demand-Side Semantics")

    # =========================================================================
    # SLIDE 4: 5-Tier Architecture Topology
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "DEPLOYTOUR: 5-Tier Containerized Architecture", "System Topology")

    tiers = [
        ("1. Storage & Ingestion", "Docker shared volume /data. Go parquet-go + PyIceberg generates v1.metadata.json & parquet files.", 0.8),
        ("2. Catalog Governance", "Apache Gravitino (8090) metalake managing dual Iceberg REST catalogs (fiware & segittur).", 3.2),
        ("3. Semantic Layer (OSI)", "Apache Ossie datasets.yaml, mappings.yaml, and metrics.yaml formalizing joins.", 5.6),
        ("4. Execution & MCP Server", "DuckDB iceberg_scan views + FastAPI/FastMCP server (8000) exposing JSON-RPC tools.", 8.0),
        ("5. Intelligence & Agent", "Gemma LLM Agent with Gemma-2 prompt template, interactive CLI & automated test suite.", 10.4),
    ]

    for title, desc, left in tiers:
        add_card(s4, left, 1.8, 2.1, 5.0, title, [desc], badge="Tier")

    # =========================================================================
    # SLIDE 5: Storage & Ingestion: Apache Iceberg
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Storage & Ingestion: Zero-Cloud Local Iceberg", "Data Pipeline")

    add_card(s5, 0.8, 1.8, 5.6, 5.0, "Synthetic Data Generation (Go)", [
        ("Engine", "High-performance Go service using parquet-go."),
        ("Coverage", "Spanish tourism destinations with realistic coordinates & INE codes (Madrid, Barcelona, Girona, etc.)."),
        ("Row Count", ">= 50 rows per ontology (produces 73 joined records)."),
        ("Format", "Columnar Apache Parquet with Snappy compression.")
    ], badge="Ingestion")

    add_card(s5, 6.8, 1.8, 5.6, 5.0, "Iceberg Metadata Bridge (PyIceberg)", [
        ("DuckDB Compatibility", "DuckDB C++ Iceberg extension requires strict Avro manifests & metadata."),
        ("Bridge Role", "pyiceberg creates compliant v1.metadata.json, manifest-list, and snapshot manifests."),
        ("Zero S3/MinIO", "Operates entirely on local file:// storage mounts without external cloud object store daemons."),
        ("Idempotence", "Guaranteed safe execution across container volume restarts.")
    ], badge="Metadata")

    # =========================================================================
    # SLIDE 6: Catalog Governance: Apache Gravitino
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Catalog Governance: Apache Gravitino Metalake", "Metadata Governance")

    add_card(s6, 0.8, 1.8, 5.6, 5.0, "Unified Metalake Architecture", [
        ("Service", "Apache Gravitino 0.5.1 server running on port 8090."),
        ("Metalake", "deploytour_metalake registered as root catalog namespace."),
        ("Dual Catalogs", "fiware_catalog (Lakehouse A) & segittur_catalog (Lakehouse B)."),
        ("Storage Backend", "Filesystem-backed Iceberg catalog provider.")
    ], badge="Catalog Management")

    add_card(s6, 6.8, 1.8, 5.6, 5.0, "Automated Bootstrap via REST API", [
        ("Bootstrap Container", "gravitino-init (curlimages/curl)."),
        ("API Probing", "Polls Gravitino health at http://gravitino:8090/api/version."),
        ("Automated Registration", "Executes REST POST to /api/v1/metalakes and registers both catalogs."),
        ("Health Signalling", "Signals completion via Docker healthcheck probe.")
    ], badge="Orchestration")

    # =========================================================================
    # SLIDE 7: Semantic Layer: Apache Ossie (OSI)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Semantic Interoperability: Apache Ossie (OSI)", "Ontological Alignment")

    add_card(s7, 0.8, 1.8, 3.6, 5.0, "1. datasets.yaml", [
        ("Physical Schema", "Defines fiware_accommodations & segittur_destinos."),
        ("Semantic Types", "Associates raw columns with abstract semantic dimensions (MunicipalityCode, Category, Capacity).")
    ], badge="Schema Discovery")

    add_card(s7, 4.8, 1.8, 3.6, 5.0, "2. mappings.yaml", [
        ("Key Alignment", "municipality_code <=> codigo_ine_municipio."),
        ("Taxonomy Map", "Hotel <=> AlojamientoHotelero"),
        ("Taxonomy Map", "Camping <=> ZonaAcampada"),
        ("Taxonomy Map", "Hostal <=> AlojamientoHotelero"),
        ("Taxonomy Map", "Apartment <=> AlojamientoHotelero")
    ], badge="Cross-Ontology Map")

    add_card(s7, 8.8, 1.8, 3.6, 5.0, "3. metrics.yaml", [
        ("TourismPressureIndex", "Monthly Footfall / (Bed Capacity * 30)."),
        ("EffectiveGuests", "capacity_beds * occupancy_rate."),
        ("MonthlySpend", "visitantes_mensuales * gasto_medio_diario.")
    ], badge="Derived Metrics")

    # =========================================================================
    # SLIDE 8: Execution Engine: DuckDB Cross-Ontology SQL
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Query Over Everything: DuckDB Federated Execution", "SQL Engine")

    add_card(s8, 0.8, 1.8, 5.6, 5.0, "DuckDB Native Iceberg Scanning", [
        ("Extensions", "Loads iceberg and spatial extensions dynamically."),
        ("Zero-Copy Views", "CREATE VIEW fiware_lake AS SELECT * FROM iceberg_scan('/data/lakehouse_a_fiware');"),
        ("Performance", "Vectorized in-memory execution scanning local parquet directly through Iceberg metadata manifests.")
    ], badge="Vectorized Engine")

    add_card(s8, 6.8, 1.8, 5.6, 5.0, "Cross-Ontology Join Logic", [
        ("Spatial Equivalence", "f.municipality_code = s.codigo_ine_municipio"),
        ("Taxonomic Equivalence", "Evaluates cross-ontology accommodation classifications defined in Ossie."),
        ("Aggregated Results", "Computes total beds, active guests, monthly spend, and tourism pressure index."),
        ("Output Size", "Yields 73 cleanly federated destination-accommodation records.")
    ], badge="Federated Join")

    # =========================================================================
    # SLIDE 9: Model Context Protocol (MCP) Server
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Model Context Protocol (MCP) Server Interface", "Standardized API")

    add_card(s9, 0.8, 1.8, 5.6, 5.0, "Standardized Protocols & Endpoints", [
        ("Framework", "FastAPI + FastMCP listening on port 8000."),
        ("JSON-RPC 2.0", "Endpoint /mcp compliant with standard Anthropic / open MCP specification."),
        ("REST Tool Invocation", "Direct GET/POST endpoints at /tools/{name}."),
        ("Streaming", "Server-Sent Events (SSE) support for streaming observations.")
    ], badge="Server Architecture")

    add_card(s9, 6.8, 1.8, 5.6, 5.0, "Exposed Analytical MCP Tools", [
        ("list_semantic_entities", "Returns Ossie datasets, entities, and defined metrics."),
        ("get_ontology_mappings", "Returns FIWARE <-> SEGITTUR translation dictionary and join keys."),
        ("execute_federated_query", "Executes the cross-ontology join in DuckDB returning structured rows."),
        ("run_custom_duckdb_sql", "Executes targeted custom SQL queries against the federated Iceberg views.")
    ], badge="MCP Tools")

    # =========================================================================
    # SLIDE 10: Intelligence Tier: Google Gemma LLM Agent
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Intelligence Tier: Google Gemma LLM Agent", "Autonomous Reasoner")

    add_card(s10, 0.8, 1.8, 5.6, 5.0, "Gemma-2 Prompt Engineering", [
        ("Template", "<start_of_turn>user ... <end_of_turn> <start_of_turn>model thought ..."),
        ("Function Calling", "Formulates explicit tool call blocks: ```call:tool_name {args}```"),
        ("Synthesis", "Transforms raw tabular DuckDB observations into structured executive reports with Markdown tables.")
    ], badge="Prompt Format")

    add_card(s10, 6.8, 1.8, 5.6, 5.0, "Zero-Dependency & External LLM Pluggability", [
        ("Autonomous Engine", "Embedded reasoning engine operates completely offline without downloading 5GB models."),
        ("Ollama / vLLM Ready", "Easily connected to real external Gemma models via LLM_BASE_URL (e.g. ollama run gemma:2b)."),
        ("CLI Interface", "Supports both one-shot commands and interactive REPL sessions.")
    ], badge="Flexibility")

    # =========================================================================
    # SLIDE 11: Verification & Testing: 5 Scenarios
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Validation Suite: 5 Real-World Semantic Test Scenarios", "Test Engineering")

    scenarios = [
        ("1. Schema Discovery", "list_semantic_entities", "Discovers fiware_accommodations, segittur_destinos, and metrics.", 0.8),
        ("2. Mapping Resolution", "get_ontology_mappings", "Validates join keys and taxonomy equivalence rules.", 3.2),
        ("3. Tourism Pressure", "execute_federated_query", "73 rows federated; identifies Las Palmas (35016) index 22.34.", 5.6),
        ("4. City Comparison", "run_custom_duckdb_sql", "Targeted query comparing Girona (17079) and Barcelona (08019).", 8.0),
        ("5. Overcapacity Scan", "run_custom_duckdb_sql", "Detects extreme overcapacity anomalies where visitors > 50x beds.", 10.4),
    ]

    for title, tool, desc, left in scenarios:
        add_card(s11, left, 1.8, 2.1, 5.0, title, [f"Tool: {tool}", desc], badge="Verified", border_color=C_EMERALD)

    # =========================================================================
    # SLIDE 12: Native Apache Ossie Extension: duckdb-ossie Evaluation
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Native Apache Ossie Extension: duckdb-ossie Evaluation", "Community Extension")

    add_card(s12, 0.8, 1.8, 3.6, 5.0, "C++ In-Engine Semantic Core", [
        ("Iqea duckdb-ossie", "Official community extension ('INSTALL ossie FROM community;')."),
        ("Embedded Execution", "Declarative Apache Ossie models parsed and evaluated directly in DuckDB core."),
        ("Schema Validation", "CALL ossie_load validates JSON models (v0.2.0.dev0) and entity dimensions."),
        ("Catalog Introspection", "Native functions: ossie_datasets(), ossie_fields(), ossie_metrics(), ossie_relationships().")
    ], badge="Extension Core")

    add_card(s12, 4.8, 1.8, 3.6, 5.0, "Autonomous SQL Planning", [
        ("Multi-Grain Compilation", "ossie_compile autonomously generates GROUP BY and aggregations across dimensions."),
        ("Semantic Query Execution", "ossie_query executes complex derived metric calculations without manual SQL."),
        ("duckdb_mcp Integration", "Exposes semantic tools natively via PRAGMA mcp_publish_tool / query."),
        ("Zero Middleware", "Enables direct LLM agent queries without requiring external web servers.")
    ], badge="SQL Synthesis")

    add_card(s12, 8.8, 1.8, 3.6, 5.0, "Containerized Verification", [
        ("Docker Test Service", "Containerized service duckdb-ossie-tester in docker-compose.yml."),
        ("ABI Compatibility", "Pinned to DuckDB 1.5.5 with pre-cached community extension binaries."),
        ("Automated Test Runner", "./run_duckdb_ossie_test.sh validates all 6 lifecycle steps with code 0."),
        ("Architectural Verdict", "Proven complement to FastMCP: ultra-fast in-engine compilation.")
    ], badge="6/6 Steps Passed", border_color=C_EMERALD)

    # =========================================================================
    # SLIDE 13: Deployment & Operational Developer Experience
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Deployment & Operational Workflow", "DevOps & CLI")

    add_card(s13, 0.8, 1.8, 5.6, 5.0, "Execution Modes & Automated Tooling", [
        ("./start_infra.sh", "Starts data-generator, Gravitino, and MCP server in background."),
        ("./query.sh <prompt>", "Executes Gemma Agent one-shot query against running MCP server."),
        ("./query.sh", "Launches interactive conversational REPL session with Gemma."),
        ("./run_tests.sh", "Runs full 5-scenario Gemma test suite against live infrastructure."),
        ("./run_duckdb_ossie_test.sh", "Runs containerized test for native duckdb-ossie C++ extension."),
        ("./stop_infra.sh", "Tears down containers and wipes volumes.")
    ], badge="Developer Workflow")

    add_card(s13, 6.8, 1.8, 5.6, 5.0, "CI/CD & Container Portability", [
        ("./run.sh", "Single-command bootstrap, build, end-to-end verification and exit code 0."),
        ("100% Dockerized", "All services, agents, and test runners run inside Docker Compose."),
        ("Zero Host Toolchains", "No local Python, Go, or DuckDB required on the developer host."),
        ("Multi-Layer Verification", "Validates Iceberg metadata, Gravitino REST, DuckDB SQL, and Gemma LLM.")
    ], badge="CI/CD Pipeline")

    # =========================================================================
    # SLIDE 14: Summary & Business Value
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Key Takeaways & Future Roadmap", "Strategic Value")

    add_card(s14, 0.8, 1.8, 3.6, 5.0, "Proven Results", [
        ("Zero-ETL Success", "Bridged conflicting schemas without copying data."),
        ("Standards Alignment", "Fully compliant with Apache Iceberg & Gravitino."),
        ("High Performance", "Sub-second federated SQL in DuckDB."),
        ("Dual Semantic Support", "Verified FastMCP bridge and native duckdb-ossie C++ extension."),
        ("Agentic Accessibility", "Standard MCP interface enabling conversational AI.")
    ], badge="Accomplished")

    add_card(s14, 4.8, 1.8, 3.6, 5.0, "Business Impact", [
        ("Tourism Sustainability", "Accurately computes tourism pressure and congestion risks."),
        ("Cross-Entity Trust", "Allows public and private entities to collaborate without sharing raw internal DBs."),
        ("Interoperability Blueprint", "Ready for deployment across Spanish smart destinations.")
    ], badge="Impact")

    add_card(s14, 8.8, 1.8, 3.6, 5.0, "Future Roadmap", [
        ("Enterprise Storage", "Transition from local volume to S3/GCS object stores with Gravitino."),
        ("Live Stream Updates", "Continuous CDC ingestion into Iceberg tables."),
        ("Multi-Modal Dashboard", "Visual geospatial heatmaps embedded in agent responses.")
    ], badge="Roadmap")

    # Save presentation
    prs.save(output_path)
    print(f"✓ Successfully generated presentation at: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "DEPLOYTOUR_PoC_Architecture_and_Testing.pptx"
    create_deck(out)

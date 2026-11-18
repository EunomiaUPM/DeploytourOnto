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
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


def create_deck(output_path="DEPLOYTOUR_PoC_Architecture_and_Testing.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # UPM & DEPLOYTOUR Design Tokens
    C_UPM_NAVY = RGBColor(10, 37, 64)       # #0A2540
    C_UPM_DEEP = RGBColor(0, 51, 102)       # #003366
    C_UPM_BLUE = RGBColor(0, 119, 200)      # #0077C8
    C_UPM_LIGHT = RGBColor(224, 242, 254)   # #E0F2FE

    C_SOVEREIGN = RGBColor(5, 150, 105)     # #059669
    C_SOV_LIGHT = RGBColor(236, 253, 245)   # #ECFDF5
    C_SOV_BORDER = RGBColor(110, 231, 183)  # #6EE7B7

    C_ALERT = RGBColor(220, 38, 38)         # #DC2626
    C_ALERT_LIGHT = RGBColor(254, 242, 242) # #FEF2F2
    C_ALERT_BORDER = RGBColor(252, 165, 165)# #FCA5A5

    C_AMBER = RGBColor(217, 119, 6)         # #D97706
    C_AMBER_LIGHT = RGBColor(255, 251, 235) # #FFFBEB
    C_AMBER_BORDER = RGBColor(252, 211, 77) # #FCD34D

    C_PURPLE = RGBColor(126, 34, 206)       # #7E22CE
    C_PURPLE_LIGHT = RGBColor(250, 245, 255)# #FAF5FF

    C_SLATE_50 = RGBColor(248, 250, 252)
    C_SLATE_100 = RGBColor(241, 245, 249)
    C_BORDER = RGBColor(203, 213, 225)
    C_TEXT = RGBColor(15, 23, 42)
    C_MUTED = RGBColor(71, 85, 105)
    C_WHITE = RGBColor(255, 255, 255)

    def add_top_stripe(slide):
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.08))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = C_UPM_BLUE
        stripe.line.color.rgb = C_UPM_BLUE

    def add_header(slide, title_text, badge_text, corner_tag="DEPLOYTOUR • UPM"):
        add_top_stripe(slide)

        # Category badge pill
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(0.28), Inches(6.2), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = C_UPM_LIGHT
        badge.line.color.rgb = C_UPM_LIGHT
        tf_b = badge.text_frame
        tf_b.margin_left = Inches(0.12)
        tf_b.margin_top = Inches(0.03)
        p_b = tf_b.paragraphs[0]
        p_b.text = badge_text.upper()
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = C_UPM_DEEP

        # Corner tag
        c_box = slide.shapes.add_textbox(Inches(9.0), Inches(0.28), Inches(3.733), Inches(0.32))
        tf_c = c_box.text_frame
        p_c = tf_c.paragraphs[0]
        p_c.alignment = PP_ALIGN.RIGHT
        p_c.text = corner_tag
        p_c.font.size = Pt(10.5)
        p_c.font.bold = True
        p_c.font.color.rgb = C_MUTED

        # Main Slide Title
        t_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.65), Inches(12.133), Inches(0.65))
        tf_t = t_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = C_UPM_NAVY

        # Divider
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.32), Inches(12.133), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = C_BORDER
        line.line.color.rgb = C_BORDER

    def add_footer(slide, takeaway_text, slide_num):
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(6.85), Inches(12.133), Inches(0.42))
        bar.fill.solid()
        bar.fill.fore_color.rgb = C_SLATE_100
        bar.line.color.rgb = C_BORDER
        bar.line.width = Pt(1)

        tb = slide.shapes.add_textbox(Inches(0.75), Inches(6.9), Inches(10.8), Inches(0.32))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = takeaway_text
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_UPM_NAVY

        nb = slide.shapes.add_textbox(Inches(11.6), Inches(6.9), Inches(1.0), Inches(0.32))
        p_n = nb.text_frame.paragraphs[0]
        p_n.alignment = PP_ALIGN.RIGHT
        p_n.text = f"{slide_num:02d} / 18"
        p_n.font.size = Pt(10.5)
        p_n.font.bold = True
        p_n.font.color.rgb = C_MUTED

    def add_card(slide, left, top, width, height, title, items, badge="",
                 border_color=C_BORDER, bg_color=C_SLATE_50, title_color=C_UPM_NAVY):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.14), Inches(width - 0.36), Inches(height - 0.28))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(14)
        p0.font.bold = True
        p0.font.color.rgb = title_color

        if badge:
            pb = tf.add_paragraph()
            pb.text = badge
            pb.font.size = Pt(10)
            pb.font.bold = True
            pb.font.color.rgb = C_UPM_BLUE
            pb.space_before = Pt(2)

        for item in items:
            p = tf.add_paragraph()
            p.space_before = Pt(5)
            p.font.size = Pt(11)
            p.font.color.rgb = C_TEXT
            if isinstance(item, tuple):
                p.text = f"• {item[0]}: "
                p.font.bold = True
                run = p.add_run()
                run.text = item[1]
                run.font.bold = False
            else:
                p.text = f"• {item}"

    def add_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = notes_text

    # =========================================================================
    # SLIDE 01: Title Slide — OSI-Based Semantic Solution
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_UPM_NAVY
    bg1.line.color.rgb = C_UPM_NAVY

    accent1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(0.14), Inches(4.5))
    accent1.fill.solid()
    accent1.fill.fore_color.rgb = C_UPM_BLUE
    accent1.line.color.rgb = C_UPM_BLUE

    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(7.5), Inches(4.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "DEPLOYTOUR • SEMANTIC INTEROPERABILITY"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_AMBER_BORDER

    p = tf1.add_paragraph()
    p.text = "OSI-Based Semantic Solution"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.space_before = Pt(10)

    p = tf1.add_paragraph()
    p.text = "Deterministic, real-time semantic interoperability for federated tourism data spaces — without moving or centralizing source databases."
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_before = Pt(14)

    p = tf1.add_paragraph()
    p.text = "Universidad Politécnica de Madrid (UPM)  |  YAML Contracts (Apache OSSIE + ODRL)  |  DuckDB + MCP + Gemma"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_SOV_BORDER
    p.space_before = Pt(24)

    # Right Emblem Card ("BabelFish")
    add_card(
        s1, 9.0, 1.5, 3.7, 4.4,
        "BabelFish for Data Spaces",
        [
            ("Universal Translator", "Bridges FIWARE & SEGITTUR schemas in real time."),
            ("100% Sovereign", "Zero raw data copies or central cloud lakes."),
            ("Auditable AI", "Governed YAML contracts eliminate SQL hallucinations."),
            ("POC v2", "Dockerized Iceberg, Gravitino, Ossie, DuckDB & MCP.")
        ],
        badge="UPM • VIENNA",
        border_color=C_UPM_BLUE,
        bg_color=C_UPM_LIGHT,
        title_color=C_UPM_NAVY
    )
    add_notes(s1, "Welcome everyone. Today the UPM team presents our OSI-based semantic interoperability solution for DEPLOYTOUR — a real-time, deterministic translation layer that connects federated tourism data spaces without moving source data.")

    # =========================================================================
    # SLIDE 02: Alice's Challenge & Sovereignty Rule
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Alice's Challenge: Computing Tourism Pressure Without Moving Source Data",
               "Slide 02 • Business Use Case & Data Sovereignty Rule", "Federated Tourism Data Space")

    add_card(s2, 0.6, 1.55, 4.0, 5.0, "4 Sovereign Data Partners (Local)", [
        ("John (City Hall)", "Population & Census • SEGITTUR"),
        ("Paul (Hotels)", "Beds & Occupancy • FIWARE"),
        ("George (Mobility)", "Passenger Flows • GTFS"),
        ("Ringo (Rentals)", "Tourist Rentals • REST API"),
        ("100% Sovereignty", "Each owner keeps data in-place.")
    ], badge="STAY AT ORIGIN", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_card(s2, 4.85, 1.55, 3.6, 5.0, "Alice — DMO Manager", [
        ("Goal", "Needs real-time sustainability KPI before City Council deadline."),
        ("Formula", "Tourism Pressure Index = (Tourists + Day-trippers) / (Residents + Beds)"),
        ("Federated Outcome", "Computed in-place without copying source databases.")
    ], badge="FEDERATED QUERY", border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT, title_color=C_UPM_NAVY)

    add_card(s2, 8.7, 1.55, 4.0, 5.0, "False Solution: Cloud Monolith", [
        ("Blocked Pattern", "Copying all hotel and city databases into one central lake."),
        ("Why It Fails", "Strips local owners of data sovereignty and creates GDPR/commercial risk."),
        ("STOP", "Never copy raw data into a central monolith.")
    ], badge="BLOCKED", border_color=C_ALERT, bg_color=C_ALERT_LIGHT, title_color=C_ALERT)

    add_footer(s2, "Data Space Golden Rule: Bring the computation to the data, never copy raw data into a central monolith.", 2)
    add_notes(s2, "Meet Alice, a Destination Manager who needs the Tourism Pressure Index before a City Council vote. John, Paul, George, and Ringo hold the required datasets locally. Copying everything into a central cloud monolith violates data sovereignty — so we compute the KPI in place via federated queries.")

    # =========================================================================
    # SLIDE 03: 4 Dialects & N×M Scaling Explosion
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Four Incompatible Dialects for the Same Municipality Trigger an N×M Explosion",
               "Slide 03 • Semantic Mismatch & Scaling Bottleneck", "N × M vs. N + M")

    add_card(s3, 0.6, 1.55, 5.9, 5.0, "1. The Semantic Tower of Babel (Same City)", [
        ("John (SEGITTUR)", "municipio_id, poblacion"),
        ("Paul (FIWARE)", "refMunicipality, beds"),
        ("George (GTFS CSV)", "stop_city, pax_count"),
        ("Ringo (REST API)", "cod_ine, plazas_vt"),
        ("Unified Contract", "4 dialects mapped once to canonical ine_municipality_code.")
    ], badge="OSI / OSSIE HUB", border_color=C_UPM_BLUE, bg_color=C_SLATE_50)

    add_card(s3, 6.8, 1.55, 5.9, 5.0, "2. Maintenance Explosion (4 DMO Apps)", [
        ("Custom Point-to-Point (N × M)", "4 providers × 4 apps = 16 adapters today; 20 providers = 80 adapters!"),
        ("Semantic Hub Standard (N + M)", "20 providers + 4 apps = Only 24 integrations."),
        ("Impact", "-70% connectors & maintenance overhead.")
    ], badge="-70% CONNECTORS", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s3, "Impact: Replacing custom ETL pipelines (N×M) with an N+M semantic federation layer cuts overhead by 70%.", 3)
    add_notes(s3, "All four partners refer to the exact same city, yet they use four incompatible field names. Point-to-point adapters explode quadratically (N×M = 80). Mapping each source once to a canonical OSI contract cuts integrations by 70% (N+M = 24).")

    # =========================================================================
    # SLIDE 04: Classic Semantic Web Gap
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Classic Semantic Web (RDF/OWL) Creates an Impedance Gap Between Data and AI",
               "Slide 04 • Why Classic Semantic Web Fails Operational Data", "3-Tier Architecture")

    add_card(s4, 0.6, 1.55, 12.133, 1.35, "Top Tier: Modern Operational Demand (AI Agents & DMO Dashboards)", [
        "Need instant SQL / tabular KPI answers today without graph traversal delays."
    ], border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s4, 0.6, 3.05, 12.133, 1.75, "Middle Wall: Classic W3C Stack (XML / RDF Triples / OWL Ontologies)", [
        ("Complex Graph Inference", "Heavy reasoning overhead for simple aggregations."),
        ("High Query Latency", "No native mapping to Apache Iceberg, Parquet, or DuckDB SQL."),
        ("Practical Bridge (OSI / Apache OSSIE)", "Lightweight semantic contracts (YAML) over SQL & Iceberg — zero heavy RDF triples.")
    ], badge="THE SEMANTIC GAP", border_color=C_ALERT, bg_color=C_ALERT_LIGHT, title_color=C_ALERT)

    add_card(s4, 0.6, 4.95, 12.133, 1.55, "Bottom Tier: Modern Operational Storage Reality", [
        ("SQL / BI", "City & ERP Databases"),
        ("Parquet / Iceberg", "Modern Data Lakehouses"),
        ("REST / CSV", "Hotel & Sensor APIs")
    ], border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT)

    add_footer(s4, "Tech Reality: Hotels and municipalities will not migrate their operational SQL/Iceberg tables into RDF triple stores.", 4)
    add_notes(s4, "Operational tourism systems run on SQL, Parquet/Iceberg, and REST APIs, while AI agents need instant tabular answers. Heavy RDF triple stores create an impedance gap. Lightweight YAML semantic contracts bridge SQL and AI directly.")

    # =========================================================================
    # SLIDE 05: LLM Loops vs. Deterministic OSI Contract
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "On-the-Fly LLM Loops Hallucinate KPIs; OSI Contracts Guarantee 100% Repeatability",
               "Slide 05 • Hallucination Risk vs. Deterministic Trust", "Zero SQL Hallucinations")

    add_card(s5, 0.6, 1.55, 12.133, 2.4, "1. On-the-Fly Knowledge Graph + LLM Loop (Non-Deterministic)", [
        ("Prompt", "\"Tourism pressure in August?\" -> Unbalanced ontology + agent guesses JOINs."),
        ("Divergent Runs", "Run 1: Index = 4.20  |  Run 2: Index = 3.85  |  Run 3: Wrong JOIN (Hallucinated) ❌"),
        ("Business Risk", "Different answers every time you ask — unacceptable for public policy.")
    ], badge="PROBABILISTIC", border_color=C_ALERT, bg_color=C_ALERT_LIGHT, title_color=C_ALERT)

    add_card(s5, 0.6, 4.15, 12.133, 2.4, "2. OSI / Apache OSSIE Semantic Contract (Deterministic)", [
        ("Same Prompt", "\"Tourism pressure in August?\" -> Explicit YAML Spec (spec.yaml) with audited joins & KPI formula."),
        ("100% Repeatable", "Every Run: Index = 4.15 ✔  with full auditable data lineage."),
        ("Result", "Zero hallucinations, instant execution, and full trust for decision-makers.")
    ], badge="100% AUDITABLE", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s5, "Architectural Key: AI must never guess schemas; the LLM queries a governed OSI semantic contract.", 5)
    add_notes(s5, "Letting an LLM loop guess joins produces different KPIs on every run. With an explicit Apache OSSIE YAML contract, the formula and join keys are audited once and return 4.15 every single time.")

    # =========================================================================
    # SLIDE 06: OSI Standard & Launch Partners
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "OSI: Open Semantic Interoperability",
               "Slide 06 • The Universal OSI Standard", "open-semantic-interchange.org")

    add_card(s6, 0.6, 1.55, 5.9, 5.0, "The Universal Standard for Semantic Data", [
        ("100% Vendor Neutral", "Open industry standard for exchanging semantic metadata."),
        ("YAML Declarative Spec", "Human- and machine-readable single source of truth."),
        ("Apache 2.0", "Open-source governance with zero vendor lock-in."),
        ("AI Ready", "Built as semantic contracts for BI and AI agents.")
    ], badge="OPEN STANDARD", border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s6, 6.8, 1.55, 5.9, 5.0, "Open Semantic Interchange — Launch Partners", [
        ("Data & Warehouses", "Snowflake, dbt Labs, Cube, Hex"),
        ("AI & Analytics", "Mistral AI, ThoughtSpot, Sigma, Honeydew"),
        ("Enterprise & Governance", "Salesforce, Alation, Atlan, RelationalAI"),
        ("Ecosystem Value", "Global industry backing ensures long-term interoperability.")
    ], badge="GLOBAL INDUSTRY BACKING", border_color=C_SOVEREIGN, bg_color=C_SLATE_50)

    add_footer(s6, "Adopting an open standard backed by data & AI leaders prevents vendor lock-in.", 6)
    add_notes(s6, "We build on Open Semantic Interchange (OSI) — a vendor-neutral, Apache 2.0 YAML standard backed by Snowflake, dbt Labs, Mistral AI, Salesforce, and leading metadata platforms.")

    # =========================================================================
    # SLIDE 07: The OSI Layer Cake
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "The Layer Cake: Clean Separation of Concept, Logic & Physical Storage",
               "Slide 07 • OSI Layered Architecture", "ontology.json + spec.yaml")

    add_card(s7, 0.6, 1.55, 12.133, 1.55, "1. Conceptual Level (ontology.json)", [
        "Technology-agnostic domain vocabulary: defines canonical concepts, inheritance, relationships, and natural-language verbalizations."
    ], border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s7, 0.6, 3.25, 12.133, 1.55, "2. Logical Level (spec.yaml)", [
        "Concrete data products: encapsulates calculated metrics, explicit joins, and consumer-ready analytical models for BI and AI."
    ], border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_card(s7, 0.6, 4.95, 12.133, 1.55, "3. Physical Level (System Schemas)", [
        "Decoupled from Ossie: underlying physical storage layouts (Iceberg, Parquet, SQL) and local partition keys."
    ], border_color=C_MUTED, bg_color=C_SLATE_100)

    add_footer(s7, "Key Benefit: Physical warehouse tables can evolve without breaking business logic or AI prompts.", 7)
    add_notes(s7, "OSI separates semantics into three clean tiers: Conceptual (ontology.json), Logical (spec.yaml), and Physical Storage. Physical warehouse schemas can evolve without breaking business KPIs.")

    # =========================================================================
    # SLIDE 08: Applied Tourism Example Across 3 Layers
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Mapping the Tourism Pressure Index Across All 3 OSI Layers",
               "Slide 08 • Applied Tourism Example", "TOURISM EXAMPLE")

    add_card(s8, 0.6, 1.55, 12.133, 1.55, "1. Conceptual (Business) — DMO Business Language", [
        "Tourism Pressure Index & Overnight Stays KPI."
    ], border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_card(s8, 0.6, 3.25, 12.133, 1.55, "2. Logical (OSSIE YAML) — spec.yaml", [
        "visitors / (residents + beds)  —  Joined via 5-digit INE municipality code (municipality_code = codigo_ine_municipio)."
    ], border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s8, 0.6, 4.95, 12.133, 1.55, "3. Physical (Storage) — Untouched Distributed Silos", [
        "Hotel FIWARE Iceberg Tables (/data/lakehouse_a_fiware) + City SEGITTUR Tables (/data/lakehouse_b_segittur)."
    ], border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_footer(s8, "Full Traceability: Every business KPI maps deterministically down to physical source tables.", 8)
    add_notes(s8, "Applied to tourism: the Conceptual layer defines the Tourism Pressure Index; the Logical layer specifies the YAML formula joined by INE municipality code; the Physical layer leaves FIWARE and SEGITTUR tables untouched.")

    # =========================================================================
    # SLIDE 09: Apache OSSIE Hub-and-Spoke
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Apache OSSIE: From N×M Spaghetti to a Hub-and-Spoke Model",
               "Slide 09 • Open-Source Implementation", "ossie.apache.org")

    add_card(s9, 0.6, 1.55, 5.9, 5.0, "The N × M Problem (Quadratic Mess)", [
        ("Point-to-Point Chaos", "BI Tool A, AI Model B, BI Tool C, AI Agent D each wire directly to Databases 1–4."),
        ("Semantic Fragmentation", "Inconsistent business definitions across silos."),
        ("AI SQL Hallucinations", "Agents guess raw SQL joins without shared contracts.")
    ], badge="BEFORE", border_color=C_ALERT, bg_color=C_ALERT_LIGHT, title_color=C_ALERT)

    add_card(s9, 6.8, 1.55, 5.9, 5.0, "The Ossie Hub-and-Spoke (Linear N+M Flow)", [
        ("Shared Semantic Source of Truth", "Apache Ossie sits between all BI/AI tools and all physical databases."),
        ("Decentralized & Self-Describing", "Turns a quadratic integration mess into a clean N+M pipeline."),
        ("Native DuckDB Support", "Validated via duckdb-ossie & duckdb_mcp community extensions.")
    ], badge="AFTER", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s9, "Tourism Value: Each actor keeps its existing tools while sharing one trusted KPI dictionary.", 9)
    add_notes(s9, "Apache OSSIE implements OSI as a Hub-and-Spoke semantic source of truth, eliminating quadratic point-to-point integration spaghetti across BI tools and AI agents.")

    # =========================================================================
    # SLIDE 10: Ongoing POC & Scope Isolation
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Ongoing POC: Validating End-to-End Semantic Federation",
               "Slide 10 • Proof of Concept (POC)", "Ongoing Work")

    add_card(s10, 0.6, 1.55, 5.9, 5.0, "Core POC Focus", [
        ("Semantic Resolution", "Gemma + FastMCP translates natural language via Apache Ossie."),
        ("Catalog Discovery", "Apache Gravitino resolves Iceberg catalogs for FIWARE & SEGITTUR."),
        ("In-Memory Joins", "DuckDB executes zero-copy cross-ontology joins over Parquet/Iceberg."),
        ("Flow", "Gemma LLM -> FastMCP -> Ossie -> Gravitino -> DuckDB")
    ], badge="END-TO-END VALIDATION", border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s10, 6.8, 1.55, 5.9, 5.0, "Controlled Scope: Isolating the Semantic Layer", [
        ("Abstracted Cryptography", "Verifiable Credential (VC) overhead is abstracted in this initial POC stage."),
        ("100% Focus on Semantics", "Validates semantic interaction, SQL security guardrails, and zero-copy execution."),
        ("Next Step (Act V)", "Direct integration with the 5 European trial data-space connectors.")
    ], badge="CONTROLLED SCOPE", border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_footer(s10, "POC Goal: Prove semantic determinism before scaling across the 5 European trial data spaces.", 10)
    add_notes(s10, "Our ongoing POC validates end-to-end semantic resolution and in-memory SQL federation first, temporarily abstracting Verifiable Credential overhead before plugging into the 5 European trial connectors.")

    # =========================================================================
    # SLIDE 11: 5-Tier Containerized Topology
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "DEPLOYTOUR: 5-Tier Containerized Topology",
               "Slide 11 • Containerized Topology", "Docker • Iceberg • Gravitino • Ossie • DuckDB • Gemma")

    tiers = [
        ("TIER 5: Intelligence Layer", "Autonomous Google Gemma LLM agent with structured Gemma-2 tool prompting (./query.sh).", C_UPM_NAVY, C_UPM_LIGHT),
        ("TIER 4: Federated Execution Engine", "DuckDB with native Iceberg & spatial extensions + FastMCP server (Port 8000).", C_UPM_BLUE, C_SLATE_50),
        ("TIER 3: Semantic Layer (OSI)", "Vocabulary Hub & Apache Ossie formalizing concepts, schemas, and structural joins (ossie/*.yaml, duckdb_ossie_model.json).", C_SOVEREIGN, C_SOV_LIGHT),
        ("TIER 2: Catalog Governance", "Apache Gravitino 0.5.1 metalake federating dual Iceberg REST catalogs: fiware_catalog & segittur_catalog (Port 8090).", C_AMBER, C_AMBER_LIGHT),
        ("TIER 1: Storage & Ingestion", "Synthetic Parquet (Go parquet-go) + PyIceberg v1.metadata.json on shared Docker volume (/data).", C_MUTED, C_SLATE_100),
    ]
    for idx, (t_title, t_desc, b_col, bg_col) in enumerate(tiers):
        top = 1.52 + idx * 1.03
        add_card(s11, 0.6, top, 12.133, 0.92, t_title, [t_desc], border_color=b_col, bg_color=bg_col, title_color=b_col)

    add_footer(s11, "Modular Architecture: 100% powered by open-source foundations (Iceberg, Gravitino, Ossie, DuckDB).", 11)
    add_notes(s11, "Our containerized POC stack spans 5 clean tiers: Parquet/Iceberg storage, Apache Gravitino catalog governance, the OSI Semantic Layer, DuckDB + FastMCP federated execution, and the Google Gemma LLM agent.")

    # =========================================================================
    # SLIDE 12: Anatomy of a Query (Las Palmas — INE 35016)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "The Resolution Pipeline: Anatomy of a Query (Las Palmas — INE 35016)",
               "Slide 12 • Federated Query Anatomy", "End-to-End 6 Steps")

    add_card(s12, 0.6, 1.55, 5.9, 5.0, "Steps 1–3: Intent & Semantic Translation", [
        ("Step 1: The Ask (Gemma)", "User asks: \"What is the tourism pressure in Las Palmas?\""),
        ("Step 2: Tool Selection (MCP)", "Gemma invokes governed tool execute_federated_query."),
        ("Step 3: Translation (V-Hub + Ossie)", "Maps FIWARE taxonomy to SEGITTUR schemas and supplies derived KPI formula (spec.yaml).")
    ], badge="SEMANTIC RESOLUTION", border_color=C_UPM_BLUE, bg_color=C_SLATE_50)

    add_card(s12, 6.8, 1.55, 5.9, 5.0, "Steps 4–6: Federated Execution & Output", [
        ("Step 4: Catalog Resolution (Gravitino)", "Metalake resolves physical endpoints for both Iceberg datasets."),
        ("Step 5: In-Memory Join (DuckDB)", "Vectorized execution joins both sources on municipality_code 35016."),
        ("Step 6: The Output (SSE Stream)", "Streams audited Markdown report back to the user.")
    ], badge="ZERO DATA DUPLICATION", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s12, "From natural-language prompt to federated join in milliseconds — zero data duplication.", 12)
    add_notes(s12, "Tracing a live query for Las Palmas (INE 35016): Gemma invokes FastMCP, Vocabulary Hub & Ossie translate FIWARE and SEGITTUR schemas, Gravitino locates the Iceberg tables, and DuckDB joins them in memory in milliseconds.")

    # =========================================================================
    # SLIDE 13: Semantic Layer — Separated Interacting Components
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Semantic Layer: Vocabulary Hub, Apache OSSIE & Decoupled Components",
               "Slide 13 • Semantic Layer & Vocabulary Hub Architecture", "Modular Semantic Plane")

    add_card(s13, 0.6, 1.55, 3.0, 5.0, "Origin Data Spaces", [
        ("City Data Space", "SEGITTUR Schema kept at City Hall."),
        ("Hotel Data Space", "FIWARE Schema kept in Hotel systems."),
        ("100% Sovereignty", "Untouched at source.")
    ], badge="AT ORIGIN", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    # 4 Modular Components inside Semantic Layer
    add_card(s13, 3.85, 1.55, 2.7, 2.4, "1. Vocabulary Hub", [
        "Canonical dictionary & cross-dialect mappings (FIWARE <-> SEGITTUR)."
    ], badge="ontology.json", border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s13, 6.75, 1.55, 2.7, 2.4, "2. Apache OSSIE", [
        "Logical contracts, KPI formulas & audited join rules."
    ], badge="spec.yaml", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT)

    add_card(s13, 3.85, 4.15, 2.7, 2.4, "3. ODRL Policy Engine", [
        "Evaluates permissions, duties & prohibitions before data access."
    ], badge="W3C ODRL", border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_card(s13, 6.75, 4.15, 2.7, 2.4, "4. DuckDB + FastMCP", [
        "Exposes MCP tools & runs zero-copy in-memory joins."
    ], badge="RUNTIME", border_color=C_PURPLE, bg_color=C_PURPLE_LIGHT, title_color=C_PURPLE)

    add_card(s13, 9.7, 1.55, 3.0, 5.0, "Consumers & AI", [
        ("FastMCP Interface", "Standard tool protocol for AI & BI."),
        ("Google Gemma Agent", "Natural-language Q&A with zero SQL hallucinations."),
        ("Alice (DMO)", "Gets audited sustainability KPI.")
    ], badge="POC: VC ABSTRACTED", border_color=C_UPM_NAVY, bg_color=C_SLATE_100)

    add_footer(s13, "Key Takeaway: Inside the Semantic Layer, Vocabulary Hub, Apache OSSIE, ODRL, and DuckDB/MCP stay modular and interoperate cleanly.", 13)
    add_notes(s13, "Inside the Semantic Layer, Vocabulary Hub, Apache OSSIE, the ODRL Policy Engine, and DuckDB + FastMCP are distinct, modular components that interact dynamically while keeping Origin Data Spaces untouched.")

    # =========================================================================
    # SLIDE 14: Automated Governance — W3C ODRL Policy Validation
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Automated Governance: W3C ODRL Policy Validation",
               "Slide 14 • Query-Time Compliance Engine", "Pre-Execution Policy Gate")

    add_card(s14, 0.6, 1.55, 3.2, 5.0, "1. Data Request", [
        ("Caller", "AI Agent / Analyst via MCP Tool Call."),
        ("Target", "Hotel Occupancy + City Population for Municipality 35016.")
    ], badge="MCP TOOL CALL", border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s14, 4.05, 1.55, 4.9, 5.0, "2. ODRL Validator (Semantic Layer)", [
        ("PERMISSION (odrl:permits)", "Aggregate public sustainability & tourism pressure KPIs."),
        ("DUTY (odrl:duty)", "Anonymize & aggregate at municipality level + cite source."),
        ("PROHIBITION (odrl:prohibits)", "Granular hotel room-rate scraping or commercial data resale.")
    ], badge="POLICY ENGINE", border_color=C_UPM_NAVY, bg_color=C_SLATE_50)

    add_card(s14, 9.2, 1.55, 3.533, 2.4, "✔ COMPLIANT (ALLOWED)", [
        "DuckDB executes the federated query and returns the aggregated KPI."
    ], border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_card(s14, 9.2, 4.15, 3.533, 2.4, "✕ VIOLATION (BLOCKED)", [
        "Automatically blocked before touching any source database."
    ], border_color=C_ALERT, bg_color=C_ALERT_LIGHT, title_color=C_ALERT)

    add_footer(s14, "Security by Design: Commercial trade secrets are protected before SQL execution ever begins.", 14)
    add_notes(s14, "Before any query touches source data, the ODRL Policy Engine checks permissions, duties, and prohibitions — allowing aggregated sustainability KPIs while automatically blocking granular room-rate scraping.")

    # =========================================================================
    # SLIDE 15: Federated Reference Architecture (DSP + ODRL + VocabularyHub)
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Federated Reference Architecture: Data Space Authority, DSP & VocabularyHub",
               "Slide 15 • European Reference Architecture", "DSP • ODRL • IHUB")

    add_card(s15, 0.6, 1.55, 12.133, 1.35, "Top Tier: Data Space Authority & IHUB Actors", [
        ("Identity Provider", "Trust & credential verification"),
        ("VocabularyHub", "Canonical semantic governance"),
        ("Federated Catalog", "Distributed dataset discovery")
    ], border_color=C_UPM_NAVY, bg_color=C_UPM_LIGHT)

    add_card(s15, 0.6, 3.1, 5.9, 2.45, "Organization A (Data Provider — IHUB)", [
        ("Final Data System", "SQL / Iceberg"),
        ("Connector", "Control Plane (DSP) + Data Plane")
    ], border_color=C_UPM_BLUE, bg_color=C_SLATE_50)

    add_card(s15, 6.833, 3.1, 5.9, 2.45, "Organization B (Data Consumer — IHUB)", [
        ("Connector", "Control Plane (DSP) + Data Plane"),
        ("Final Data System", "DMO App / AI Agent")
    ], border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_card(s15, 0.6, 5.75, 12.133, 0.9, "Open Protocol Bar (IDSA / Gaia-X Blueprint)", [
        "Active Profile: DSP Catalog & Contract Negotiation (ODRL) • Signed by the Hub"
    ], border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_footer(s15, "Full Interoperability: Control plane negotiated via DSP/ODRL and semantics governed by VocabularyHub.", 15)
    add_notes(s15, "In the European Data Space reference architecture, VocabularyHub sits alongside the Identity Provider and Federated Catalog inside the Data Space Authority, governing semantics across DSP/ODRL connectors.")

    # =========================================================================
    # SLIDE 16: Next Steps & 3-Phase Execution Roadmap
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Next Steps & Execution Roadmap",
               "Slide 16 • European Scaling & Execution Plan", "5 Milestones -> 3 Phases")

    add_card(s16, 0.6, 1.55, 6.9, 5.0, "5 Strategic Milestones", [
        ("01 Testing Scenarios", "Connect & validate scenarios across 5 European trial data spaces."),
        ("02 Direct Connectors", "Evolve from batch Iceberg ETL to live on-the-fly federated querying."),
        ("03 Semantic Integration", "Unify Vocabulary Hub, Apache OSSIE, ODRL & MCP in production."),
        ("04 UNE Standardization", "Contribute semantic catalog & Vocabulary Hub specs to UNE."),
        ("05 Unified Domain Ontology", "Establish core tourism ontology across DEPLOYTOUR.")
    ], badge="MILESTONES", border_color=C_UPM_BLUE, bg_color=C_SLATE_50)

    add_card(s16, 7.75, 1.55, 4.983, 1.55, "PHASE 1: Pilot Validation", [
        "Step 01 • Connect and validate real scenarios across 5 European trials."
    ], border_color=C_UPM_BLUE, bg_color=C_UPM_LIGHT)

    add_card(s16, 7.75, 3.25, 4.983, 1.55, "PHASE 2: Live Federation", [
        "Steps 02 & 03 • Move from Iceberg ETL to live on-the-fly querying in Vocabulary Hub."
    ], border_color=C_AMBER, bg_color=C_AMBER_LIGHT, title_color=C_AMBER)

    add_card(s16, 7.75, 4.95, 4.983, 1.55, "PHASE 3: EU Standardization", [
        "Steps 04 & 05 • Publish UNE catalog and unified tourism domain ontology."
    ], border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s16, "From validated POC to an interoperable European tourism standard.", 16)
    add_notes(s16, "Our execution roadmap spans 5 milestones across 3 phases: validating the 5 European trials, moving from batch Iceberg ETL to live federated connectors, and contributing our semantic catalog to UNE standards and a unified tourism ontology.")

    # =========================================================================
    # SLIDE 17: Closing Vision — BabelFish for Data Spaces
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    add_header(s17, "BabelFish for Data Spaces: Real-Time Semantic Interoperability",
               "Slide 17 • Closing Vision", "UPM Team • DEPLOYTOUR")

    add_card(s17, 0.6, 1.55, 7.4, 5.0, "Real-Time Semantic Interoperability in Tourism and Beyond", [
        ("Native Schemas Preserved", "Every destination, hotel, or mobility provider keeps speaking its own native schema."),
        ("Real-Time Translation", "Vocabulary Hub + OSI translates meaning in real time without moving a single source record."),
        ("Cross-Sector Potential", "Applicable to Tourism, Mobility, Energy, Health & Smart Cities."),
        ("UPM Team", "Universidad Politécnica de Madrid — DEPLOYTOUR Vocabulary Hub.")
    ], badge="CLOSING VISION", border_color=C_UPM_NAVY, bg_color=C_UPM_LIGHT)

    add_card(s17, 8.25, 1.55, 4.483, 5.0, "Validated PoC Metrics", [
        ("Verification Suite", "9/9 Gemma Agent & MCP test cases passing."),
        ("Native C++ Ossie", "6/6 duckdb-ossie & duckdb_mcp tests passing."),
        ("Quick Start", "./start_infra.sh  ->  ./query.sh  ->  ./run_tests.sh")
    ], badge="PROVEN IN CODE", border_color=C_SOVEREIGN, bg_color=C_SOV_LIGHT, title_color=C_SOVEREIGN)

    add_footer(s17, "Universidad Politécnica de Madrid • DEPLOYTOUR — BabelFish for Data Spaces", 17)
    add_notes(s17, "Ultimately, Vocabulary Hub + OSI acts as a universal BabelFish for data spaces — enabling real-time semantic interoperability across tourism, mobility, energy, and smart cities.")

    # =========================================================================
    # SLIDE 18: Q&A & Alignment
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    add_header(s18, "Q&A & Executive Alignment",
               "Slide 18 • Discussion & Alignment", "Vienna • UPM Team")

    pillars = [
        ("01 • SOVEREIGNTY", "Zero Central Copies", "Source data stays sovereign inside hotels and city halls.", C_SOVEREIGN, C_SOV_LIGHT),
        ("02 • OSI / OSSIE", "YAML Contracts", "Zero SQL hallucinations; 100% repeatable KPIs.", C_UPM_BLUE, C_UPM_LIGHT),
        ("03 • FEDERATION", "DuckDB + MCP + Gemma", "Vectorized in-memory joins over Iceberg & SQL.", C_AMBER, C_AMBER_LIGHT),
        ("04 • GOVERNANCE", "ODRL Validation", "Permissions & prohibitions enforced before execution.", C_PURPLE, C_PURPLE_LIGHT),
    ]
    for idx, (p_badge, p_title, p_desc, b_col, bg_col) in enumerate(pillars):
        left = 0.6 + idx * 3.08
        add_card(s18, left, 1.55, 2.9, 2.15, p_title, [p_desc], badge=p_badge, border_color=b_col, bg_color=bg_col, title_color=b_col)

    hero_qa = s18.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.95), Inches(12.133), Inches(2.6))
    hero_qa.fill.solid()
    hero_qa.fill.fore_color.rgb = C_UPM_NAVY
    hero_qa.line.color.rgb = C_UPM_BLUE
    hero_qa.line.width = Pt(2)

    tb_qa = s18.shapes.add_textbox(Inches(1.0), Inches(4.3), Inches(11.333), Inches(1.9))
    tf_qa = tb_qa.text_frame
    tf_qa.word_wrap = True
    p_q1 = tf_qa.paragraphs[0]
    p_q1.alignment = PP_ALIGN.CENTER
    p_q1.text = "Q&A & Alignment"
    p_q1.font.size = Pt(34)
    p_q1.font.bold = True
    p_q1.font.color.rgb = C_WHITE

    p_q2 = tf_qa.add_paragraph()
    p_q2.alignment = PP_ALIGN.CENTER
    p_q2.text = "Open discussion and feedback — questions on the architecture or upcoming European trials?"
    p_q2.font.size = Pt(15)
    p_q2.font.color.rgb = C_UPM_LIGHT
    p_q2.space_before = Pt(10)

    add_footer(s18, "Thank you! 18-slide deck aligned with the DEPLOYTOUR OSI Semantic Solution.", 18)
    add_notes(s18, "To recap our four pillars: 100% data sovereignty, deterministic YAML contracts, in-memory DuckDB + MCP federation, and automated ODRL governance. Thank you — we welcome your questions and feedback.")

    prs.save(output_path)
    print(f"Presentation successfully generated ({len(prs.slides)} slides): {os.path.abspath(output_path)}")


if __name__ == "__main__":
    create_deck()

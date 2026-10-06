#!/usr/bin/env bash
set -euo pipefail

echo "================================================================================"
echo "  DEPLOYTOUR: Deploying Core Semantic Infrastructure"
echo "================================================================================"

echo "[1/3] Building and starting infrastructure containers in background..."
docker compose up -d --build data-generator gravitino gravitino-init mcp-server

echo "[2/3] Waiting for infrastructure services to become healthy..."
echo " - Waiting for data-generator and Iceberg lakehouses..."
until docker compose ps data-generator | grep -q "healthy"; do
  sleep 1
done
echo "   ✓ Parquet & Iceberg lakehouses generated successfully."

echo " - Waiting for Apache Gravitino Server (port 8090)..."
until docker compose ps gravitino | grep -q "healthy"; do
  sleep 1
done
echo "   ✓ Apache Gravitino server is healthy."

echo " - Waiting for Gravitino Catalog bootstrap..."
until docker compose ps gravitino-init | grep -q "healthy"; do
  sleep 1
done
echo "   ✓ FIWARE and SEGITTUR catalogs registered in Gravitino."

echo " - Waiting for MCP Server & DuckDB Engine (port 8000)..."
until docker compose ps mcp-server | grep -q "healthy"; do
  sleep 1
done
echo "   ✓ MCP Server is healthy and listening on port 8000."

echo "================================================================================"
echo "  ✓ DEPLOYTOUR Infrastructure is LIVE and READY!"
echo "================================================================================"
echo " - MCP Server URL      : http://localhost:8000"
echo " - Gravitino Server URL: http://localhost:8090"
echo " - REST Tools Endpoint : http://localhost:8000/tools/execute_federated_query"
echo " - JSON-RPC Endpoint   : http://localhost:8000/mcp"
echo ""
echo "To ask natural language questions with the Gemma agent, run:"
echo "  ./query.sh \"Which municipality has the highest tourism pressure?\""
echo "  ./query.sh                          # (Interactive session)"
echo ""
echo "To run the automated test suite, run:"
echo "  ./run_tests.sh"
echo ""
echo "To tear down the infrastructure, run:"
echo "  ./stop_infra.sh"
echo "================================================================================"

#!/usr/bin/env bash
set -euo pipefail

echo "================================================================================"
echo "  DEPLOYTOUR: Cross-Ontology Federation PoC (OSI, Gravitino, DuckDB & MCP)"
echo "================================================================================"

# Tear down previous state and remove all ephemeral volumes
echo "[1/3] Tearing down previous containers and volumes..."
docker compose down -v --remove-orphans

# Build all container images
echo "[2/3] Building container topology..."
docker compose build

# Orchestrate execution and wait for verifier container
echo "[3/3] Bootstrapping federated stack and running test suite..."
docker compose --profile test up --abort-on-container-exit --exit-code-from verifier

echo "================================================================================"
echo "  ✓ DEPLOYTOUR PoC verification completed successfully!"
echo "================================================================================"

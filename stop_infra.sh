#!/usr/bin/env bash
set -euo pipefail

echo "================================================================================"
echo "  DEPLOYTOUR: Stopping & Tearing Down Infrastructure"
echo "================================================================================"

docker compose down -v --remove-orphans

echo "✓ Infrastructure stopped and resources cleaned up."

#!/usr/bin/env bash

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

set -euo pipefail

echo "================================================================================"
echo "  DEPLOYTOUR: Running duckdb-ossie Test (100% Containerized via Docker Compose)"
echo "  Service: duckdb-ossie-tester"
echo "  Reference: https://github.com/iqea-ai/duckdb-ossie"
echo "================================================================================"

docker compose build duckdb-ossie-tester
docker compose run --rm duckdb-ossie-tester

echo "================================================================================"
echo "  ✓ duckdb-ossie containerized test execution completed successfully!"
echo "================================================================================"

#!/bin/sh

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

set -e

GRAVITINO_URL="${GRAVITINO_URL:-http://gravitino:8090}"
echo "[gravitino-init] Waiting for Gravitino at ${GRAVITINO_URL}..."

until curl -s "${GRAVITINO_URL}/api/version" > /dev/null 2>&1; do
  echo "[gravitino-init] Gravitino not ready yet, sleeping 2s..."
  sleep 2
done

echo "[gravitino-init] Gravitino is up! Creating metalake: deploytour_metalake..."
curl -s -X POST "${GRAVITINO_URL}/api/metalakes" \
  -H "Content-Type: application/json" \
  -d '{"name":"deploytour_metalake","comment":"DEPLOYTOUR Cross-Ontology Federation Metalake"}' > /dev/null 2>&1 || true

# Register fiware_catalog if not present
echo "[gravitino-init] Registering fiware_catalog..."
curl -s -X POST "${GRAVITINO_URL}/api/metalakes/deploytour_metalake/catalogs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fiware_catalog",
    "type": "RELATIONAL",
    "provider": "lakehouse-iceberg",
    "comment": "FIWARE Smart Data Models Lakehouse",
    "properties": {
      "catalog-backend": "jdbc",
      "uri": "jdbc:h2:mem:fiware;DB_CLOSE_DELAY=-1;MODE=MYSQL",
      "warehouse": "/data/lakehouse_a_fiware"
    }
  }' > /dev/null 2>&1 || true

# Register segittur_catalog if not present
echo "[gravitino-init] Registering segittur_catalog..."
curl -s -X POST "${GRAVITINO_URL}/api/metalakes/deploytour_metalake/catalogs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "segittur_catalog",
    "type": "RELATIONAL",
    "provider": "lakehouse-iceberg",
    "comment": "SEGITTUR / Schema.org Lakehouse",
    "properties": {
      "catalog-backend": "jdbc",
      "uri": "jdbc:h2:mem:segittur;DB_CLOSE_DELAY=-1;MODE=MYSQL",
      "warehouse": "/data/lakehouse_b_segittur"
    }
  }' > /dev/null 2>&1 || true

echo "[gravitino-init] Verifying registered catalogs..."
CATALOGS_RESP=$(curl -s "${GRAVITINO_URL}/api/metalakes/deploytour_metalake/catalogs")
echo "[gravitino-init] Registered Catalogs: ${CATALOGS_RESP}"

# Health check file touch
touch /tmp/gravitino_init_done
echo "[gravitino-init] Catalog bootstrap completed successfully!"

tail -f /dev/null

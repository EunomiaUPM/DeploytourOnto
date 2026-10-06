#!/bin/sh
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

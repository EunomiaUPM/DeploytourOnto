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

FROM python:3.11-slim

WORKDIR /app

# Install DuckDB 1.5.5 matching the duckdb-ossie community extension ABI
RUN pip install --no-cache-dir "duckdb==1.5.5"

# Pre-install and cache the community extensions inside the container image
RUN python3 -c "import duckdb; con = duckdb.connect(); con.execute('INSTALL ossie FROM community; INSTALL duckdb_mcp FROM community;')"

COPY ossie/duckdb_ossie_model.json /app/ossie/duckdb_ossie_model.json
COPY test/test_duckdb_ossie.py /app/test/test_duckdb_ossie.py

ENV OSSIE_MODEL_PATH=/app/ossie/duckdb_ossie_model.json

CMD ["python3", "test/test_duckdb_ossie.py"]

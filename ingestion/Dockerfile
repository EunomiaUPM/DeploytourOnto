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

# Stage 1: Build Go generator
FROM golang:1.24-alpine AS go-builder
WORKDIR /build

COPY go.mod ./
COPY main.go ./
RUN go mod tidy && CGO_ENABLED=0 GOOS=linux go build -o /build/data-generator main.go

# Stage 2: Runtime container with Python & PyIceberg
FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir "pyiceberg[sql-sqlite,pyarrow]==0.7.1" numpy

COPY --from=go-builder /build/data-generator /app/data-generator
COPY bridge_iceberg.py /app/bridge_iceberg.py

CMD ["sh", "-c", "/app/data-generator /tmp/raw_parquet && python3 /app/bridge_iceberg.py && tail -f /dev/null"]

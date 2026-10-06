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

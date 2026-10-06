FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir duckdb requests pyyaml

# Pre-install duckdb extensions
RUN python3 -c "import duckdb; con = duckdb.connect(); con.execute('INSTALL iceberg; INSTALL spatial;')"

COPY verifier/verify.py ./
COPY gemma_agent /app/gemma_agent/

ENV PYTHONPATH=/app

CMD ["python3", "verify.py"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests pyyaml

COPY gemma_agent /app/gemma_agent/

ENV PYTHONPATH=/app
ENV MCP_SERVER_URL=http://mcp-server:8000

CMD ["python3", "-m", "gemma_agent.test_cases"]

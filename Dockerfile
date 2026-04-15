FROM python:3.12-slim

LABEL maintainer="Enterprise Standards Team"
LABEL description="MCP Standards Server — distributes coding rules and skills to IDEs"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ src/
COPY standards/ standards/
COPY run.py .
COPY config.yaml .

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Expose SSE port
EXPOSE 8080

# Health check — verify the process is listening on port 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('localhost', 8080), timeout=3); s.close()" || exit 1

# Default: streamable-http transport for cloud deployment (works behind reverse proxies)
CMD ["python", "run.py", "--transport", "streamable-http", "--port", "8080", "--log-level", "INFO"]

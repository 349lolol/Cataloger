FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model at build time (cache in image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Use gunicorn for production
# Reduced timeout to 30s - long operations should use background tasks
# Increased workers to 8 for better concurrency
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "--timeout", "30", "--worker-class", "sync", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "run:app"]

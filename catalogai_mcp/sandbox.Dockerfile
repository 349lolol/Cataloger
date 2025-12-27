FROM python:3.11-slim

# Install only safe dependencies
RUN pip install --no-cache-dir httpx

# Copy catalogai SDK
COPY catalogai_sdk /catalogai_sdk
RUN cd /catalogai_sdk && pip install -e .

# Add security hardening
# Create non-root user
RUN useradd -m -u 1001 sandbox
USER sandbox

WORKDIR /code

CMD ["python"]

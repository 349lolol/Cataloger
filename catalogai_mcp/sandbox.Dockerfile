FROM python:3.11-slim

# Install only safe dependencies
RUN pip install --no-cache-dir httpx

# Copy catalogai SDK and install it
# The SDK is structured as a flat package, so we copy it directly
COPY catalogai_sdk /opt/catalogai_sdk
RUN cd /opt/catalogai_sdk && pip install --no-cache-dir .

# Add security hardening
# Create non-root user
RUN useradd -m -u 1001 sandbox
USER sandbox

WORKDIR /code

CMD ["python"]

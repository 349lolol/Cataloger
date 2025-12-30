#!/bin/bash
# Build Docker sandbox for code execution

echo "Building catalogai-sandbox Docker image..."

# Build from project root
cd "$(dirname "$0")/.." || exit 1

docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .

if [ $? -eq 0 ]; then
    echo "✅ Sandbox image built successfully: catalogai-sandbox:latest"
    echo ""
    echo "To verify, run:"
    echo "  docker run --rm catalogai-sandbox:latest python -c 'from catalogai import CatalogAI; print(\"SDK installed:\", CatalogAI.__name__)'"
else
    echo "❌ Failed to build sandbox image"
    exit 1
fi

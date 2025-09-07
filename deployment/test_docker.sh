#!/bin/bash

# Docker Container Test Script
# Run this script to validate the Docker setup

set -e

echo "========================================="
echo "Docker Container Validation Test"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker daemon"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker Compose is not installed${NC}"
    echo "Install with: pip install docker-compose"
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
fi

echo ""
echo "Building Docker image..."
echo "========================================="

# Build the image
if docker build -t llm-surveying-llms:test . ; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

# Check image size
IMAGE_SIZE=$(docker images llm-surveying-llms:test --format "{{.Size}}")
echo "Image size: $IMAGE_SIZE"

# Check if image is under 2GB
SIZE_MB=$(docker images llm-surveying-llms:test --format "{{.Size}}" | sed 's/GB/000/;s/MB//;s/\..*//')
if [ ! -z "$SIZE_MB" ]; then
    if [ "$SIZE_MB" -lt 2000 ]; then
        echo -e "${GREEN}✓ Image size is reasonable (<2GB)${NC}"
    else
        echo -e "${YELLOW}⚠ Image size is large (>2GB)${NC}"
    fi
fi

echo ""
echo "Testing container startup..."
echo "========================================="

# Test container with basic Python import
if docker run --rm llm-surveying-llms:test python -c "
import pandas
import numpy
import matplotlib
import sklearn
print('All packages imported successfully')
"; then
    echo -e "${GREEN}✓ Container runs and packages work${NC}"
else
    echo -e "${RED}✗ Container or package test failed${NC}"
    exit 1
fi

echo ""
echo "Testing with environment variables..."
echo "========================================="

# Test with environment variables
if docker run --rm \
    -e ANTHROPIC_API_KEY="test-key-123" \
    -e SCIMCP_DATA_PATH="/app/data/test.parquet" \
    llm-surveying-llms:test \
    python -c "
import os
assert os.environ.get('ANTHROPIC_API_KEY') == 'test-key-123'
assert os.environ.get('SCIMCP_DATA_PATH') == '/app/data/test.parquet'
print('Environment variables set correctly')
"; then
    echo -e "${GREEN}✓ Environment variables work${NC}"
else
    echo -e "${RED}✗ Environment variable test failed${NC}"
    exit 1
fi

echo ""
echo "Testing volume mounts..."
echo "========================================="

# Create temporary test directory
TEMP_DIR=$(mktemp -d)
echo "Test data" > "$TEMP_DIR/test.txt"

# Test volume mounting
if docker run --rm \
    -v "$TEMP_DIR:/app/test" \
    llm-surveying-llms:test \
    cat /app/test/test.txt | grep -q "Test data"; then
    echo -e "${GREEN}✓ Volume mounting works${NC}"
else
    echo -e "${RED}✗ Volume mounting failed${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Clean up
rm -rf "$TEMP_DIR"

echo ""
echo "Testing Docker Compose..."
echo "========================================="

# Check if docker-compose.yml exists
if [ -f docker-compose.yml ]; then
    # Test compose config
    if docker-compose config &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose configuration is valid${NC}"
    else
        echo -e "${RED}✗ Docker Compose configuration is invalid${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ docker-compose.yml not found${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}All tests passed successfully!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Set your API key: export ANTHROPIC_API_KEY='your-key'"
echo "2. Place data at: ./data/all_papers.parquet"
echo "3. Run: docker-compose up"
echo ""
echo "Or run directly:"
echo "docker run -it --rm \\"
echo "  -e ANTHROPIC_API_KEY='your-key' \\"
echo "  -v \$(pwd)/data:/app/data \\"
echo "  -v \$(pwd)/outputs:/app/outputs \\"
echo "  llm-surveying-llms:test python simplified_demo.py"
echo ""

# Optional: Remove test image
read -p "Remove test image? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi llm-surveying-llms:test
    echo "Test image removed"
fi
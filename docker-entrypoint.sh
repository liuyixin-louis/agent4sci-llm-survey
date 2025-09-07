#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "LLM Surveying LLMs - Docker Container"
echo "========================================"

# Validate environment
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}Warning: ANTHROPIC_API_KEY not set. API operations will fail.${NC}"
    echo "To set: docker run -e ANTHROPIC_API_KEY='your-key' ..."
else
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY is configured${NC}"
fi

# Create necessary directories
mkdir -p /app/data /app/outputs /app/cache /app/logs

# Check if data file exists
if [ ! -f "$SCIMCP_DATA_PATH" ]; then
    echo -e "${YELLOW}Warning: Data file not found at $SCIMCP_DATA_PATH${NC}"
    echo "Please mount your data volume or download the dataset:"
    echo "  docker run -v /path/to/data:/app/data ..."
else
    echo -e "${GREEN}✓ Data file found at $SCIMCP_DATA_PATH${NC}"
    # Get file size
    DATA_SIZE=$(du -h "$SCIMCP_DATA_PATH" | cut -f1)
    echo "  Data file size: $DATA_SIZE"
fi

# System information
echo ""
echo "System Information:"
echo "  Python version: $(python --version 2>&1)"
echo "  Working directory: $(pwd)"
echo "  Cache directory: $CACHE_DIR"
echo "  Log level: $LOG_LEVEL"
echo "  Memory limit: $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null | numfmt --to=iec 2>/dev/null || echo 'Not set')"

# Check Claude CLI
if command -v claude &> /dev/null; then
    echo -e "  Claude CLI: ${GREEN}Available${NC}"
else
    echo -e "  Claude CLI: ${RED}Not available${NC}"
fi

# Python packages check
echo ""
echo "Checking Python packages..."
python -c "
import sys
packages = ['pandas', 'numpy', 'matplotlib', 'sklearn', 'requests']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✓ {pkg}')
    except ImportError:
        print(f'  ✗ {pkg} - MISSING')
        missing.append(pkg)
if missing:
    print(f'\nError: Missing packages: {missing}')
    sys.exit(1)
" || exit 1

echo ""
echo "========================================"
echo -e "${GREEN}Container initialized successfully!${NC}"
echo "========================================"
echo ""

# Execute the main command
exec "$@"
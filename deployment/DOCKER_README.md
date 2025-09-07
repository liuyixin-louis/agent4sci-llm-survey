# Docker Deployment Guide - LLM Surveying LLMs

## Quick Start

### Prerequisites
- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- At least 4GB RAM available
- ANTHROPIC_API_KEY for Claude API access

### 1. Basic Setup

```bash
# Clone the repository
git clone https://github.com/agents4science/llm-surveying-llms
cd llm-surveying-llms

# Create .env file from template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 2. Build and Run

#### Option A: Using Docker Compose (Recommended)

```bash
# Build the image
docker-compose build

# Run the default demo
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

#### Option B: Using Docker CLI

```bash
# Build the image
docker build -t llm-surveying-llms:latest .

# Run with environment variables
docker run -it --rm \
  -e ANTHROPIC_API_KEY="your-api-key" \
  -e SCIMCP_DATA_PATH="/app/data/all_papers.parquet" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  llm-surveying-llms:latest

# Run specific script
docker run -it --rm \
  -e ANTHROPIC_API_KEY="your-api-key" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  llm-surveying-llms:latest \
  python run_real_experiment.py --papers 5
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional API Keys
PERPLEXITY_API_KEY=your-perplexity-key
OPENAI_API_KEY=your-openai-key

# Data Configuration
SCIMCP_DATA_PATH=/app/data/all_papers.parquet
HOST_DATA_PATH=./data
HOST_OUTPUT_PATH=./outputs

# Performance Settings
CACHE_DIR=/app/cache
API_RATE_LIMIT_DELAY=3
LOG_LEVEL=INFO

# Resource Limits (Docker Compose)
MEMORY_LIMIT=4g
CPU_LIMIT=2.0
```

### Volume Mounts

The container uses three main volumes:

1. **Data Volume** (`/app/data`): Mount your sciMCP dataset here
2. **Output Volume** (`/app/outputs`): Results and figures are saved here
3. **Cache Volume** (`/app/cache`): Response cache for performance

Example with custom paths:

```bash
docker run -it --rm \
  -v /path/to/your/data:/app/data \
  -v /path/to/your/outputs:/app/outputs \
  -v /path/to/your/cache:/app/cache \
  llm-surveying-llms:latest
```

## Usage Examples

### Running Experiments

```bash
# Small experiment (5 papers)
docker-compose run --rm llm-survey python run_real_experiment.py --papers 5

# Full experiment (55 papers)
docker-compose run --rm llm-survey python src/experiments/run_experiments.py --papers 55

# Generate figures
docker-compose run --rm llm-survey python create_paper_figures.py

# Run trend discovery
docker-compose run --rm llm-survey python src/discovery/topic_discovery.py --topic "LLM Agents"
```

### Interactive Development

```bash
# Start Jupyter Lab (requires dev profile)
docker-compose --profile dev up jupyter

# Access at http://localhost:8888

# Interactive Python shell
docker-compose run --rm llm-survey python

# Bash shell in container
docker-compose run --rm llm-survey bash
```

### Testing Inside Container

```bash
# Run all tests
docker-compose run --rm llm-survey pytest tests/

# Run specific test
docker-compose run --rm llm-survey pytest tests/test_iterative.py

# Check Claude CLI
docker-compose run --rm llm-survey claude --version
```

## Multi-Stage Build Details

The Dockerfile uses a multi-stage build for optimization:

1. **Builder Stage**: Compiles Python dependencies
2. **Runtime Stage**: Minimal runtime with only necessary components

This reduces the final image size by ~40%.

## Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Verify environment variable is set
docker-compose run --rm llm-survey env | grep ANTHROPIC

# Test API access
docker-compose run --rm llm-survey python -c "
import os
print('API Key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))
"
```

#### 2. Data File Not Found
```bash
# Check volume mount
docker-compose run --rm llm-survey ls -la /app/data/

# Download sample data (if needed)
mkdir -p data
# Place your all_papers.parquet file in ./data/
```

#### 3. Out of Memory
```bash
# Increase memory limit in docker-compose.yml
mem_limit: 8g  # Increase from 4g

# Or use Docker CLI with memory limit
docker run -m 8g ...
```

#### 4. Permission Issues
```bash
# Fix output directory permissions
sudo chown -R $(id -u):$(id -g) outputs/

# Run with user permissions
docker run --user $(id -u):$(id -g) ...
```

### Container Health Check

The container includes a health check that verifies:
- Python environment is functional
- Required packages are importable

Check health status:
```bash
docker-compose ps
docker inspect llm-survey-container --format='{{.State.Health.Status}}'
```

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml llm-survey-stack

# Scale service
docker service scale llm-survey-stack_llm-survey=3
```

### Using Kubernetes

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-survey
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-survey
  template:
    metadata:
      labels:
        app: llm-survey
    spec:
      containers:
      - name: llm-survey
        image: llm-surveying-llms:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: outputs
          mountPath: /app/outputs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
      - name: outputs
        persistentVolumeClaim:
          claimName: outputs-pvc
```

## Image Optimization

Current image size: ~1.5GB

To reduce further:
1. Use Alpine Linux base (saves ~100MB)
2. Remove development dependencies
3. Use pip install --no-cache-dir
4. Clean apt cache after installation

## Security Considerations

1. **Never commit .env files** with real API keys
2. **Use secrets management** in production (Docker Secrets, K8s Secrets)
3. **Run as non-root user** in production:
   ```dockerfile
   USER 1000:1000
   ```
4. **Scan for vulnerabilities**:
   ```bash
   docker scan llm-surveying-llms:latest
   ```

## Monitoring

### Container Metrics
```bash
# Real-time stats
docker stats llm-survey-container

# Resource usage
docker-compose top
```

### Logging
```bash
# View logs
docker-compose logs -f --tail=100

# Save logs to file
docker-compose logs > deployment.log
```

## Backup and Recovery

### Backup Cache and Outputs
```bash
# Backup volumes
docker run --rm \
  -v llm-survey-cache:/cache \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/cache-backup.tar.gz -C /cache .

# Restore volumes
docker run --rm \
  -v llm-survey-cache:/cache \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/cache-backup.tar.gz -C /cache
```

## Support

For issues related to Docker deployment:
1. Check container logs: `docker-compose logs`
2. Verify environment variables are set correctly
3. Ensure volumes are mounted properly
4. Check system resources (RAM, disk space)

For general project issues, see main README.md

---
*Docker deployment guide v1.0.0*  
*Last updated: 2025-09-07*
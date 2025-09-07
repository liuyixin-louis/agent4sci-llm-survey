# LLM Survey Generator API Documentation

## Overview

The LLM Survey Generator API provides a RESTful interface for generating scientific surveys using Large Language Models. It supports multiple generation strategies, real-time progress monitoring via WebSockets, and various output formats.

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints require API key authentication via the `api-key` header:

```http
api-key: your-api-key-here
```

## Endpoints

### 1. Root Endpoint

```http
GET /
```

Returns API information and version.

**Response:**
```json
{
  "message": "LLM Survey Generator API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2. Upload Paper

```http
POST /upload
```

Upload a research paper for inclusion in survey generation.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: File upload

**Response:**
```json
{
  "paper_id": "uuid",
  "filename": "paper.pdf",
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract...",
  "upload_time": "2025-01-01T00:00:00"
}
```

### 3. Create Survey

```http
POST /surveys
```

Create a new survey generation job.

**Request Body:**
```json
{
  "topic": "Large Language Models",
  "paper_ids": ["uuid1", "uuid2"],  // Optional
  "system_type": "iterative",  // Options: baseline, lce, iterative
  "max_iterations": 5,
  "model_preference": "balanced"  // Options: fast, balanced, complex
}
```

**Response:**
```json
{
  "survey_id": "uuid",
  "status": "pending",
  "created_at": "2025-01-01T00:00:00",
  "topic": "Large Language Models",
  "system_type": "iterative"
}
```

### 4. Get Survey Status

```http
GET /surveys/{survey_id}/status
```

Get the current status of a survey generation job.

**Response:**
```json
{
  "survey_id": "uuid",
  "status": "processing",  // Options: pending, processing, completed, failed
  "current_iteration": 2,
  "current_phase": "verifying_quality",
  "quality_score": 3.8,
  "estimated_time_remaining": 120  // seconds
}
```

### 5. Get Completed Survey

```http
GET /surveys/{survey_id}?format=json
```

Retrieve a completed survey.

**Query Parameters:**
- `format`: Output format (`json` or `markdown`)

**Response (JSON):**
```json
{
  "title": "Survey on Large Language Models",
  "sections": [
    {
      "title": "Introduction",
      "content": "Content...",
      "citations": ["Paper1", "Paper2"]
    }
  ],
  "quality_score": 4.2,
  "iterations": 3,
  "metadata": {}
}
```

### 6. List Papers

```http
GET /papers?skip=0&limit=10
```

List uploaded papers with pagination.

**Query Parameters:**
- `skip`: Number of papers to skip
- `limit`: Maximum papers to return

**Response:**
```json
{
  "total": 50,
  "skip": 0,
  "limit": 10,
  "papers": [
    {
      "paper_id": "uuid",
      "filename": "paper.pdf",
      "title": "Paper Title",
      "upload_time": "2025-01-01T00:00:00"
    }
  ]
}
```

### 7. Health Check

```http
GET /health
```

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00",
  "active_jobs": 3,
  "active_connections": 2
}
```

## WebSocket Endpoint

### Real-time Progress Updates

```
ws://localhost:8000/ws/{survey_id}
```

Connect to receive real-time updates during survey generation.

**Message Format:**
```json
{
  "survey_id": "uuid",
  "status": "processing",
  "current_iteration": 2,
  "current_phase": "improving_content",
  "quality_score": 3.9
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- `/upload`: 30 requests per minute
- `/surveys`: 10 requests per minute
- Other endpoints: No limit

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Common Error Codes

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Invalid API key
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error

## System Types

### 1. Baseline (`baseline`)
Basic survey generation without iteration.

### 2. Local Coherence Enhancement (`lce`)
Baseline with 2-pass local coherence improvement.

### 3. Iterative (`iterative`)
Our novel global verification-driven iterative system.

## Model Preferences

- `fast`: Use faster, smaller models (haiku)
- `balanced`: Balance between speed and quality (sonnet)
- `complex`: Use most capable models for best quality (opus)

## Usage Examples

### Python

```python
import requests

# Set up authentication
headers = {"api-key": "your-api-key"}
base_url = "http://localhost:8000"

# Upload a paper
with open("paper.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{base_url}/upload",
        files=files,
        headers=headers
    )
    paper_id = response.json()["paper_id"]

# Create a survey
payload = {
    "topic": "Large Language Models",
    "paper_ids": [paper_id],
    "system_type": "iterative",
    "max_iterations": 5
}
response = requests.post(
    f"{base_url}/surveys",
    json=payload,
    headers=headers
)
survey_id = response.json()["survey_id"]

# Check status
response = requests.get(
    f"{base_url}/surveys/{survey_id}/status",
    headers=headers
)
print(response.json())

# Get completed survey
response = requests.get(
    f"{base_url}/surveys/{survey_id}",
    headers=headers
)
survey = response.json()
```

### JavaScript (WebSocket)

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${surveyId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Status: ${data.status}`);
  console.log(`Phase: ${data.current_phase}`);
  console.log(`Quality: ${data.quality_score}`);
  
  if (data.status === 'completed') {
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### cURL

```bash
# Upload paper
curl -X POST "http://localhost:8000/upload" \
  -H "api-key: your-api-key" \
  -F "file=@paper.pdf"

# Create survey
curl -X POST "http://localhost:8000/surveys" \
  -H "api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Large Language Models",
    "system_type": "iterative"
  }'

# Get status
curl -X GET "http://localhost:8000/surveys/{survey_id}/status" \
  -H "api-key: your-api-key"
```


## Interactive Documentation

The API provides interactive documentation via Swagger UI:

```
http://localhost:8000/docs
```

Alternative documentation via ReDoc:

```
http://localhost:8000/redoc
```

## Performance Considerations

1. **Concurrent Jobs**: Maximum 5 concurrent survey generations
2. **Timeout**: Survey generation may take 5-30 minutes depending on size
3. **Memory**: Each job may consume 1-2GB RAM
4. **Cache**: Results are cached for 24 hours

## Security

1. Always use HTTPS in production
2. Rotate API keys regularly
3. Implement IP whitelisting if needed
4. Monitor rate limit violations
5. Sanitize uploaded files

## Support

For issues or questions:
- GitHub: https://github.com/agents4science/llm-surveying-llms
- API Status: `/health` endpoint

---

*API Version: 1.0.0*  
*Last Updated: 2025-09-07*
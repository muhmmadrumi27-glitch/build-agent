# API Documentation

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.buildagent.com/api/v1
```

## Authentication

All endpoints require Bearer token authentication except `/health` and `/`.

```bash
Authorization: Bearer <jwt_token>
```

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Endpoints

### Tasks

#### Create Task

```http
POST /tasks
Content-Type: application/json
Authorization: Bearer <token>
```

Request:
```json
{
  "goal": "Open Chrome and navigate to Google",
  "session_id": "optional-session-id",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "require_approval": false,
  "metadata": {}
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "goal": "Open Chrome and navigate to Google",
  "status": "completed",
  "result": {
    "success": true,
    "total_steps": 5,
    "completed_steps": 5,
    "duration": 12.5
  }
}
```

#### Execute Action

```http
POST /tasks/{session_id}/actions
Content-Type: application/json
Authorization: Bearer <token>
```

Request:
```json
{
  "action_type": "mouse_click",
  "parameters": {
    "x": 100,
    "y": 200
  },
  "require_approval": false
}
```

Response:
```json
{
  "success": true,
  "action_type": "mouse_click",
  "result": "Clicked at (100, 200)",
  "duration_ms": 150
}
```

#### Get Task Status

```http
GET /tasks/{session_id}/status
Authorization: Bearer <token>
```

Response:
```json
{
  "status": "executing",
  "current_task": "Open Chrome and navigate to Google",
  "current_step": 2,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_actions": 3,
  "successful_actions": 2,
  "failed_actions": 0
}
```

#### Control Execution

```http
POST /tasks/{session_id}/pause
POST /tasks/{session_id}/resume
POST /tasks/{session_id}/stop
Authorization: Bearer <token>
```

Response:
```json
{
  "status": "paused",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Screen Operations

#### Get Screen Preview

```http
GET /screen/preview
Authorization: Bearer <token>
```

Response:
```json
{
  "screenshot_path": "/app/screenshots/shot_1234567890.png",
  "analysis": {
    "dimensions": {"width": 1920, "height": 1080},
    "elements": [...],
    "layout": {...}
  },
  "text_preview": "Current screen text...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Take Screenshot

```http
POST /screen/screenshot
Authorization: Bearer <token>
```

Response:
```json
{
  "screenshot_path": "/app/screenshots/shot_1234567890.png",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Perform OCR

```http
POST /screen/ocr?x=100&y=200&width=300&height=100&languages=en&languages=ur
Authorization: Bearer <token>
```

Response:
```json
{
  "text_regions": [
    {
      "text": "Hello World",
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 30,
      "confidence": 0.95,
      "language": "en"
    }
  ],
  "full_text": "Hello World"
}
```

#### Analyze Screen

```http
POST /screen/analyze
Authorization: Bearer <token>
```

Response:
```json
{
  "dimensions": {"width": 1920, "height": 1080},
  "elements": [
    {
      "element_type": "button",
      "x": 100,
      "y": 200,
      "width": 120,
      "height": 40,
      "confidence": 0.85,
      "text": "Submit"
    }
  ],
  "layout": {
    "header_region": {"x": 0, "y": 0, "width": 1920, "height": 100},
    "main_content_region": {"x": 0, "y": 100, "width": 1920, "height": 900}
  },
  "colors": {
    "dominant_colors": [...],
    "is_dark_mode": false
  }
}
```

### Memory

#### Query Memory

```http
POST /memory/query
Content-Type: application/json
Authorization: Bearer <token>
```

Request:
```json
{
  "query": "How to open Chrome browser",
  "entry_type": "task",
  "n_results": 5
}
```

Response:
```json
{
  "memories": [
    {
      "id": "mem-123",
      "content": "Task: Open Chrome browser\nResult: Success",
      "metadata": {"task_description": "Open Chrome browser"},
      "distance": 0.15
    }
  ],
  "total": 1
}
```

#### Get Session Memory

```http
GET /memory/session/{session_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "memories": [
    {
      "id": "mem-123",
      "content": "Task: Open Chrome browser",
      "metadata": {"session_id": "sess-456"}
    }
  ],
  "total": 1
}
```

#### Clear Session Memory

```http
DELETE /memory/session/{session_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "success": true,
  "session_id": "sess-456"
}
```

### Workflows

#### Create Workflow

```http
POST /workflows
Content-Type: application/json
Authorization: Bearer <token>
```

Request:
```json
{
  "name": "Daily Report Generation",
  "description": "Generate daily analytics report",
  "steps": [
    {
      "action_type": "browser_open",
      "parameters": {}
    },
    {
      "action_type": "browser_navigate",
      "parameters": {"url": "https://analytics.example.com"}
    }
  ],
  "variables": {
    "report_date": "{{date}}"
  },
  "tags": ["daily", "report", "automated"]
}
```

Response:
```json
{
  "id": "wf-123",
  "name": "Daily Report Generation",
  "steps": [...],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### List Workflows

```http
GET /workflows
Authorization: Bearer <token>
```

Response:
```json
{
  "workflows": [
    {
      "id": "wf-123",
      "name": "Daily Report Generation",
      "description": "Generate daily analytics report",
      "usage_count": 15,
      "success_rate": 0.95
    }
  ],
  "total": 1
}
```

#### Execute Workflow

```http
POST /workflows/{workflow_id}/execute
Content-Type: application/json
Authorization: Bearer <token>
```

Request:
```json
{
  "variables": {
    "report_date": "2024-01-15"
  }
}
```

Response:
```json
{
  "workflow_id": "wf-123",
  "status": "executing",
  "session_id": "sess-789"
}
```

### Agent Status

#### Get Status

```http
GET /agent/status
Authorization: Bearer <token>
```

Response:
```json
{
  "status": "idle",
  "current_task": null,
  "current_step": null,
  "session_id": null,
  "total_actions": 42,
  "successful_actions": 40,
  "failed_actions": 2,
  "error_count": 2
}
```

#### Get Configuration

```http
GET /agent/config
Authorization: Bearer <token>
```

Response:
```json
{
  "llm_providers": ["openai", "gemini", "anthropic"],
  "default_provider": "openai",
  "default_model": "gpt-4o",
  "safe_mode": true,
  "require_approval": false,
  "max_retries": 3,
  "screenshot_interval": 1.0
}
```

### Sessions

#### List Sessions

```http
GET /sessions?skip=0&limit=20
Authorization: Bearer <token>
```

Response:
```json
{
  "sessions": [
    {
      "id": "sess-123",
      "name": "Task Session",
      "status": "completed",
      "started_at": "2024-01-15T10:00:00Z",
      "ended_at": "2024-01-15T10:05:00Z"
    }
  ],
  "total": 1
}
```

#### Get Session Details

```http
GET /sessions/{session_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "sess-123",
  "name": "Task Session",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "ended_at": "2024-01-15T10:05:00Z",
  "duration_seconds": 300,
  "metadata": {}
}
```

#### Get Session Screenshots

```http
GET /sessions/{session_id}/screenshots
Authorization: Bearer <token>
```

Response:
```json
{
  "screenshots": [
    {
      "id": "shot-123",
      "file_path": "/screenshots/shot_123.png",
      "timestamp": "2024-01-15T10:01:00Z",
      "is_key_frame": true
    }
  ],
  "total": 5
}
```

#### Get Session Actions

```http
GET /sessions/{session_id}/actions
Authorization: Bearer <token>
```

Response:
```json
{
  "actions": [
    {
      "id": "act-123",
      "action_type": "mouse_click",
      "status": "success",
      "parameters": {"x": 100, "y": 200},
      "result": "Clicked successfully",
      "started_at": "2024-01-15T10:01:00Z",
      "duration_ms": 150
    }
  ],
  "total": 10
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to BuildAgent');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

### Messages

#### Run Task

```json
{
  "action": "run_task",
  "goal": "Open Chrome and navigate to Google",
  "session_id": "optional-id"
}
```

#### Get Status

```json
{
  "action": "get_status"
}
```

Response:
```json
{
  "type": "status",
  "data": {
    "status": "executing",
    "current_step": 2
  }
}
```

#### Control Execution

```json
{
  "action": "pause"
}
```

```json
{
  "action": "resume"
}
```

```json
{
  "action": "stop"
}
```

#### Get Screenshot

```json
{
  "action": "screenshot"
}
```

Response:
```json
{
  "type": "screenshot",
  "data": {
    "screenshot_path": "/screenshots/shot_123.png",
    "analysis": {...}
  }
}
```

### Event Types

| Event Type | Description |
|-----------|-------------|
| `task_started` | Task execution began |
| `observation` | Screen observation completed |
| `plan_created` | Action plan generated |
| `step_started` | Step execution began |
| `step_completed` | Step execution completed |
| `step_failed` | Step execution failed |
| `approval_required` | User approval needed |
| `verification` | Result verification |
| `task_completed` | Task execution completed |
| `task_failed` | Task execution failed |
| `status` | Agent status update |
| `screenshot` | Screenshot available |
| `final_result` | Final task result |

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "validation_error"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource conflict |
| 422 | Validation Error - Invalid data |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Rate Limiting

- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated endpoints
- WebSocket: 1 connection per user

## Pagination

List endpoints support pagination:

```http
GET /sessions?skip=0&limit=20
GET /sessions?skip=20&limit=20
```

Response includes:
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

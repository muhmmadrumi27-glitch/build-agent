# BuildAgent

A Production-Grade Autonomous Computer Use Agent capable of seeing the screen, understanding content, planning actions, and executing complex multi-step tasks with human-like behavior.

## Features

- **Vision System**: Real-time screen capture, UI element detection, layout analysis
- **OCR Engine**: Multi-language text recognition (English, Urdu, Arabic, Hindi)
- **Task Planner**: AI-powered action planning using LLM reasoning
- **Action Executor**: Human-like mouse/keyboard control, browser automation, desktop control
- **Memory System**: Vector-based memory with semantic search using ChromaDB
- **Security**: Permission system, audit logging, dangerous pattern detection, data masking
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Dashboard**: Real-time WebSocket communication, live screen preview

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   FastAPI       │     │   Agent Core    │
│   (Next.js)     │◄───►│   Backend       │◄───►│   (LangGraph)   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │PostgreSQL│          │  Redis  │          │ChromaDB │
   └─────────┘          └─────────┘          └─────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd build-agent
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the services**
   - API: http://localhost:8000
   - Frontend: http://localhost:3000
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Tasks
- `POST /api/v1/tasks` - Create and execute a task
- `POST /api/v1/tasks/{session_id}/actions` - Execute a single action
- `GET /api/v1/tasks/{session_id}/status` - Get task status
- `POST /api/v1/tasks/{session_id}/pause` - Pause execution
- `POST /api/v1/tasks/{session_id}/resume` - Resume execution
- `POST /api/v1/tasks/{session_id}/stop` - Stop execution

### Screen
- `GET /api/v1/screen/preview` - Get screen preview
- `POST /api/v1/screen/screenshot` - Take screenshot
- `POST /api/v1/screen/ocr` - Perform OCR
- `POST /api/v1/screen/analyze` - Analyze screen

### Memory
- `POST /api/v1/memory/query` - Query memories
- `GET /api/v1/memory/session/{session_id}` - Get session memories
- `DELETE /api/v1/memory/session/{session_id}` - Clear session memories

### Workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows/{id}/execute` - Execute workflow

### Agent
- `GET /api/v1/agent/status` - Get agent status
- `GET /api/v1/agent/config` - Get agent configuration
- `WS /ws` - WebSocket for real-time communication

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production) | `development` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GEMINI_API_KEY` | Gemini API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `SECRET_KEY` | JWT secret key | `change-me-in-production` |
| `SAFE_MODE` | Enable safe mode | `true` |
| `REQUIRE_APPROVAL` | Require approval for actions | `false` |

### LLM Providers

Supported providers:
- OpenAI (GPT-4o, GPT-4)
- Google Gemini (Gemini 1.5 Pro)
- Anthropic Claude (Claude 3.5 Sonnet)
- OpenRouter (multiple models)

## Security

### Features
- **Permission System**: Role-based access control (admin, user, viewer)
- **Audit Logging**: All actions logged with timestamps and details
- **Pattern Detection**: Blocks dangerous commands and file access
- **Data Masking**: Sensitive data masked in logs
- **Approval Mode**: Optional user approval for high-risk actions
- **Safe Mode**: Restricts destructive operations

### Security Levels
- `LOW`: Basic monitoring
- `MEDIUM`: Approval for file operations
- `HIGH`: Approval for all browser actions
- `CRITICAL`: Approval required for all actions

## Testing

```bash
cd backend
pytest
```

Run specific test suites:
```bash
pytest tests/test_vision.py -v
pytest tests/test_ocr.py -v
pytest tests/test_memory.py -v
pytest tests/test_planner.py -v
pytest tests/test_executor.py -v
pytest tests/test_security.py -v
```

## Monitoring

### Prometheus Metrics
- `buildagent_status` - Agent current status
- `buildagent_active_sessions` - Number of active sessions
- `buildagent_actions_total` - Total actions executed
- `buildagent_errors_total` - Total errors
- `buildagent_task_success_rate` - Task success rate
- `buildagent_response_duration_seconds` - API response times

### Grafana Dashboard
Access at http://localhost:3000 with default credentials `admin/admin`.

## Project Structure

```
build-agent/
├── backend/
│   ├── agents/
│   │   ├── executor/      # Action execution engine
│   │   ├── memory/        # Vector memory storage
│   │   ├── ocr/           # Text recognition
│   │   ├── planner/       # Task planning
│   │   ├── security/      # Security agent
│   │   └── vision/        # Screen analysis
│   ├── api/               # FastAPI routes
│   ├── database/          # SQLAlchemy models
│   ├── tests/             # Test suite
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   ├── security.py        # Security utilities
│   ├── agent.py           # Main agent orchestrator
│   ├── main.py            # API entry point
│   ├── requirements.txt   # Dependencies
│   ├── Dockerfile         # Backend container
│   └── .env.example       # Environment template
├── frontend/              # Next.js dashboard
├── docker/                # Docker configs
├── docker-compose.yml     # Full stack orchestration
└── README.md
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions, please open an issue on GitHub.

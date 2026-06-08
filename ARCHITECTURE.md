# Architecture Documentation

## System Overview

BuildAgent is a distributed system with the following architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │  Workflow    │  │   Settings   │      │
│  │   (React)    │  │   Builder    │  │    Panel     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │  WebSocket   │  │   Auth/JWT   │      │
│  │   REST API   │  │   Handler    │  │   Middleware │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Orchestrator                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Observer   │  │   Planner    │  │   Executor   │      │
│  │   (Vision)   │  │   (LLM)      │  │   (Actions)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Memory     │  │   Security   │  │   Recovery   │      │
│  │   Engine     │  │   Agent      │  │   Engine     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │   ChromaDB   │
│  (Relational)│    │    (Cache)   │    │  (Vector DB) │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Core Components

### 1. Vision Engine

**Purpose:** Screen capture and analysis

**Responsibilities:**
- Capture screenshots continuously
- Detect UI elements (buttons, fields, menus)
- Analyze layout and color schemes
- Detect text regions
- Compare screenshots for changes

**Technologies:**
- OpenCV (image processing)
- Pillow (image manipulation)
- Custom heuristics (UI detection)

**Data Flow:**
```
Screen ──► Screenshot ──► Analysis ──► UI Elements
                              │
                              ▼
                        OCR Text Regions
```

### 2. OCR Engine

**Purpose:** Text recognition from screen

**Responsibilities:**
- Read visible text
- Support multiple languages (EN, UR, AR, HI)
- Detect text regions and positions
- Extract form fields
- Detect language

**Technologies:**
- EasyOCR (primary)
- Tesseract OCR (fallback)
- Pillow (preprocessing)

**Data Flow:**
```
Image ──► Preprocessing ──► OCR ──► Text Regions
                          │
                          ▼
                    Language Detection
```

### 3. Task Planner

**Purpose:** Create action plans using LLM reasoning

**Responsibilities:**
- Break down goals into steps
- Generate action sequences
- Handle dependencies
- Create recovery plans
- Optimize plans

**Technologies:**
- LangChain (LLM framework)
- LangGraph (agent framework)
- OpenAI/Claude/Gemini (LLMs)

**Planning Cycle:**
```
Goal ──► Context Gathering ──► LLM Planning ──► Plan Validation
                                              │
                                              ▼
                                        Action Sequence
```

### 4. Action Executor

**Purpose:** Execute planned actions

**Responsibilities:**
- Mouse control (move, click, drag)
- Keyboard input (type, shortcuts)
- Browser automation (Playwright)
- Desktop automation (pyautogui)
- Application control
- Window management

**Technologies:**
- PyAutoGUI (desktop)
- Playwright (browser)
- Pynput (keyboard/mouse)
- PyGetWindow (window management)

**Execution Flow:**
```
Action ──► Security Check ──► Execute ──► Verify
                              │
                              ▼
                        Screenshot Before/After
```

### 5. Memory Engine

**Purpose:** Store and retrieve agent memories

**Responsibilities:**
- Store task history
- Store action results
- Store failures and recoveries
- Semantic search
- Session context

**Technologies:**
- ChromaDB (vector database)
- Sentence transformers (embeddings)

**Memory Types:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Tasks     │  │  Actions    │  │  Failures   │  │ Preferences │
│  (Success)  │  │  (Results)  │  │  (Recovery) │  │  (User)     │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

### 6. Security Agent

**Purpose:** Monitor and enforce security policies

**Responsibilities:**
- Evaluate action risk
- Detect dangerous patterns
- Control file access
- Filter URLs
- Manage approvals
- Audit logging

**Security Levels:**
```
LOW ──► MEDIUM ──► HIGH ──► CRITICAL
Basic   File Ops   Browser    All Actions
Monitoring Approval  Approval   Approval
```

## Data Flow

### Task Execution Flow

```
1. User Request
   │
   ▼
2. API Gateway (Auth, Validation)
   │
   ▼
3. Agent Orchestrator
   │
   ├──► 4. Observe (Screenshot + OCR + Vision)
   │
   ├──► 5. Plan (LLM-based planning)
   │
   ├──► 6. Execute (Action execution)
   │    │
   │    ├──► Security Check
   │    ├──► Execute Action
   │    └──► Verify Result
   │
   ├──► 7. Memory Store (Results)
   │
   └──► 8. Return Result
```

### WebSocket Real-time Flow

```
Client ──► WebSocket ──► Agent ──► Events
                              │
                              ├──► Task Started
                              ├──► Step Started
                              ├──► Step Completed
                              ├──► Screenshot
                              └──► Task Completed
```

## Database Schema

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    User      │       │   Session    │       │    Task      │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────┤ id (PK)      │◄──────┤ id (PK)      │
│ username     │       │ user_id (FK) │       │ session_id   │
│ email        │       │ name         │       │ name         │
│ password     │       │ status       │       │ status       │
│ role         │       │ started_at   │       │ goal         │
└──────────────┘       │ ended_at     │       │ result       │
                       └──────────────┘       └──────────────┘
                              │
                              │
                       ┌──────┴──────┐
                       │             │
                       ▼             ▼
                ┌──────────────┐ ┌──────────────┐
                │ Screenshot   │ │  Recording   │
                ├──────────────┤ ├──────────────┤
                │ id (PK)      │ │ id (PK)      │
                │ session_id   │ │ session_id   │
                │ file_path    │ │ file_path    │
                │ timestamp    │ │ duration     │
                └──────────────┘ └──────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Action     │       │  Workflow    │       │  AuditLog    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │       │ id (PK)      │
│ task_id (FK) │       │ user_id (FK) │       │ user_id      │
│ type         │       │ name         │       │ action_type  │
│ parameters   │       │ steps        │       │ details      │
│ status       │       │ variables    │       │ timestamp    │
│ result       │       │ tags         │       │ severity     │
└──────────────┘       └──────────────┘       └──────────────┘
```

## Communication Patterns

### Synchronous (REST API)

- Task creation
- Status queries
- Configuration changes
- Memory queries

### Asynchronous (WebSocket)

- Real-time task execution
- Screenshot streaming
- Event notifications
- Approval requests

### Message Queue (Redis)

- Task queueing
- Background jobs
- Event broadcasting
- Rate limiting

## Scalability

### Horizontal Scaling

```
┌──────────────┐
│  Load Balancer│
└──────────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌─────┐
│API 1│ │API 2│
└─────┘ └─────┘
   │       │
   └───┬───┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌─────┐
│DB 1 │ │DB 2 │
└─────┘ └─────┘
```

### Caching Strategy

| Data | Cache | TTL |
|------|-------|-----|
| Session status | Redis | 5 min |
| User preferences | Redis | 1 hour |
| Screen analysis | Redis | 1 min |
| Memory queries | ChromaDB | Persistent |
| Task plans | Redis | 30 min |

## Error Handling

### Error Recovery Flow

```
Action Failure
    │
    ▼
Retry (up to 3 times)
    │
    ├──► Success ──► Continue
    │
    └──► Failure ──► Analyze Error
                          │
                          ▼
                    Check Memory
                          │
                          ├──► Known Issue ──► Apply Recovery
                          │
                          └──► New Issue ──► LLM Replanning
                                                │
                                                ▼
                                          Alternative Strategy
```

## Monitoring

### Metrics Collection

```
Application ──► Prometheus ──► Grafana
    │
    ├──► Request Count
    ├──► Response Time
    ├──► Error Rate
    ├──► Active Sessions
    ├──► Action Success Rate
    └──► Resource Usage
```

### Alerting

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | > 10% errors | Warning |
| Agent Down | No heartbeat | Critical |
| Slow Response | p95 > 5s | Warning |
| Memory Full | > 90% usage | Critical |
| Disk Full | > 85% usage | Warning |

## Deployment Patterns

### Development

```
Single Machine
├── Docker Compose
├── Local Database
├── Local Redis
└── Local ChromaDB
```

### Production

```
Kubernetes Cluster
├── Multiple API Replicas
├── PostgreSQL HA
├── Redis Cluster
├── ChromaDB Cluster
├── Ingress Controller
└── Monitoring Stack
```

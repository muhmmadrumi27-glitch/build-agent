"""API routes for BuildAgent."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent import build_agent
from agents.memory.memory import memory_engine
from agents.vision.vision import vision_engine
from config import settings
from database import get_db
from database.models import (
    Action, ActionStatus, ActionType, AuditLog, MemoryEntry, Recording,
    Screenshot, SecurityLevel, Session, Task, TaskStatus, User, Workflow,
)
from security import PermissionManager, create_access_token, get_current_user

router = APIRouter()


# Pydantic models for requests/responses
class TaskRequest(BaseModel):
    goal: str = Field(..., description="Task goal description")
    session_id: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    require_approval: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    session_id: str
    goal: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ActionRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    require_approval: bool = False


class ActionResponse(BaseModel):
    success: bool
    action_type: str
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0


class MemoryQuery(BaseModel):
    query: str
    entry_type: Optional[str] = None
    n_results: int = 5


class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total: int


class ScreenPreview(BaseModel):
    screenshot_path: Optional[str]
    analysis: Dict[str, Any]
    text_preview: str
    timestamp: str


class AgentStatus(BaseModel):
    status: str
    current_task: Optional[str]
    current_step: Optional[int]
    session_id: Optional[str]
    total_actions: int
    successful_actions: int
    failed_actions: int


class WorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


# Task endpoints
@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create and execute a new task."""
    session_id = request.session_id or str(uuid.uuid4())

    result = await build_agent.run_task(
        goal=request.goal,
        session_id=session_id,
        user_id=current_user.get("sub"),
        llm_provider=request.llm_provider or settings.default_llm_provider,
        llm_model=request.llm_model or settings.default_llm_model,
        require_approval=request.require_approval,
    )

    return TaskResponse(
        session_id=session_id,
        goal=request.goal,
        status="completed" if result["success"] else "failed",
        result=result if result["success"] else None,
        error=result.get("error") if not result["success"] else None,
    )


@router.post("/tasks/{session_id}/actions")
async def execute_action(
    session_id: str,
    request: ActionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Execute a single action."""
    from agents.executor.executor import executor

    result = await executor.execute_action(
        action_type=request.action_type,
        parameters=request.parameters,
        session_id=session_id,
        require_approval=request.require_approval,
    )

    return ActionResponse(
        success=result.success,
        action_type=result.action_type,
        result=result.result,
        error=result.error,
        duration_ms=result.duration_ms,
    )


@router.get("/tasks/{session_id}/status")
async def get_task_status(session_id: str):
    """Get task execution status."""
    status = build_agent.get_status()
    return AgentStatus(**status)


@router.post("/tasks/{session_id}/pause")
async def pause_task(session_id: str):
    """Pause task execution."""
    build_agent.pause()
    return {"status": "paused", "session_id": session_id}


@router.post("/tasks/{session_id}/resume")
async def resume_task(session_id: str):
    """Resume task execution."""
    build_agent.resume()
    return {"status": "resumed", "session_id": session_id}


@router.post("/tasks/{session_id}/stop")
async def stop_task(session_id: str):
    """Stop task execution."""
    build_agent.stop()
    return {"status": "stopped", "session_id": session_id}


# Screen endpoints
@router.get("/screen/preview", response_model=ScreenPreview)
async def get_screen_preview():
    """Get current screen preview."""
    preview = await build_agent.get_screen_preview()
    return ScreenPreview(**preview)


@router.post("/screen/screenshot")
async def take_screenshot():
    """Take a screenshot."""
    _, path = vision_engine.capture_screenshot()
    return {"screenshot_path": path, "timestamp": datetime.utcnow().isoformat()}


@router.post("/screen/ocr")
async def perform_ocr(
    x: Optional[int] = None,
    y: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    languages: List[str] = Query(["en"]),
):
    """Perform OCR on screen or region."""
    import cv2
    from agents.ocr.ocr import ocr_engine

    img, _ = vision_engine.capture_screenshot(save=False)

    if all(v is not None for v in [x, y, width, height]):
        roi = img[y:y+height, x:x+width]
        regions = ocr_engine.read_text(roi, languages=languages)
    else:
        regions = ocr_engine.read_text(img, languages=languages)

    return {
        "text_regions": [r.to_dict() for r in regions],
        "full_text": " ".join(r.text for r in regions),
    }


@router.post("/screen/analyze")
async def analyze_screen():
    """Analyze current screen."""
    import cv2

    img, _ = vision_engine.capture_screenshot(save=False)
    analysis = vision_engine.analyze_image(img)

    return analysis


# Memory endpoints
@router.post("/memory/query", response_model=MemoryResponse)
async def query_memory(query: MemoryQuery):
    """Query agent memory."""
    memories = memory_engine.retrieve(
        query=query.query,
        entry_type=query.entry_type,
        n_results=query.n_results,
    )

    return MemoryResponse(
        memories=memories,
        total=len(memories),
    )


@router.get("/memory/session/{session_id}")
async def get_session_memory(session_id: str):
    """Get all memories for a session."""
    memories = memory_engine.get_session_context(session_id)
    return {"memories": memories, "total": len(memories)}


@router.delete("/memory/session/{session_id}")
async def clear_session_memory(session_id: str):
    """Clear memories for a session."""
    success = memory_engine.clear_session(session_id)
    return {"success": success, "session_id": session_id}


# Workflow endpoints
@router.post("/workflows")
async def create_workflow(
    request: WorkflowRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new workflow."""
    # In production, save to database
    workflow_id = str(uuid.uuid4())
    return {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "steps": request.steps,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/workflows")
async def list_workflows(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all workflows."""
    # In production, query from database
    return {"workflows": [], "total": 0}


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow."""
    # In production, query from database
    raise HTTPException(status_code=404, detail="Workflow not found")


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: WorkflowRequest,
):
    """Update a workflow."""
    # In production, update in database
    return {"id": workflow_id, "updated": True}


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    # In production, delete from database
    return {"id": workflow_id, "deleted": True}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    variables: Optional[Dict[str, Any]] = None,
):
    """Execute a workflow."""
    # In production, load workflow and execute
    return {"workflow_id": workflow_id, "status": "executing", "session_id": str(uuid.uuid4())}


# Agent status
@router.get("/agent/status")
async def get_agent_status():
    """Get current agent status."""
    return build_agent.get_status()


@router.get("/agent/config")
async def get_agent_config():
    """Get agent configuration."""
    return {
        "llm_providers": settings.available_llm_providers,
        "default_provider": settings.default_llm_provider,
        "default_model": settings.default_llm_model,
        "safe_mode": settings.safe_mode,
        "require_approval": settings.require_approval,
        "max_retries": settings.max_retries,
        "screenshot_interval": settings.screenshot_interval,
    }


# Session history
@router.get("/sessions")
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List agent sessions."""
    from sqlalchemy import select

    stmt = select(Session).offset(skip).limit(limit).order_by(Session.started_at.desc())
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": str(s.id),
                "name": s.name,
                "status": s.status.value,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get session details."""
    from sqlalchemy import select

    stmt = select(Session).where(Session.id == uuid.UUID(session_id))
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "name": session.name,
        "status": session.status.value,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "duration_seconds": session.duration_seconds,
        "metadata": session.metadata,
    }


@router.get("/sessions/{session_id}/screenshots")
async def get_session_screenshots(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get screenshots for a session."""
    from sqlalchemy import select

    stmt = select(Screenshot).where(Screenshot.session_id == uuid.UUID(session_id))
    result = await db.execute(stmt)
    screenshots = result.scalars().all()

    return {
        "screenshots": [
            {
                "id": str(s.id),
                "file_path": s.file_path,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                "is_key_frame": s.is_key_frame,
            }
            for s in screenshots
        ],
        "total": len(screenshots),
    }


@router.get("/sessions/{session_id}/actions")
async def get_session_actions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get actions for a session."""
    from sqlalchemy import select

    stmt = select(Action).where(Action.session_id == uuid.UUID(session_id)).order_by(Action.sequence_number)
    result = await db.execute(stmt)
    actions = result.scalars().all()

    return {
        "actions": [
            {
                "id": str(a.id),
                "action_type": a.action_type.value,
                "status": a.status.value,
                "parameters": a.parameters,
                "result": a.result,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "duration_ms": a.duration_ms,
            }
            for a in actions
        ],
        "total": len(actions),
    }

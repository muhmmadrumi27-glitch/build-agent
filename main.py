"""Main entry point for BuildAgent API server."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from agent import build_agent
from api.routes import router as api_router
from config import settings
from database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Production-Grade Autonomous Computer Use Agent",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication."""
    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_json()

            action = message.get("action")

            if action == "run_task":
                goal = message.get("goal", "")
                session_id = message.get("session_id")

                async for event in build_agent.stream_task(goal, session_id):
                    await websocket.send_json(event)

            elif action == "get_status":
                status = build_agent.get_status()
                await websocket.send_json({"type": "status", "data": status})

            elif action == "pause":
                build_agent.pause()
                await websocket.send_json({"type": "paused", "data": {}})

            elif action == "resume":
                build_agent.resume()
                await websocket.send_json({"type": "resumed", "data": {}})

            elif action == "stop":
                build_agent.stop()
                await websocket.send_json({"type": "stopped", "data": {}})

            elif action == "screenshot":
                preview = await build_agent.get_screen_preview()
                await websocket.send_json({"type": "screenshot", "data": preview})

            else:
                await websocket.send_json({"type": "error", "message": "Unknown action"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=1 if settings.api_reload else settings.api_workers,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )

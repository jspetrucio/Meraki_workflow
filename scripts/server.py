"""
FastAPI server for CNL (Conversational Network Language).

Serves REST API endpoints for:
- Discovery (network analysis)
- Configuration (SSIDs, VLANs, firewall, ACLs)
- Workflows (automation tasks)
- Reports (HTML/PDF generation)
- Profiles (Meraki credential management)
- Settings (application configuration)

Usage:
    from scripts.server import app, run_server

    # Start server
    run_server(host="127.0.0.1", port=3141)

    # Or with uvicorn directly
    uvicorn scripts.server:app --host 127.0.0.1 --port 3141
"""

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from scripts import __version__
from scripts.settings import SettingsManager
from scripts.auth import CredentialsNotFoundError, InvalidProfileError
from scripts.workflow import WorkflowError, WorkflowValidationError
from scripts.chat_session import SessionManager
from scripts.agent_router import process_message, classify_intent
from scripts.ai_engine import AIEngine

# Import routers
from scripts.settings_routes import router as settings_router
from scripts.profile_routes import router as profiles_router
from scripts.discovery_routes import router as discovery_router
from scripts.config_routes import router as config_router
from scripts.workflow_routes import router as workflow_router
from scripts.report_routes import router as report_router
from scripts.n8n_routes import router as n8n_router

logger = logging.getLogger(__name__)

# Server start time for uptime tracking
_start_time: float = 0.0

# Global session manager for WebSocket chat
_session_manager: SessionManager = SessionManager()

# Global AI engine instance (initialized on startup)
_ai_engine: Optional[AIEngine] = None


# ==================== Response Models ====================


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float


class StatusResponse(BaseModel):
    """Connection status response."""
    meraki_connected: bool
    meraki_profile: str
    ai_configured: bool
    ai_provider: Optional[str]
    n8n_connected: bool


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str
    code: str


# ==================== FastAPI App ====================


app = FastAPI(
    title="CNL",
    version=__version__,
    description="Conversational Network Language API Server"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3141",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3141",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Exception Handlers ====================


@app.exception_handler(CredentialsNotFoundError)
async def credentials_not_found_handler(request: Request, exc: CredentialsNotFoundError):
    """Handle credentials not found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "credentials_not_found",
            "detail": str(exc),
            "code": "CRED_NOT_FOUND"
        }
    )


@app.exception_handler(InvalidProfileError)
async def invalid_profile_handler(request: Request, exc: InvalidProfileError):
    """Handle invalid profile errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_profile",
            "detail": str(exc),
            "code": "INVALID_PROFILE"
        }
    )


@app.exception_handler(WorkflowError)
async def workflow_error_handler(request: Request, exc: WorkflowError):
    """Handle workflow errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "workflow_error",
            "detail": str(exc),
            "code": "WORKFLOW_ERROR"
        }
    )


@app.exception_handler(WorkflowValidationError)
async def workflow_validation_error_handler(request: Request, exc: WorkflowValidationError):
    """Handle workflow validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "workflow_validation_error",
            "detail": str(exc),
            "code": "WORKFLOW_VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with safe error message."""
    # Import here to avoid circular dependency
    import meraki.exceptions

    # Special handling for Meraki API errors
    if isinstance(exc, meraki.exceptions.APIError):
        return JSONResponse(
            status_code=502,
            content={
                "error": "meraki_api_error",
                "detail": str(exc),
                "code": "MERAKI_API_ERROR"
            }
        )

    # Generic error - don't expose internal details
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An internal error occurred. Please check server logs.",
            "code": "INTERNAL_ERROR"
        }
    )


# ==================== Startup/Shutdown Events ====================


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    global _start_time, _ai_engine
    _start_time = time.time()

    logger.info(f"CNL Server v{__version__} starting")
    logger.info(f"Server started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Load settings
    manager = SettingsManager()
    settings = manager.load()
    logger.info(f"Settings loaded - Port: {settings.port}, Profile: {settings.meraki_profile}")

    # Initialize AI engine if configured
    if settings.ai_api_key:
        try:
            _ai_engine = AIEngine(settings)
            logger.info(f"AI Engine initialized: {settings.ai_provider}/{settings.ai_model}")
        except Exception as exc:
            logger.warning(f"Failed to initialize AI Engine: {exc}")
            _ai_engine = None
    else:
        logger.info("AI Engine not configured (no API key)")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    uptime = time.time() - _start_time
    logger.info(f"CNL Server shutting down after {uptime:.2f}s uptime")


# ==================== Health Endpoints ====================


@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns server status, version, and uptime.
    """
    return HealthResponse(
        status="ok",
        version=__version__,
        uptime_seconds=time.time() - _start_time
    )


@app.get("/api/v1/status", response_model=StatusResponse, tags=["health"])
async def status_check():
    """
    Connection status check.

    Returns status of Meraki, AI provider, and N8N connections.
    """
    manager = SettingsManager()
    settings = manager.load()

    # Check Meraki connection
    meraki_connected = False
    meraki_profile = settings.meraki_profile
    try:
        from scripts.auth import load_profile, validate_credentials
        profile = load_profile(meraki_profile)
        meraki_connected, _ = validate_credentials(profile)
    except Exception:
        pass

    # Check AI configuration
    ai_configured = bool(settings.ai_api_key)
    ai_provider = settings.ai_provider if ai_configured else None

    # Check N8N connection
    n8n_connected = False
    if settings.n8n_enabled and settings.n8n_url:
        try:
            n8n_connected, _ = manager.validate_n8n_connection(
                settings.n8n_url,
                settings.n8n_api_key
            )
        except Exception:
            pass

    return StatusResponse(
        meraki_connected=meraki_connected,
        meraki_profile=meraki_profile,
        ai_configured=ai_configured,
        ai_provider=ai_provider,
        n8n_connected=n8n_connected
    )


# ==================== WebSocket Connection Manager ====================


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, session_id: str, websocket: WebSocket):
        """
        Accept and register a WebSocket connection.

        Args:
            session_id: Session identifier
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: session={session_id}, total={len(self.active_connections)}")

    def disconnect(self, session_id: str):
        """
        Disconnect and remove a WebSocket connection.

        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            self.active_connections.pop(session_id)
            logger.info(f"WebSocket disconnected: session={session_id}, remaining={len(self.active_connections)}")

    async def send_to(self, session_id: str, data: dict):
        """
        Send data to a specific session.

        Args:
            session_id: Session identifier
            data: Data to send (will be JSON-encoded)
        """
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(data)

    async def broadcast(self, data: dict):
        """
        Broadcast data to all connected sessions.

        Args:
            data: Data to send (will be JSON-encoded)
        """
        for ws in self.active_connections.values():
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"Failed to broadcast to connection: {exc}")

    def get_active_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
_connection_manager = ConnectionManager()


# ==================== WebSocket Endpoint ====================


def _validate_origin(websocket: WebSocket) -> bool:
    """
    Validate WebSocket origin header.

    Only accepts connections from localhost origins for security.

    Args:
        websocket: WebSocket connection

    Returns:
        True if origin is allowed, False otherwise
    """
    origin = websocket.headers.get("origin", "")

    # Allow localhost and 127.0.0.1 on any port
    allowed_origins = [
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "https://127.0.0.1",
    ]

    # Check if origin starts with any allowed prefix
    for allowed in allowed_origins:
        if origin.startswith(allowed):
            return True

    # Also allow missing origin (for testing)
    if not origin:
        return True

    logger.warning(f"Rejected WebSocket connection from origin: {origin}")
    return False


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Protocol:
        Client → Server:
            {"type": "message", "content": "...", "session_id": "..."}
            {"type": "confirm_response", "request_id": "...", "approved": bool}
            {"type": "cancel"}
            {"type": "ping"}

        Server → Client:
            {"type": "stream", "chunk": "...", "agent": "..."}
            {"type": "data", "format": "...", "data": {...}, "agent": "..."}
            {"type": "classification", "agent": "...", "confidence": 0.95, "reasoning": "..."}
            {"type": "agent_status", "agent": "...", "status": "thinking|executing|done"}
            {"type": "error", "message": "...", "code": "..."}
            {"type": "done", "agent": "...", "session_id": "..."}
            {"type": "pong"}
    """
    # Validate origin
    if not _validate_origin(websocket):
        await websocket.close(code=1008, reason="Invalid origin")
        return

    session_id: Optional[str] = None

    try:
        # Accept connection (will be registered with session_id later)
        await websocket.accept()

        # Main message loop
        while True:
            # Receive message
            try:
                raw = await websocket.receive_json()
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "code": "INVALID_JSON"
                })
                continue

            msg_type = raw.get("type")

            # Handle ping/pong
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # Handle message
            elif msg_type == "message":
                content = raw.get("content", "").strip()
                session_id = raw.get("session_id") or str(uuid.uuid4())

                # Input validation
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message",
                        "code": "EMPTY_MESSAGE"
                    })
                    continue

                # Limit message length
                if len(content) > 5000:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message too long (max 5000 chars)",
                        "code": "MESSAGE_TOO_LONG"
                    })
                    continue

                # Register connection with session_id if not already done
                if session_id not in _connection_manager.active_connections:
                    _connection_manager.active_connections[session_id] = websocket
                    logger.info(f"Registered WebSocket for session {session_id}")

                # Get or create session
                session = _session_manager.get_session(session_id)
                if not session:
                    session = _session_manager.create_session(session_id)

                # Add user message to session
                session.add_message(role="user", content=content)

                # Send thinking status
                await websocket.send_json({
                    "type": "agent_status",
                    "agent": "system",
                    "status": "thinking"
                })

                # Process message via agent router
                if _ai_engine:
                    try:
                        # Get session context
                        context = session.get_context(max_messages=20)

                        # Process message with streaming
                        async for chunk in process_message(
                            message=content,
                            session_id=session_id,
                            ai_engine=_ai_engine,
                            session_context=context
                        ):
                            await websocket.send_json(chunk)

                            # If this is a stream chunk, accumulate for assistant message
                            if chunk.get("type") == "stream":
                                # TODO: Accumulate chunks for final assistant message
                                pass

                    except Exception as exc:
                        logger.exception("Error processing message")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Processing failed: {type(exc).__name__}",
                            "code": "PROCESSING_ERROR"
                        })
                else:
                    # No AI engine configured - send stub response
                    await websocket.send_json({
                        "type": "stream",
                        "chunk": "AI Engine not configured. Please set your API key in settings.",
                        "agent": "system"
                    })

                # Send done
                await websocket.send_json({
                    "type": "done",
                    "agent": "system",
                    "session_id": session_id
                })

            # Handle cancel
            elif msg_type == "cancel":
                # TODO: Implement cancellation logic
                await websocket.send_json({
                    "type": "done",
                    "cancelled": True,
                    "agent": "system"
                })

            # Handle confirmation response
            elif msg_type == "confirm_response":
                # TODO: Implement confirmation flow
                request_id = raw.get("request_id")
                approved = raw.get("approved", False)

                logger.info(f"Confirmation response: request_id={request_id}, approved={approved}")

                # For now, just acknowledge
                await websocket.send_json({
                    "type": "stream",
                    "chunk": f"Confirmation {'approved' if approved else 'denied'}",
                    "agent": "system"
                })

            # Unknown message type
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                    "code": "UNKNOWN_MESSAGE_TYPE"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as exc:
        logger.exception("Unexpected error in WebSocket handler")
    finally:
        # Clean up connection
        if session_id:
            _connection_manager.disconnect(session_id)


# ==================== Mount Routers ====================


app.include_router(settings_router)    # /api/v1/settings/*
app.include_router(profiles_router)    # /api/v1/profiles/*
app.include_router(discovery_router)   # /api/v1/discovery/*
app.include_router(config_router)      # /api/v1/config/*
app.include_router(workflow_router)    # /api/v1/workflows/*
app.include_router(report_router)      # /api/v1/reports/*
app.include_router(n8n_router)         # /api/v1/n8n/*


# ==================== Static Files (Production React Build) ====================


frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    logger.info(f"Static files mounted from {frontend_dist}")


# ==================== Server Runner ====================


def run_server(host: str = "127.0.0.1", port: Optional[int] = None):
    """
    Start the CNL server.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: from settings or 3141)
    """
    if port is None:
        manager = SettingsManager()
        settings = manager.load()
        port = settings.port

    logger.info(f"Starting CNL server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


# ==================== Main ====================


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Simple CLI parsing
    host = "127.0.0.1"
    port = None

    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    run_server(host=host, port=port)

"""API module for REST and WebSocket endpoints."""

from .server import app
from .websocket import setup_websocket_routes, manager, broadcast_cognitive_state, broadcast_decision, broadcast_telemetry, broadcast_alert

__all__ = [
    "app",
    "setup_websocket_routes",
    "manager",
    "broadcast_cognitive_state",
    "broadcast_decision",
    "broadcast_telemetry",
    "broadcast_alert"
]


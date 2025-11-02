"""
WebSocket server for real-time streaming of cognitive states and decisions.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] New connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        self.active_connections.remove(websocket)
        print(f"[WS] Connection closed. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[WS] Error sending personal message: {e}")


# Global manager instance
manager = ConnectionManager()


def setup_websocket_routes(app):
    """Add WebSocket routes to FastAPI app."""
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        Main WebSocket endpoint for streaming updates.
        
        Clients can send commands and receive:
        - Cognitive state updates
        - Decision notifications
        - Telemetry data
        """
        await manager.connect(websocket)
        
        try:
            # Send welcome message
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "message": "Connected to MindAware Agent stream"
            })
            
            # Listen for client messages
            while True:
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    command = message.get("command")
                    
                    if command == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        })
                    
                    elif command == "subscribe":
                        channel = message.get("channel", "all")
                        await websocket.send_json({
                            "type": "subscribed",
                            "channel": channel
                        })
                    
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown command: {command}"
                        })
                
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON"
                    })
        
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            print(f"[WS] Error in websocket: {e}")
            manager.disconnect(websocket)


async def broadcast_cognitive_state(state: dict):
    """Broadcast a cognitive state update to all clients."""
    await manager.broadcast({
        "type": "cognitive_state",
        "data": state
    })


async def broadcast_decision(decision: dict):
    """Broadcast an agent decision to all clients."""
    await manager.broadcast({
        "type": "decision",
        "data": decision
    })


async def broadcast_telemetry(telemetry: dict):
    """Broadcast drone telemetry to all clients."""
    await manager.broadcast({
        "type": "telemetry",
        "data": telemetry
    })


async def broadcast_alert(alert: dict):
    """Broadcast an alert to all clients."""
    await manager.broadcast({
        "type": "alert",
        "data": alert
    })


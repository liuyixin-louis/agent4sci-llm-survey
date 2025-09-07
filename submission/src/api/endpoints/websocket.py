"""
WebSocket endpoint for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, survey_id: str):
        await websocket.accept()
        if survey_id not in self.active_connections:
            self.active_connections[survey_id] = []
        self.active_connections[survey_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, survey_id: str):
        if survey_id in self.active_connections:
            self.active_connections[survey_id].remove(websocket)
    
    async def broadcast(self, survey_id: str, message: dict):
        if survey_id in self.active_connections:
            for connection in self.active_connections[survey_id]:
                await connection.send_json(message)

manager = ConnectionManager()


@router.websocket("/{survey_id}")
async def websocket_endpoint(websocket: WebSocket, survey_id: str):
    """WebSocket endpoint for real-time survey generation updates."""
    await manager.connect(websocket, survey_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to survey {survey_id}",
            "survey_id": survey_id
        })
        
        # Keep connection alive and send periodic updates
        while True:
            # In production, would send actual progress updates
            await asyncio.sleep(5)
            await websocket.send_json({
                "type": "progress",
                "survey_id": survey_id,
                "progress": 50,
                "message": "Survey generation in progress..."
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, survey_id)
        print(f"Client disconnected from survey {survey_id}")
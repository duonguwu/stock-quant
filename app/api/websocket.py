"""WebSocket connection manager for real-time dashboard updates"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "user_id": user_id or "anonymous",
            "connected_at": asyncio.get_event_loop().time(),
            "message_count": 0
        }
        
        logger.info(f"New WebSocket connection: {user_id or 'anonymous'}")
        logger.info(f"Total active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            user_info = self.connection_info.pop(websocket)
            logger.info(f"WebSocket disconnected: {user_info.get('user_id')}")
        
        logger.info(f"Total active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            
            # Update message count
            if websocket in self.connection_info:
                self.connection_info[websocket]["message_count"] += 1
                
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message)
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
                
                # Update message count
                if connection in self.connection_info:
                    self.connection_info[connection]["message_count"] += 1
                    
            except WebSocketDisconnect:
                logger.warning("WebSocket disconnect during broadcast")
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        if disconnected_connections:
            logger.info(f"Cleaned up {len(disconnected_connections)} disconnected connections")
    
    async def broadcast_to_group(self, message: Dict[str, Any], group_filter: callable = None):
        """Broadcast message to specific group of connections"""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message)
        disconnected_connections = []
        sent_count = 0
        
        for connection in self.active_connections:
            # Apply group filter if provided
            if group_filter and not group_filter(self.connection_info.get(connection, {})):
                continue
                
            try:
                await connection.send_text(message_text)
                sent_count += 1
                
                # Update message count
                if connection in self.connection_info:
                    self.connection_info[connection]["message_count"] += 1
                    
            except WebSocketDisconnect:
                logger.warning("WebSocket disconnect during group broadcast")
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to group connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        logger.debug(f"Group broadcast sent to {sent_count} connections")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self.active_connections),
            "connection_details": [
                {
                    "user_id": info.get("user_id"),
                    "connected_duration": asyncio.get_event_loop().time() - info.get("connected_at", 0),
                    "message_count": info.get("message_count", 0)
                }
                for info in self.connection_info.values()
            ]
        }
    
    async def send_heartbeat(self):
        """Send heartbeat to all connections to keep them alive"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": asyncio.get_event_loop().time(),
            "connections": len(self.active_connections)
        }
        await self.broadcast(heartbeat_message)
    
    async def cleanup_stale_connections(self, max_age_seconds: int = 3600):
        """Remove connections that have been idle for too long"""
        current_time = asyncio.get_event_loop().time()
        stale_connections = []
        
        for connection, info in self.connection_info.items():
            if current_time - info.get("connected_at", 0) > max_age_seconds:
                stale_connections.append(connection)
        
        for connection in stale_connections:
            try:
                await connection.close()
            except Exception:
                pass
            self.disconnect(connection)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections") 
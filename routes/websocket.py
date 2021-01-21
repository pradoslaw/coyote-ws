from fastapi import APIRouter, WebSocket, Query, Depends, WebSocketDisconnect, status
from typing import Optional, List
from client import Client
import logging

router = APIRouter()

async def get_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    return token

active_connections: List[WebSocket] = []

@router.websocket("/realtime")
async def index(websocket: WebSocket, token: str = Depends(get_token)):
    await websocket.accept()

    client = Client(websocket)

    active_connections.append(websocket)
    logging.info('Client connected. Number of clients: %d' % len(active_connections))

    try:
        await client.authorize(token)

        while True:
            message = await websocket.receive_text()
            logging.info('Message from websocket client: %s' % message)

            await client.handle_message(message)
    except Exception:
        await websocket.close(code=1000)

        await client.unsubscribe()
        active_connections.remove(websocket)

        del client

        logging.info('Client disconnected')
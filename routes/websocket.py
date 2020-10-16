from fastapi import APIRouter, WebSocket, Query, Depends, WebSocketDisconnect, status
from typing import Optional, List
from utils.redis import redis_connection
from utils.crypt import jwt_decode
from utils.types import ChannelNames
from aioredis.pubsub import Receiver
import asyncio
import aioredis
import logging
import os
import json

router = APIRouter()

async def get_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    return token

def is_valid_json(message):
    try:
        obj = json.loads(message)
    except ValueError:
        return False

    return obj

class Client:
    def __init__(self, websocket: WebSocket):
        self._websocket = websocket
        self._redis = None
        self._channel_names: ChannelNames = []
        self._receiver = Receiver()

    def __del__(self):
        logging.info('Closing connection')

    async def authorize(self, token: str):
        try:
            self._channel_names = jwt_decode(token)

            logging.info('Client authenticated. Channel name: %s' % self._channel_names)

            await self.subscribe()
        except Exception as e:
            logging.warning('Invalid token: %s. Error: %s.' % (token, str(e)))

            await self._websocket.close(403)

    async def publish(self, channel_name: str, data: str):
        pub_connection = await redis_connection()

        await pub_connection.publish(channel_name, data)

    async def subscribe(self):
        """
        Subscribe to Redis channel and if - event occurs - pass data to the client by calling websocket method

        :return:
        """
        self._redis = await aioredis.create_redis((os.environ['REDIS_HOST'], 6379))

        async def reader():
            async for channel, message in self._receiver.iter():
                logging.info(message)

                await self._websocket.send_text(message.decode('utf-8'))

        asyncio.ensure_future(reader())

        await self._redis.subscribe(
            *[self._receiver.channel(channel) for channel in self._channel_names]
        )

    async def unsubscribe(self):
        if self._channel_names:
            await self._redis.unsubscribe(*self._channel_names)

        self._channel_names = []
        self._redis.close()

        self._redis = None

        logging.info('Unsubscribed')


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

            if not (data := is_valid_json(message)):
                continue

            channel_name = data.pop('channel')

            await client.publish(channel_name, json.dumps(data))
    except WebSocketDisconnect:
        logging.info('Client disconnected')

        active_connections.remove(websocket)

        await client.unsubscribe()

        del client
import asyncio
import tornado.websocket
import tornado.ioloop
import logging
import json
from utils.redis import redis_connection
from utils.crypt import jwt_decode
from utils.types import ChannelNames
from aioredis.pubsub import Receiver
from . import clients
import aioredis
import os

def is_valid_json(message):
    try:
        obj = json.loads(message)
    except ValueError:
        return False

    return obj


class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.redis = None
        self.channel_names = []
        self.receiver = Receiver()

    def __del__(self):
        logging.info('Removing client')

    def check_origin(self, origin):
        return True

    async def subscribe(self, channel_names: ChannelNames):
        """
        Subscribe to Redis channel and if - event occurs - pass data to the client by calling emit_message() method

        :return:
        """
        self.redis = await aioredis.create_redis((os.environ['REDIS_HOST'], 6379))

        async def reader():
            async for channel, message in self.receiver.iter():
                self.emit_message(message)

        asyncio.ensure_future(reader())

        await self.redis.subscribe(
            *[self.receiver.channel(channel) for channel in channel_names]
        )

        self.channel_names = channel_names

    async def unsubscribe(self):
        await self.redis.unsubscribe(*self.channel_names)

        self.channel_names = []
        self.redis.close()

        self.redis = None

    async def publish(self, channel_name: str, data: str):
        pub_connection = await redis_connection()

        await pub_connection.publish(channel_name, data)

    def open(self, *args):
        clients.add(self)

        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), clients.__len__()))

        token = self.get_argument('token')

        try:
            channel_names = jwt_decode(token)
            logging.info('Client authenticated. Channel name: %s' % channel_names)

            asyncio.create_task(self.subscribe(channel_names))
        except Exception as e:
            logging.warning('Invalid token: %s. Error: %s.' % (token, str(e)))

            self.close()

    def on_pong(self, data: bytes) -> None:
        logging.debug('Pong from websocket client: %s' % str(data))

    def on_message(self, message: str):
        """
        Raw message from websocket client.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

        if not (data := is_valid_json(message)):
            return

        try:
            channel_name = data.pop('channel')
            asyncio.create_task(self.publish(channel_name, json.dumps(data)))
        except KeyError as e:
            logging.error(str(e))

    def emit_message(self, message: str):
        """
        Send data to websocket client

        :param message:
        :return:
        """
        logging.info(message)

        # send data to client
        self.write_message(message)

    def on_close(self):
        if self.channel_names and hasattr(self.redis, 'unsubscribe'):
            asyncio.create_task(self.unsubscribe())

            logging.info('Unsubscribed')

        logging.info('Connection closed')

        clients.remove(self)


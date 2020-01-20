import aioredis
import asyncio
import tornado.web
import tornado.websocket
import tornado.ioloop
import logging
import json
from utils.redis import redis_connection
from utils.crypt import jwt_decode

# global array of clients...
clients = []

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.redis = None
        self.channel_name = None

    def check_origin(self, origin):
        return True

    async def subscribe(self, channel_name):
        self.redis = await redis_connection()

        await self.redis.subscribe(channel_name)
        channel = self.redis.channels[channel_name]

        self.channel_name = channel_name

        while await channel.wait_message():
            message = await channel.get()

            self.emit_message(message)

    async def unsubscribe(self):
        await self.redis.unsubscribe(self.channel_name)

    async def publish(self, channel_name, data):
        await self.redis.publish(channel_name, data)

    def open(self, *args):
        clients.append(self)
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), clients.__len__()))

        token = self.get_argument('token')

        try:
            channel_name = jwt_decode(token)
            logging.info('Client authenticated. Channel name: %s' % channel_name)

            asyncio.create_task(self.subscribe(channel_name))

            self.heartbeat()
        except Exception as e:
            logging.warning('Invalid token: %s. Error: %s.' % (token, str(e)))

            self.close()

    def heartbeat(self):
        """
        Send heartbeat every 1 minutes.
        :return:
        """
        try:
            logging.info('Sending heartbeat...')

            self.ping(json.dumps({'event': 'hb', 'data': 'hb'}))
        except tornado.websocket.WebSocketClosedError as err:
            logging.warning('Websocket closed when sending message.' + str(err))
        finally:
            loop = asyncio.get_event_loop()
            loop.call_later(60, self.heartbeat)

    def on_pong(self, data: bytes) -> None:
        logging.info('Pong from websocket client: %s' % str(data))

    def on_message(self, message):
        """
        Raw message from websocket client.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

        if not (data := self.__is_valid_json(message)):
            return

        try:
            channel_name = data.pop('channel')
            asyncio.create_task(self.publish(channel_name, json.dumps(data)))
        except KeyError as e:
            logging.error(str(e))

    def emit_message(self, message):
        """
        Send data to websocket client

        :param message:
        :return:
        """
        logging.info(message)

        # send data to client
        self.write_message(message.decode('ascii'))

    def on_close(self):
        if self.channel_name and hasattr(self.redis, 'unsubscribe'):
            asyncio.create_task(self.unsubscribe())

            logging.info('Unsubscribed')

        clients.remove(self)

        logging.info('Connection closed')

    def __is_valid_json(self, message):
        try:
            obj = json.loads(message)
        except ValueError:
            return False

        return obj
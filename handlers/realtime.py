import aioredis
import asyncio
import tornado.web
import tornado.websocket
import tornado.ioloop
import utils.crypt as crypt
import logging
import datetime
import json
import os
from aioredis.pubsub import Receiver

# global array of clients...
clients = []

redis_pool = None

async def redis_connection():
    global redis_pool

    if not redis_pool:
        redis_pool = await aioredis.create_redis_pool('redis://redis')

    return redis_pool

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.channel = '' # channel name
        self.redis = None

    def check_origin(self, origin):
        return True

    async def listen(self):
        self.redis = await redis_connection()

        await self.redis.subscribe(self.channel)
        channel = self.redis.channels[self.channel]

        while await channel.wait_message():
            message = await channel.get()

            self.emit_message(message)

    def open(self, *args):
        clients.append(self)
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), clients.__len__()))

        token = self.get_argument('token')

        try:
            channel = crypt.jwt_decode(token)

            self.channel = channel
            logging.info('Client authenticated. Channel name: %s' % self.channel)

            asyncio.create_task(self.listen())

            self.heartbeat()
        except Exception as e:
            logging.warning('Invalid token: %s. Error: %s. Signature: %s' % (token, str(e), os.environ['APP_KEY']))
            self.close()

    def heartbeat(self):
        """
        Send heartbeat every 5 minutes.
        :return:
        """
        try:
            logging.info('Sending heartbeat...')

            self.write_message(json.dumps({'event': 'hb', 'data': 'hb'}))
        except tornado.websocket.WebSocketClosedError as err:
            logging.warning('Websocket closed when sending message.' + str(err))

        tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.heartbeat)

    def on_message(self, message):
        """
        Raw message from websocket client. We can just ignore it.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

        try:
            result = json.loads(message)

            if result['event'][0:7] == 'client-':
                # result.pop('channel')
                # result.pop('event')

                asyncio.create_task(self.whisper(result['channel'], result['event'][7:], result))

        except Exception as e:
            logging.warning(str(e))

    async def whisper(self, channel, event, data):
        await self.redis.publish(channel, json.dumps({'event': event, 'data': data}))

    def emit_message(self, message):
        """
        Event subscribe

        :param message:
        :return:
        """
        logging.info(message)

        # send data to client
        self.write_message(message.decode('ascii'))

    def on_close(self):
        logging.info('Connection closed')

        if hasattr(self.redis, 'subscribed'):
            asyncio.create_task(self.redis.unsubscribe(self.channel))

        self.redis = None
        clients.remove(self)
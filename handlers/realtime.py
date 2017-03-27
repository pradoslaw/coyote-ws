import tornadoredis
import tornado.web
import tornado.websocket
import tornado.ioloop
import utils.crypt as crypt
import logging
import time
import datetime
import json
from phpserialize import loads, dumps
import urllib
import os

# global array of clients...
clients = []

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.channel = '' # channel name
        self.client = None
        self.session_id = None

    def check_origin(self, origin):
        return True

    @tornado.gen.engine
    def listen(self):
        yield tornado.gen.Task(self.client.subscribe, self.channel)
        self.client.listen(self.on_event)

    @tornado.gen.engine
    def open(self, *args):
        clients.append(self)
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), clients.__len__()))

        cookie = self.get_cookie(os.environ['COOKIE'])

        if not cookie:
            self.close()
            return

        session_id = crypt.decrypt(urllib.unquote(cookie).decode('utf8'))

        self.client = tornadoredis.Client()
        self.client.connect()

        payload = yield tornado.gen.Task(self.client.get, session_id)

        if payload is None:
            logging.error('Session does not exist: %s' % session_id)
            self.close()

            return

        data = loads(payload)

        self.channel = 'user:%d' % data['user_id'] if 'user_id' in data and data['user_id'] is not None else None
        self.session_id = session_id

        logging.info('Client authenticated. Channel name: %s' % self.channel)

        if self.channel:
            self.listen()

        tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.heartbeat)

    def heartbeat(self):
        """
        Send heartbeat every 5 minutes.
        :return:
        """
        if hasattr(self.client, 'subscribed'):
            try:
                logging.info('Sending heartbeat...')
                self.write_message(json.dumps({'event': 'hb', 'data': 'hb'}))
            except tornado.websocket.WebSocketClosedError:
                logging.warning('Websocket closed when sending message.')

                self.close()

            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.heartbeat)

    @tornado.gen.engine
    def on_message(self, message):
        """
        Raw message from websocket client.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

        client = tornadoredis.Client()
        client.connect()

        payload = yield tornado.gen.Task(client.get, self.session_id)
        data = loads(payload)

        # update last activity timestamp
        data['updated_at'] = time.time()

        yield tornado.gen.Task(client.set, self.session_id, dumps(data))
        client.disconnect()

    def on_event(self, message):
        """
        Event subscribe

        :param message:
        :return:
        """
        logging.info(message)

        if hasattr(message, 'kind') and message.kind == 'message':
            # send data to client
            self.write_message(str(message.body))

    def on_close(self):
        logging.info('Connection closed')

        if hasattr(self.client, 'subscribed') and self.channel is not None:
            self.client.unsubscribe(self.channel)
            self.client.disconnect()

        self.client = None

        if self in clients:
            clients.remove(self)
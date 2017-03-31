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

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.listener = None # redis instance
        self.channel = None
        self.session_id = None

    def check_origin(self, origin):
        return True

    @property
    def redis(self):
        return self.settings['redis']

    @property
    def clients(self):
        return self.settings['clients']

    @clients.setter
    def clients(self, value):
        self.settings['clients'] = value

    @tornado.gen.engine
    def listen(self):
        if not self.channel:
            return

        self.listener = tornadoredis.Client()
        self.listener.connect()

        yield tornado.gen.Task(self.listener.subscribe, self.channel)
        self.listener.listen(self.on_event)

    @tornado.gen.engine
    def open(self, *args):
        self.clients += 1
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), self.clients))

        cookie = self.get_cookie(os.environ['COOKIE'])

        if not cookie:
            logging.info('No cookie provided.')
            self.send_exit()
            return

        session_id = crypt.decrypt(urllib.unquote(cookie).decode('utf8'))
        payload = yield tornado.gen.Task(self.redis.hget, 'sessions', session_id)

        if payload is None:
            logging.info('Session does not exist: %s' % session_id)
            self.send_exit()

            return

        try:
            data = loads(payload)

            self.channel = 'user:%d' % data['user_id'] if 'user_id' in data and data['user_id'] is not None else None
            self.session_id = session_id

            logging.info('Client authenticated. Channel name: %s' % self.channel)

            self.listen()

            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.send_heartbeat)
        except ValueError:
            logging.warning('Can not unserialize PHP object')

    def send_heartbeat(self):
        """
        Send heartbeat every 1 minutes.
        :return:
        """
        try:
            logging.info('Sending heartbeat...')
            self.write_message(json.dumps({'event': 'hb', 'data': 'hb'}))

            # MUST BE send every 1 minutes so proxy (nginx) can keep connection alive
            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.send_heartbeat)
        except tornado.websocket.WebSocketClosedError:
            logging.warning('Websocket closed when sending message.')

            self.close()

    def send_exit(self):
        try:
            logging.info('Send signal to give up...')
            self.write_message(json.dumps({'event': 'exit'}))
        except tornado.websocket.WebSocketClosedError:
            logging.warning('Websocket closed when sending message.')

    @tornado.gen.engine
    def on_message(self, message):
        """
        Raw message from websocket client.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

        payload = yield tornado.gen.Task(self.redis.hget, 'sessions', self.session_id)

        try:
            data = loads(payload)

            # update last activity timestamp
            data['updated_at'] = time.time()

            yield tornado.gen.Task(self.redis.hset, 'sessions', self.session_id, dumps(data))
        except ValueError:
            logging.warning('Can not unserialize PHP object')

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

        if self.listener is not None:
            self.listener.unsubscribe(self.channel)
            self.listener.disconnect()

            self.listener = None
            self.channel = None

        self.clients -= 1
import tornadoredis
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen
import utils.crypt as crypt
import logging
import datetime
import json
from phpserialize import loads
import urllib
import os

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.is_connected = False

        # redis instance, only for sub/pub
        self.listener = None
        # channel to subscribe
        self.channel = None
        # handler returned by add_timeout() method
        self.timeout_handler = None

    def check_origin(self, origin):
        return True

    @property
    def redis(self):
        """
        Returns global redis instance. Keep in mind that we don't initialize separate redis connection

        :return:
        """
        return self.settings['redis']

    @property
    def clients(self):
        """
        Returns global number of connections.

        :return integer:
        """
        return self.settings['clients']

    @clients.setter
    def clients(self, value):
        """
        Set number of connections.

        :param value:
        :return:
        """
        self.settings['clients'] = value

    @tornado.gen.engine
    def open(self, *args):
        """
        Connection was established.

        :param args:
        :return:
        """
        self.clients += 1
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), self.clients))

        self.is_connected = True

        # cookie contains encypted session id
        cookie = self.get_cookie(os.environ['COOKIE'])

        if not cookie:
            self._send_exit()
            return

        payload = None

        try:
            # read cookie and decrypt it to obtain session id
            session_id = crypt.decrypt(urllib.unquote(cookie).decode('utf8'))
            # read payload from redis session
            payload = yield tornado.gen.Task(self.redis.hget, 'sessions', session_id)
        except Exception as e:
            logging.exception(e)

        if payload is None:
            self._send_exit()
        else:
            self.listen(payload)

    @tornado.gen.engine
    def listen(self, payload):
        """
        New connection for Redis only for sub/pub.

        :return:
        """
        try:
            data = loads(payload)

            self.channel = 'user:%d' % data['user_id'] if 'user_id' in data and data['user_id'] is not None else None
        except ValueError:
            logging.warning('Can not unserialize PHP object')
        except Exception as e:
            logging.exception(e)

        if self.channel:
            logging.info('Client authenticated. Channel name: %s' % self.channel)

            # send heartbeat after successful connection
            self._send_heartbeat()

            self.listener = tornadoredis.Client()
            self.listener.connect()

            yield tornado.gen.Task(self.listener.subscribe, self.channel)
            self.listener.listen(self.on_event)

    def _send_heartbeat(self):
        """
        Send heartbeat every 1 minute.

        :return:
        """
        if self.is_connected:
            self._send_data({'event': 'hb', 'data': 'hb'})

            # MUST BE send every 1 minutes so proxy (nginx) can keep connection alive
            self.timeout_handler = tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self._send_heartbeat)

    def _send_exit(self):
        """
        Send exit event. WebSocket client WILL NOT attempt to reconnect.

        :return:
        """
        self._send_data({'event': 'exit'})

    def _send_data(self, data):
        """
        Send data through WebSocket and close connection if error occurs.

        :param data:
        :return:
        """
        try:
            json_data = json.dumps(data)

            logging.info('Sending %s to %s' % (json_data, self.channel))
            self.write_message(json_data)
        except tornado.websocket.WebSocketClosedError:
            logging.warning('Websocket closed when sending message.')

            self.close()

    def on_message(self, message):
        """
        Raw message from websocket client.

        :param message:
        :return:
        """
        logging.info('Message from websocket client : %s' % message)

    def on_event(self, message):
        """
        Pass data from redis to websocket client.

        :param message:
        :return:
        """
        logging.info(message)

        if hasattr(message, 'kind') and message.kind == 'message':
            logging.info('Sending notification to ... %s' % self.channel)
            self.write_message(str(message.body))

    def on_close(self):
        """
        Unsubscribe and close redis connection.

        :return:
        """
        logging.info('Connection closed')

        if self.timeout_handler is not None:
            tornado.ioloop.IOLoop.instance().remove_timeout(self.timeout_handler)

        if self.listener is not None:
            self.listener.unsubscribe(self.channel)
            self.listener.disconnect()

            self.listener = None

        self.channel = None

        self.clients -= 1
        self.is_connected = False
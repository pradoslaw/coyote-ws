import tornadoredis
import tornado.web
import tornado.websocket
import tornado.ioloop
import utils.crypt as crypt
import logging
import time
import datetime
import json

# global array of clients...
clients = []

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)

        self.channel = '' # channel name
        self.client = None

    def check_origin(self, origin):
        return True

    @tornado.gen.engine
    def listen(self):
        self.client = tornadoredis.Client()
        self.client.connect()

        yield tornado.gen.Task(self.client.subscribe, self.channel)
        self.client.listen(self.on_event)

    def open(self, *args):
        clients.append(self)
        logging.info('Client %s connected. Number of clients: %d' % (str(self.request.remote_ip), clients.__len__()))

        token = self.get_argument('token')

        channel, timestamp = crypt.decrypt(token).split('|')
        diff = abs(int(time.time()) - int(timestamp))

        # token is valid only for one hour
        # @todo w przypadku gdy uzytkownik ma otwarta przez kilka godzine przegladarke, token
        # przestanie byc wazny. w sytuacji gdy bedziemy musieli zrestartowac serwer, klient JS nie bedzie
        # mogl ponownie polaczyc sie z serwerem poniewaz token bedzie niewazny. Pomoze przeladowanie strony
        # byc moze mozna to rozwiazac w inny sposob?
        if diff < 3600:
            self.channel = channel
            logging.info('Client authenticated. Channel name: %s' % self.channel)

            self.listen()
            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.heartbeat)
        else:
            logging.warning('Invalid token: %s' % token)
            self.close()

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

            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(minutes=1), self.heartbeat)

    def on_message(self, message):
        """
        Raw message from websocket client. We can just ignore it.

        :param message:
        :return:
        """
        logging.info('Message from websocket client: %s' % message)

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

        if hasattr(self.client, 'subscribed'):
            self.client.unsubscribe(self.channel)
            self.client.disconnect()

        self.client = None
        clients.remove(self)
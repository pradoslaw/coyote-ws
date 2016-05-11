import tornadoredis
import tornado.web
import tornado.websocket
import utils.crypt as crypt
import logging
import time


class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(RealtimeHandler, self).__init__(*args, **kwargs)
        token = self.get_argument('token')

        channel, timestamp = crypt.decrypt(token).split('|')
        diff = abs(int(time.time()) - int(timestamp))

        # token is valid only for one hour
        if diff < 3600:
            self.channel = channel
            logging.info('Channel name: %s' % self.channel)

            self.listen()
        else:
            logging.warning('Invalid token: %s' % token)

    def check_origin(self, origin):
        return True

    @tornado.gen.engine
    def listen(self):
        self.client = tornadoredis.Client()
        self.client.connect()

        yield tornado.gen.Task(self.client.subscribe, self.channel)
        self.client.listen(self.on_message)

    def open(self, *args):
        logging.info('Client connected')

    def on_message(self, message):
        """
        Event subscribe

        :param message:
        :return:
        """
        logging.info(message)

        if message.kind == 'message':
            # send data to client
            self.write_message(str(message.body))

    def on_close(self):
        logging.info('Connection closed')

        if hasattr(self, 'client') and self.client.subscribed:
            self.client.unsubscribe(self.channel)
            self.client.disconnect()
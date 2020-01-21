import tornado.ioloop
import tornado.web
import logging
import os
import signal
import settings # <-- don't remove that line. import project settings
from handlers import index, realtime

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.NOTSET)

# log everything on console
console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.NOTSET)

logger.addHandler(console)

app = tornado.web.Application([(r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler)], websocket_ping_interval=10)

logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.listen(os.environ.get('PORT'), os.environ.get('IP'))

def shutdown_handler(signum):
    logging.error('Received exit signal: %s' % signum)

    tornado.ioloop.IOLoop.instance().stop()

for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
    signal.signal(s, shutdown_handler)

try:
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.instance().stop()
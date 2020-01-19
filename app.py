import tornado.ioloop
import tornado.web
import logging
import os
import settings # <-- don't remove that line. import project settings
from handlers import index, realtime

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
#
console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)

logger.addHandler(console)

app = tornado.web.Application([(r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler)])

logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.listen(os.environ.get('PORT'), os.environ.get('IP'))

try:
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.instance().stop()
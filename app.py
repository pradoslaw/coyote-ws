import tornado.ioloop
import tornado.web
import logging
import logging.handlers
import os
import settings # <-- don't remove that line. import project settings
from handlers import index, realtime
from utils import cdn

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)

logger.addHandler(console)

log_dir = os.path.dirname(os.path.abspath(__file__)) + '/logs'

file = logging.FileHandler(log_dir + '/error.log')
file.setFormatter(formatter)
file.setLevel(logging.WARNING)

logger.addHandler(file)

app = tornado.web.Application([(r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler)], ui_methods=cdn)

logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.listen(os.environ.get('PORT'), os.environ.get('IP'))
# app.listen(8888, '127.0.0.1')

try:
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.instance().stop()
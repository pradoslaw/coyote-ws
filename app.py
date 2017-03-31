import tornado.ioloop
import tornado.web
import tornadoredis
import logging
import logging.handlers
import os
import settings # <-- don't remove that line. import project settings
from handlers import *

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.NOTSET)

logger.addHandler(console)

log_dir = os.path.dirname(os.path.abspath(__file__)) + '/logs'

file = logging.FileHandler(log_dir + '/error.log')
file.setFormatter(formatter)
file.setLevel(logging.WARNING)

logger.addHandler(file)

debug = logging.handlers.TimedRotatingFileHandler(log_dir + '/debug.log', when='midnight', backupCount=5)
debug.setFormatter(logging.Formatter("%(asctime)s\t%(message)s"))
debug.setLevel(logging.NOTSET)

logger.addHandler(debug)

class Application(tornado.web.Application):
    def __init__(self):
        redis = tornadoredis.Client()
        redis.connect()

        handlers = [
            (r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler)
        ]
        settings = {
            'redis': redis,
            'clients': 0
        }
        tornado.web.Application.__init__(self, handlers, **settings)

app = Application()
logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.listen(os.environ.get('PORT'), os.environ.get('IP'))

try:
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.instance().stop()
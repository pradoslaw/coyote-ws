import tornado.ioloop
import tornado.web
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
console.setLevel(logging.DEBUG)

logger.addHandler(console)

file = logging.FileHandler('logs/error.log')
file.setFormatter(formatter)
file.setLevel(logging.WARNING)

logger.addHandler(file)

debug = logging.handlers.TimedRotatingFileHandler('logs/debug.log', when='midnight', backupCount=5)
debug.setFormatter(logging.Formatter("%(asctime)s\t%(message)s"))
debug.setLevel(logging.DEBUG)

logger.addHandler(debug)

app = tornado.web.Application([(r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler)])

logging.info('Web socket server is running...')

app.listen(os.environ.get("PORT"))
tornado.ioloop.IOLoop.instance().start()
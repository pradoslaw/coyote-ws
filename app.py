import tornado.ioloop
import tornado.web
import logging
import logging.handlers
import os
import settings # <-- don't remove that line. import project settings
from handlers import *
from utils import cdn

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)

logger.addHandler(console)

log_dir = os.path.dirname(__file__) + '/logs/'

file = logging.FileHandler(log_dir + '/error.log')
file.setFormatter(formatter)
file.setLevel(logging.WARNING)

logger.addHandler(file)

debug = logging.handlers.TimedRotatingFileHandler(log_dir + '/debug.log', when='midnight', backupCount=5)
debug.setFormatter(logging.Formatter("%(asctime)s\t%(message)s"))
debug.setLevel(logging.DEBUG)

logger.addHandler(debug)

tracer = logging.getLogger('elasticsearch.trace')
tracer.setLevel(logging.INFO)
tracer.addHandler(logging.FileHandler(log_dir + '/es_trace.log'))

app = tornado.web.Application([(r'/realtime', realtime.RealtimeHandler), (r'/', index.IndexHandler), (r'/jobs', job.JobHandler)], ui_methods=cdn)

logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.listen(os.environ.get("PORT"))
tornado.ioloop.IOLoop.instance().start()
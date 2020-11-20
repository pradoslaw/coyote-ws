import uvicorn
import logging
import os
import signal
from settings import settings
from routes import websocket, home
from fastapi import FastAPI

app = FastAPI(title='Coyote WebSocket server')

logging.info('Web socket server is running on port %s...' % settings.port)

app.include_router(home.router)
app.include_router(websocket.router)

def shutdown_handler(signum):
    logging.error('Received exit signal: %s' % signum)

for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
    signal.signal(s, shutdown_handler)

# print(__name__)
if __name__ == "__main__":
    uvicorn.run(app, port=int(settings.port))


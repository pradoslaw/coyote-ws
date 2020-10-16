import uvicorn
import logging
import os
import signal
import settings # <-- don't remove that line. import project settings
from routes import websocket, home
from fastapi import FastAPI

app = FastAPI(title='Coyote WebSocket server')

logging.info('Web socket server is running on port %s...' % os.environ.get('PORT'))

app.include_router(home.router)
app.include_router(websocket.router)

def shutdown_handler(signum):
    logging.error('Received exit signal: %s' % signum)

for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
    signal.signal(s, shutdown_handler)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT')))


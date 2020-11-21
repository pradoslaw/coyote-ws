import uvicorn
import logging
import os
import settings
from routes import websocket, home
from fastapi import FastAPI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI(title='Coyote WebSocket server')

logging.info('Web socket server is running on port %s...' % os.environ['PORT'])

app.include_router(home.router)
app.include_router(websocket.router)

@app.on_event("shutdown")
async def shutdown_event():
    [await w.close() for w in websocket.active_connections]

logging.debug("run")
if __name__ == "__main__":
    uvicorn.run(app, port=int(os.environ['PORT']))


import os
import jwt
from utils.types import ChannelNames

def jwt_decode(token) -> ChannelNames:
    payload = jwt.decode(token, os.environ['APP_KEY'], algorithms=['HS256'])

    return payload['channel']



import jwt
from settings import settings
from utils.types import ChannelNames

def jwt_decode(token) -> ChannelNames:
    payload = jwt.decode(token, settings.app_key, algorithms=['HS256'])

    return payload['channel']



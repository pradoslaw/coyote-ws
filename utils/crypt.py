import os
import jwt

def jwt_decode(token):
    payload = jwt.decode(token, 'base64:' + os.environ['APP_KEY'], algorithms=['HS256'])

    return payload['channel']



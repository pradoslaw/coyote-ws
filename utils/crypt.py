import os
import jwt

def decrypt(token):
    payload = jwt.decode(token, os.environ['APP_KEY'], algorithms=['HS256'])

    return payload['channel']
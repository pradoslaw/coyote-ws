import os
import jwt

def jwt_decode(token):
    print('Key: %s' % os.environ['APP_KEY'])
    payload = jwt.decode(token, os.environ['APP_KEY'], algorithms=['HS256'])

    return payload



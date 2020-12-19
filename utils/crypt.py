import os
import jwt

def jwt_decode(token):
    payload = jwt.decode(token, os.environ['APP_KEY'], algorithms=['HS256'])
    print(payload)
    return payload



from json import loads

def is_valid_json(message):
    try:
        obj = loads(message)
    except ValueError:
        return False

    return obj
from os.path import join, dirname
from os import environ, path
from pydantic import BaseSettings
import logging

class Settings(BaseSettings):
    app_key: str
    redis_host: str
    port: int


dotenv_path = join(dirname(__file__), '.env')
print(dotenv_path)
settings = Settings(_env_file=dotenv_path if path.isfile(dotenv_path) else None)

try:
    with open('/run/secrets/APP_KEY_FILE', 'r') as secret_file:
        settings.app_key = secret_file.read().strip()
except IOError:
    logging.error('Secret file not found in /run/secrets/APP_KEY_FILE.')

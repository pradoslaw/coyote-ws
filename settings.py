from os.path import join, dirname
from os import environ
from dotenv import load_dotenv
import logging

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

try:
    with open('/run/secrets/APP_KEY_FILE', 'r') as secret_file:
        environ['APP_KEY'] = secret_file.read().strip()
except IOError:
    logging.error('Secret file not found in /run/secrets/APP_KEY_FILE.')

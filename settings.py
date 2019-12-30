# settings.py
from os.path import join, dirname
from os import environ
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

try:
    with open('/run/secrets/APP_KEY', 'r') as secret_file:
        environ['APP_KEY'] = secret_file.read()[7:]
except IOError:
    pass

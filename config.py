import os

from dotenv import load_dotenv

URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

LOGS_PATH = "logs/logs.txt"

TOKEN_PATH = 'token.txt'

LANG = 'ru-RU'

VOICE = 'marina'

EMOTION = 'friendly'

SPEED = '1.0'

DB_NAME = "db.sqlite"

DB_TABLE_USERS_NAME = "users"

MAX_SYMBOLS_PER_USER = 1000

WARNING_SYMBOLS_PER_USER = 800

MAX_USERS = 3

load_dotenv()

FOLDER_ID = os.getenv("folder_id")

ADMINS = os.getenv("admin_id")

BOT_TOKEN = os.getenv("token")
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.environ['TOKEN']
FONT_PATH: str = os.getenv('FONT_PATH', '/usr/share/fonts/TTF/SimpleHandmade.ttf')
FONT_SIZE: int = int(os.getenv('FONT_SIZE', '144'))
PIC_WIDTH: int = int(os.getenv('PIC_WIDTH', '300'))
PIC_HEIGHT: int = int(os.getenv('PIC_HEIGHT', '140'))
NOISE_LEVEL: int = int(os.getenv('NOISE_LEVEL', '30'))
NOISE_COLOR: str = os.getenv('NOISE_COLOR', 'black')
DB_PATH: str = os.getenv('DB_PATH', 'users.db')
MAX_ATTEMPTS: int = int(os.getenv('MAX_ATTEMPTS', '3'))
COOL_DOWN: int = int(os.getenv('COOL_DOWN', '900'))
LOCALE: str = os.getenv('LOCALE', 'ru_RU')
BLOCKLIST: set[int] = {int(x.strip()) for x in os.getenv('BLOCKLIST', '').split(',') if x.strip()}

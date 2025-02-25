# config.py
import os
from dotenv import load_dotenv
from pathlib import Path
import logging  # !!!
# !!!


load_dotenv()  # загрузили .env

BASE_DIR = Path(__file__).parent  # Путь к папке, где config
ASSETS_PATH = BASE_DIR / "assets" / "img"  # относительно config

# Берем из .env, если есть, иначе default
DATABASE_PATH = os.getenv("DATABASE_PATH", "kadry.db")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Пользователь")
DEFAULT_USER_ROLE = os.getenv("DEFAULT_USER_ROLE", "Сотрудник")

# --- Цвета ---
MAIN_BG_COLOR = "#F0F4F8"
SECONDARY_BG_COLOR = "#00B275"
LEFT_PANEL_BG_COLOR = "#FFFFFF"
BUTTON_BG_COLOR = "#FFFFFF"
BUTTON_ACTIVE_BG_COLOR = "#00B275"
BUTTON_HOVER_COLOR = "#EEEEEE"
BUTTON_TEXT_COLOR = "#333333"
BUTTON_ACTIVE_TEXT_COLOR = "#FFFFFF"
BUTTON_DISABLED_TEXT_COLOR = "#969BA0"  # Для disabled кнопок (если будут)
LABEL_TEXT_COLOR = "#464154"
FORM_LABEL_TEXT_COLOR = "#FFFFFF"  # Цвет текста меток в формах (белый)
FOOTER_TEXT_COLOR = "#969BA0"
ACCENT_COLOR = "#00B074"  # Зеленый, для акцентов (прямоугольник и т.д.)

# --- Размеры ---
LEFT_PANEL_WIDTH = 344
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1022
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 54
BUTTON_X = 62  # Используется для кнопок в левой панели
BUTTON_Y_START = 180  #
BUTTON_Y_SPACING = 15  #
AVATAR_SIZE = (48, 48)
# --- Шрифты ---
# Шрифты вынесены в отельные преременные, для удобной смены во всем приложении
DEFAULT_FONT = ("Arial", 18)  # шрифт по умолчанию
BOLD_FONT = ("Arial", 18, "bold")  # жирный шрифт
TITLE_BOLD_FONT = ("Arial", 42, "bold")  # Заголовок
FOOTER_FONT = ("Arial", 12)  # Шрифт для футера

# --- Логирование ---
# Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
LOG_FILE = "app.log"
MAX_LOG_SIZE = 1024 * 1024 * 5  # 5 MB, максимальный размер
BACKUP_COUNT = 5  # Сколько хранить старых логов

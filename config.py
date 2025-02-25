# config.py
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

load_dotenv()

BASE_DIR = Path(__file__).parent
ASSETS_PATH = BASE_DIR / "assets" / "img"
DATABASE_PATH = os.getenv("DATABASE_PATH", "personnel.db")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Пользователь")
DEFAULT_USER_ROLE = os.getenv("DEFAULT_USER_ROLE", "Сотрудник")

# --- ПУТЬ ДЛЯ ЭКСПОРТА ---
EXPORT_PATH = BASE_DIR / "export"

# --- Цвета ---
MAIN_BG_COLOR = "#F0F4F8"
SECONDARY_BG_COLOR = "#00B275"
LEFT_PANEL_BG_COLOR = "#FFFFFF"
BUTTON_BG_COLOR = "#FFFFFF"
BUTTON_ACTIVE_BG_COLOR = "#00B275"
BUTTON_HOVER_COLOR = "#EEEEEE"
BUTTON_TEXT_COLOR = "#333333"
BUTTON_ACTIVE_TEXT_COLOR = "#FFFFFF"
BUTTON_DISABLED_TEXT_COLOR = "#969BA0"
LABEL_TEXT_COLOR = "#464154"
FORM_LABEL_TEXT_COLOR = "#FFFFFF"
FOOTER_TEXT_COLOR = "#969BA0"
ACCENT_COLOR = "#00B074"

# --- Размеры ---
LEFT_PANEL_WIDTH = 344
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1022
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 54
BUTTON_X = 62
BUTTON_Y_START = 180
BUTTON_Y_SPACING = 15
AVATAR_SIZE = (48, 48)

# --- Шрифты ---
DEFAULT_FONT = ("Arial", 18)
BOLD_FONT = ("Arial", 18, "bold")
TITLE_BOLD_FONT = ("Arial", 42, "bold")
FOOTER_FONT = ("Arial", 12)

# --- Логирование ---
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
LOG_FILE = "app.log"
MAX_LOG_SIZE = 1024 * 1024 * 5
BACKUP_COUNT = 5

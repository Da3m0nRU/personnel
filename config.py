# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # загрузили .env

BASE_DIR = Path(__file__).parent  # Путь к папке, где config
ASSETS_PATH = BASE_DIR / "assets" / "img"  # относительно config

# Берем из .env, если есть, иначе default
DATABASE_PATH = os.getenv("DATABASE_PATH", "kadry.db")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Пользователь")
DEFAULT_USER_ROLE = os.getenv("DEFAULT_USER_ROLE", "Сотрудник")

# Цвета
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
FORM_LABEL_TEXT_COLOR = "#FFFFFF"
FOOTER_TEXT_COLOR = "#969BA0"
ACCENT_COLOR = "#00B074"  # Зеленый, для акцентов (прямоугольник и т.д.)

# Размеры
LEFT_PANEL_WIDTH = 344
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1022
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 54
BUTTON_X = 62
BUTTON_Y_START = 180
BUTTON_Y_SPACING = 15
AVATAR_SIZE = (48, 48)

# Шрифты. Можно оставить так, можно задать в .env
DEFAULT_FONT = ("Arial", 18)
BOLD_FONT = ("Arial", 18, "bold")
TITLE_BOLD_FONT = ("Arial", 42, "bold")
FOOTER_FONT = ("Arial", 12)

# Пути. Если нужно вынести пути к иконкам
# ASSETS_PATH перенесено в utils

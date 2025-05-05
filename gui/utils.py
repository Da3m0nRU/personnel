# gui/utils.py
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from config import ASSETS_PATH  # !!!
import logging
import logging.handlers
import re


def relative_to_assets(path: str) -> Path:
    """
    Преобразует относительный путь к файлу в папке assets в абсолютный.

    Args:
        path (str): Относительный путь к файлу (например, "image.png").

    Returns:
        Path: Объект Path, представляющий абсолютный путь к файлу.
    """
    return ASSETS_PATH / Path(path)


def load_icon(name: str, size=(24, 24)):
    """
    Загружает иконку из папки assets и возвращает объект CTkImage.

    Args:
        name (str): Имя файла иконки (например, "icon.png").
        size (tuple): Размер иконки (ширина, высота).

    Returns:
        CTkImage: Объект CTkImage для использования в customtkinter.
    """
    img = Image.open(relative_to_assets(name))
    return ctk.CTkImage(img, size=size)


def configure_logging(log_level, log_format, log_file, max_log_size, backup_count, logger_name=None,):
    """
     Настраивает логгер.
     Args:
         logger_name (str, optional):  Имя логгера.  Если None, настраивается корневой логгер.
         log_level: Уровень логирования
         log_format: Формат
         log_file: Куда сохранять
         max_log_size: Макс размер
         backup_count: Сколько хранить старых логов

     Returns:
         logging.Logger: Настроенный объект логгера.
     """

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Если уже есть хэндлеры, то выходим, не добавляя новые,
    # нужно для случая, когда мы вызываем, configure_logging несколько раз из разных мест.
    if logger.hasHandlers():
        return logger
    formatter = logging.Formatter(log_format)

    #  Обработчик для файла (с ротацией)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_log_size, backupCount=backup_count,
        encoding='utf-8'  # !!! encoding
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    #  Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def format_date(date_str):
    """
    Преобразует дату из формата БД (ГГГГ-ММ-ДД) в формат отображения (ДД.ММ.ГГГГ).

    Args:
        date_str (str): Дата в формате ГГГГ-ММ-ДД или None.

    Returns:
        str: Дата в формате ДД.ММ.ГГГГ или пустая строка, если date_str пустой или None.
    """
    if not date_str:  # Проверка на None или пустую строку
        return ""

    # Шаблон для проверки формата ГГГГ-ММ-ДД
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not pattern.match(date_str):
        return date_str  # Возвращаем исходную строку, если формат не соответствует

    # Разбиваем строку даты на компоненты
    try:
        year, month, day = date_str.split('-')
        return f"{day}.{month}.{year}"
    except ValueError:
        return date_str


def parse_date(date_str):
    """
    Преобразует дату из формата отображения (ДД.ММ.ГГГГ) в формат БД (ГГГГ-ММ-ДД).

    Args:
        date_str (str): Дата в формате ДД.ММ.ГГГГ или None.

    Returns:
        str: Дата в формате ГГГГ-ММ-ДД или пустая строка, если date_str пустой, None или неверного формата.
    """
    if not date_str:  # Проверка на None или пустую строку
        return ""

    # Шаблон для проверки формата ДД.ММ.ГГГГ
    pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    if not pattern.match(date_str):
        return ""  # Возвращаем пустую строку, если формат не соответствует

    # Разбиваем строку даты на компоненты
    try:
        day, month, year = date_str.split('.')
        return f"{year}-{month}-{day}"
    except ValueError:
        return ""

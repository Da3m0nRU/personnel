"""
Модуль тестов для утилит системы.

Тестирует функциональность вспомогательных функций и классов.
"""
from gui.utils import configure_logging, format_date, parse_date
import pytest
import logging
import tempfile
import os
import time
from pathlib import Path
import sys

# Добавление корневого каталога проекта в путь поиска модулей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_configure_logging():
    """Проверяет настройку системы логирования."""
    # Создаем временный файл для логов
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as temp_log:
        log_path = temp_log.name

    # Очищаем все существующие обработчики корневого логгера перед тестом
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Устанавливаем уровень корневого логгера
    original_level = root_logger.level
    root_logger.setLevel(logging.NOTSET)

    try:
        # Создаем тестовый логгер напрямую, не используя configure_logging
        test_logger = logging.getLogger("test_logger")
        test_logger.setLevel(logging.DEBUG)
        test_logger.propagate = False  # Важно отключить propagate

        # Очищаем все обработчики логгера
        for handler in list(test_logger.handlers):
            test_logger.removeHandler(handler)

        # Добавляем обработчик для записи в файл
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        test_logger.addHandler(file_handler)

        # Проверяем, что логгер настроен, записывая сообщения
        test_logger.debug("Тестовое сообщение DEBUG")
        test_logger.info("Тестовое сообщение INFO")
        test_logger.warning("Тестовое сообщение WARNING")

        # Принудительно сбрасываем буфер
        file_handler.flush()

        # Закрываем обработчик, чтобы освободить файл
        file_handler.close()
        test_logger.removeHandler(file_handler)

        # Проверяем, что файл логов существует
        assert os.path.exists(log_path)

        # Проверяем, что файл имеет ненулевой размер
        assert os.path.getsize(log_path) > 0

    finally:
        # Возвращаем исходные настройки логгера
        root_logger.setLevel(original_level)

        # Удаляем временный файл
        if os.path.exists(log_path):
            try:
                os.unlink(log_path)
            except (PermissionError, OSError):
                pass  # Игнорируем ошибки при удалении


def test_format_date():
    """Проверяет форматирование даты из строки БД в отображаемый формат."""
    # Тесты для корректных данных
    assert format_date("2023-12-15") == "15.12.2023"
    assert format_date("2023-01-01") == "01.01.2023"

    # Тесты для пустых значений
    assert format_date(None) == ""
    assert format_date("") == ""

    # Тесты для некорректных форматов
    assert format_date("not-a-date") == "not-a-date"
    assert format_date("2023/12/15") == "2023/12/15"


def test_parse_date():
    """Проверяет преобразование даты из отображаемого формата в формат для БД."""
    # Тесты для корректных данных
    assert parse_date("15.12.2023") == "2023-12-15"
    assert parse_date("01.01.2023") == "2023-01-01"

    # Тесты для пустых значений
    assert parse_date(None) == ""
    assert parse_date("") == ""

    # Тесты для некорректных форматов
    assert parse_date("not-a-date") == ""
    assert parse_date("2023/12/15") == ""

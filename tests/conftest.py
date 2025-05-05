"""
Модуль конфигурации тестов и общих фикстур.

Содержит фикстуры для инициализации тестовой базы данных и 
предоставления тестовых объектов для использования в тестах.
"""
from db.database import Database
import pytest
import sqlite3
import os
import sys
import tempfile
from pathlib import Path

# Добавление корневого каталога проекта в путь поиска модулей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_db_path():
    """Создаёт временный файл БД для тестов."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def test_db(test_db_path):
    """Создаёт тестовую БД со схемой."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Создание схемы БД для тестов
    with open(project_root / 'db' / 'create_tables.sql', 'r', encoding='utf-8') as f:
        script = f.read()
        cursor.executescript(script)

    # Добавление базовых справочных данных
    cursor.executescript("""
        INSERT INTO Genders (GenderName) VALUES ('Мужской'), ('Женский');
        INSERT INTO States (StateName) VALUES ('Работает'), ('Уволен');
        INSERT INTO Departments (Name) VALUES ('ИТ'), ('Кадры');
        INSERT INTO Positions (Name) VALUES ('Разработчик'), ('Менеджер');
        INSERT INTO Events (EventName) VALUES ('Прием'), ('Увольнение'), ('Перемещение');
    """)
    conn.commit()
    conn.close()

    # Возвращаем экземпляр Database
    db = Database(test_db_path)
    yield db
    db.close()

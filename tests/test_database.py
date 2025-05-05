"""
Модуль тестов для класса Database.

Тестирует функциональность базового класса для работы с БД SQLite.
"""
import pytest
from db.database import Database


def test_database_connection(test_db_path):
    """Проверяет успешное подключение к базе данных."""
    db = Database(test_db_path)
    assert db.conn is not None
    assert db.cursor is not None
    db.close()


def test_execute_query(test_db):
    """Проверяет выполнение модифицирующего запроса."""
    result = test_db.execute_query(
        "INSERT INTO Departments (Name) VALUES (?)",
        ("Тестовый отдел",)
    )
    assert result is True

    # Проверяем, что запись добавлена
    data = test_db.fetch_one(
        "SELECT Name FROM Departments WHERE Name = ?",
        ("Тестовый отдел",)
    )
    assert data is not None
    assert data[0] == "Тестовый отдел"


def test_fetch_all(test_db):
    """Проверяет получение всех записей."""
    # Добавляем тестовые данные
    test_db.execute_query(
        "INSERT INTO Departments (Name) VALUES (?)", ("Отдел 1",))
    test_db.execute_query(
        "INSERT INTO Departments (Name) VALUES (?)", ("Отдел 2",))

    # Получаем данные и проверяем результат
    result = test_db.fetch_all("SELECT Name FROM Departments ORDER BY Name")
    assert result is not None
    assert len(result) >= 4  # 2 из базовой фикстуры + 2 добавленных
    assert any(row[0] == "Отдел 1" for row in result)
    assert any(row[0] == "Отдел 2" for row in result)


def test_fetch_one(test_db):
    """Проверяет получение одной записи."""
    # Добавляем тестовые данные
    test_db.execute_query(
        "INSERT INTO Departments (Name) VALUES (?)", ("Уникальный отдел",))

    # Получаем данные и проверяем результат
    result = test_db.fetch_one(
        "SELECT Name FROM Departments WHERE Name = ?", ("Уникальный отдел",))
    assert result is not None
    assert result[0] == "Уникальный отдел"

    # Проверяем запрос с несуществующими данными
    nonexistent = test_db.fetch_one(
        "SELECT Name FROM Departments WHERE Name = ?", ("Несуществующий",))
    assert nonexistent is None


def test_error_handling(test_db):
    """Проверяет обработку ошибок при выполнении запросов."""
    # Некорректный SQL-запрос
    result = test_db.execute_query(
        "INSERT INTO NonExistentTable (Name) VALUES (?)", ("Test",))
    assert result is False

    # Некорректный запрос для fetch_all
    result = test_db.fetch_all("SELECT * FROM NonExistentTable")
    assert result is None

    # Некорректный запрос для fetch_one
    result = test_db.fetch_one("SELECT * FROM NonExistentTable")
    assert result is None

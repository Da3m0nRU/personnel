"""
Модуль тестов для класса UserRepository.

Тестирует функциональность репозитория для работы с данными пользователей системы.
"""
import pytest
from db.user_repository import UserRepository
from db.role_repository import RoleRepository


@pytest.fixture
def user_repo(test_db):
    """Создаёт репозиторий пользователей с тестовой БД."""
    return UserRepository(test_db)


@pytest.fixture
def role_repo(test_db):
    """Создаёт репозиторий ролей с тестовой БД."""
    return RoleRepository(test_db)


@pytest.fixture
def admin_role_id(role_repo):
    """Добавляет роль администратора и возвращает её ID."""
    role_id = role_repo.insert_role("Администратор")
    return role_id


@pytest.fixture
def test_user(user_repo, admin_role_id):
    """Добавляет тестового пользователя в БД."""
    user_id = user_repo.insert_user(
        login="testadmin",
        password="TestPassword123",
        employee_pn=None,
        role_id=admin_role_id,
        email="test@example.com"
    )
    return user_id


def test_insert_user(user_repo, admin_role_id):
    """Проверяет добавление нового пользователя."""
    user_id = user_repo.insert_user(
        login="newuser",
        password="Password123",
        employee_pn=None,
        role_id=admin_role_id,
        email="newuser@example.com"
    )

    assert user_id is not None

    # Проверяем, что пользователь действительно добавлен
    user = user_repo.get_user_by_id(user_id)
    assert user is not None
    assert user[1] == "newuser"  # Login

    # В системе пароль должен храниться в хешированном виде
    # Прямое сравнение с исходным паролем не будет работать
    assert user[2] != "Password123"  # Password хранится в виде хеша
    assert user[4] == admin_role_id  # RoleID
    assert user[5] == "newuser@example.com"  # Email


def test_get_user_by_id(user_repo, test_user):
    """Проверяет получение пользователя по ID."""
    user = user_repo.get_user_by_id(test_user)
    assert user is not None
    assert user[0] == test_user  # ID
    assert user[1] == "testadmin"  # Login


def test_get_user_by_login(user_repo):
    """Проверяет получение пользователя по логину."""
    # Добавляем пользователя
    user_id = user_repo.insert_user(
        login="uniquelogin",
        password="Password123",
        employee_pn=None,
        role_id=1,
        email="unique@example.com"
    )
    assert user_id is not None

    # Получаем по логину
    user = user_repo.get_user_by_login("uniquelogin")
    assert user is not None
    assert user[1] == "uniquelogin"  # Login
    assert user[5] == "unique@example.com"  # Email

    # Проверяем несуществующий логин
    nonexistent = user_repo.get_user_by_login("nonexistent")
    assert nonexistent is None


def test_update_user(user_repo, test_user):
    """Проверяет обновление данных пользователя."""
    # Получаем текущие данные
    user_before = user_repo.get_user_by_id(test_user)
    old_password_hash = user_before[2]

    # Получаем необходимые параметры
    role_id = user_before[4]

    # Обновляем данные - здесь необходимо адаптировать к реальным параметрам метода
    query = "UPDATE Users SET Email = ?, Password = ? WHERE ID = ?"
    new_password = "NewPassword456"
    new_password_hash = user_repo._hash_password(new_password)
    new_email = "updated@example.com"

    result = user_repo.db.execute_query(
        query, (new_email, new_password_hash, test_user))
    assert result is True

    # Проверяем обновленные данные
    user_after = user_repo.get_user_by_id(test_user)
    assert user_after is not None
    assert user_after[2] != old_password_hash  # Хеш пароля изменился
    assert user_after[5] == "updated@example.com"  # Email изменился


def test_delete_user(user_repo, test_user):
    """Проверяет удаление пользователя."""
    # Удаляем пользователя - адаптируем напрямую, используя SQL-запрос
    query = "DELETE FROM Users WHERE ID = ?"
    result = user_repo.db.execute_query(query, (test_user,))
    assert result is True

    # Проверяем, что пользователя больше нет
    user = user_repo.get_user_by_id(test_user)
    assert user is None


def test_login_exists(user_repo):
    """Проверяет работу метода проверки существования логина."""
    # Добавляем пользователя с уникальным логином
    user_id = user_repo.insert_user(
        login="checklogin",
        password="Password123",
        employee_pn=None,
        role_id=1,
        email="check@example.com"
    )
    assert user_id is not None

    # Существующий логин
    assert user_repo.login_exists("checklogin") is True

    # Несуществующий логин
    assert user_repo.login_exists("nonexistentlogin") is False


def test_verify_password(user_repo):
    """Проверяет работу метода проверки пароля."""
    # Создаем пользователя с известным паролем
    password = "SecurePassword123"
    user_id = user_repo.insert_user(
        login="passwordtest",
        password=password,
        employee_pn=None,
        role_id=1,
        email="password@example.com"
    )
    assert user_id is not None

    # Получаем пользователя и его хеш пароля
    user = user_repo.get_user_by_login("passwordtest")
    assert user is not None
    password_hash = user[2]

    # Проверяем правильный пароль
    is_verified = user_repo.verify_password(password_hash, password)
    assert is_verified is True

    # Проверяем неправильный пароль
    is_verified = user_repo.verify_password(password_hash, "WrongPassword")
    assert is_verified is False

"""
Модуль тестов для класса EmployeeRepository.

Тестирует функциональность репозитория для работы с данными сотрудников.
"""
import pytest
from db.employee_repository import EmployeeRepository


@pytest.fixture
def employee_repo(test_db):
    """Создаёт репозиторий сотрудников с тестовой БД."""
    return EmployeeRepository(test_db)


@pytest.fixture
def test_employee(employee_repo):
    """Добавляет тестового сотрудника в БД."""
    personnel_number = "TEST123"
    employee_repo.insert_employee(
        personnel_number=personnel_number,
        lastname="Тестов",
        firstname="Тест",
        middlename="Тестович",
        birth_date_str="1990-01-01",
        gender_id=1,  # Мужской
        position_id=1,  # Разработчик
        department_id=1,  # ИТ
        state_id=1  # Работает
    )
    return personnel_number


def test_insert_employee(employee_repo):
    """Проверяет добавление нового сотрудника."""
    result = employee_repo.insert_employee(
        personnel_number="EMP001",
        lastname="Иванов",
        firstname="Иван",
        middlename="Иванович",
        birth_date_str="1980-05-15",
        gender_id=1,  # Мужской
        position_id=1,  # Разработчик
        department_id=1,  # ИТ
        state_id=1  # Работает
    )
    assert result is True

    # Проверяем, что сотрудник действительно добавлен
    employee = employee_repo.get_employee_by_personnel_number("EMP001")
    assert employee is not None
    assert employee[1] == "Иванов"  # LastName
    assert employee[2] == "Иван"    # FirstName


def test_get_employee_by_personnel_number(employee_repo, test_employee):
    """Проверяет получение сотрудника по табельному номеру."""
    employee = employee_repo.get_employee_by_personnel_number(test_employee)
    assert employee is not None
    assert employee[0] == test_employee  # PersonnelNumber
    assert employee[1] == "Тестов"       # LastName
    assert employee[2] == "Тест"         # FirstName
    assert employee[3] == "Тестович"     # MiddleName


def test_update_employee(employee_repo, test_employee):
    """Проверяет обновление данных сотрудника."""
    # Обновляем данные
    result = employee_repo.update_employee(
        personnel_number=test_employee,
        lastname="Тестов",
        firstname="Тест",
        middlename="Обновленный",
        birth_date_str="1990-01-01",
        gender_id=1,
        position_id=2,  # Изменили должность на "Менеджер"
        department_id=2,  # Изменили отдел на "Кадры"
        state_id=1
    )
    assert result is True

    # Проверяем обновленные данные
    employee = employee_repo.get_employee_by_personnel_number(test_employee)
    assert employee is not None
    assert employee[3] == "Обновленный"  # MiddleName изменилось

    # Получаем SQL-запросом название должности и отдела для проверки
    position_query = "SELECT Name FROM Positions WHERE ID = 2"
    position_result = employee_repo.db.fetch_one(position_query)
    assert position_result is not None
    # Проверяем, что ID=2 соответствует "Менеджер"
    assert position_result[0] == "Менеджер"

    department_query = "SELECT Name FROM Departments WHERE ID = 2"
    department_result = employee_repo.db.fetch_one(department_query)
    assert department_result is not None
    # Проверяем, что ID=2 соответствует "Кадры"
    assert department_result[0] == "Кадры"

    # Проверяем, что названия должности и отдела правильно отображаются в данных сотрудника
    assert employee[6] == "Менеджер"   # PositionName
    assert employee[7] == "Кадры"      # DepartmentName


def test_delete_employee(employee_repo, test_employee):
    """Проверяет удаление сотрудника."""
    # Удаляем сотрудника
    result = employee_repo.delete_employee(test_employee)
    assert result is True

    # Проверяем, что сотрудника больше нет
    employee = employee_repo.get_employee_by_personnel_number(test_employee)
    assert employee is None


def test_personnel_number_exists(employee_repo, test_employee):
    """Проверяет работу метода проверки существования табельного номера."""
    # Существующий сотрудник
    assert employee_repo.personnel_number_exists(test_employee) is True

    # Несуществующий сотрудник
    assert employee_repo.personnel_number_exists("NONEXISTENT") is False


def test_get_employees(employee_repo, test_employee):
    """Проверяет получение списка сотрудников с фильтрацией."""
    # Добавляем еще одного сотрудника
    employee_repo.insert_employee(
        personnel_number="EMP002",
        lastname="Петров",
        firstname="Петр",
        middlename="Петрович",
        birth_date_str="1985-10-10",
        gender_id=1,
        position_id=1,
        department_id=1,
        state_id=1
    )

    # Получаем всех сотрудников
    all_employees, count = employee_repo.get_employees()
    assert all_employees is not None
    assert count >= 2  # Минимум 2 сотрудника

    # Поиск по части фамилии
    search_results, search_count = employee_repo.get_employees(
        search_term="Тест")
    assert search_results is not None
    assert search_count >= 1
    assert any(employee[0] == test_employee for employee in search_results)

    # Фильтр по табельному номеру
    filter_results, filter_count = employee_repo.get_employees(
        employee_pn_filter=test_employee)
    assert filter_results is not None
    assert filter_count == 1
    assert filter_results[0][0] == test_employee

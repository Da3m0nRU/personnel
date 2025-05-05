"""
Модуль тестов для класса AbsenceRepository.

Тестирует функциональность репозитория для работы с данными отсутствий сотрудников.
"""
import pytest
from db.absence_repository import AbsenceRepository
from db.employee_repository import EmployeeRepository


@pytest.fixture
def absence_repo(test_db):
    """Создаёт репозиторий отсутствий с тестовой БД."""
    return AbsenceRepository(test_db)


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
        gender_id=1,
        position_id=1,
        department_id=1,
        state_id=1
    )
    return personnel_number


@pytest.fixture
def test_absence(absence_repo, test_employee):
    """Добавляет тестовую запись об отсутствии в БД."""
    # Адаптируем вызов к фактической сигнатуре метода
    result = absence_repo.insert_absence(
        personnel_number=test_employee,
        absence_date="2023-11-15",
        full_day=1,
        start_time=None,
        end_time=None,
        reason="Тестовое отсутствие",
        schedule_id=None
    )
    assert result is True

    # Используем отдельный запрос, чтобы получить ID созданной записи
    query = "SELECT ID FROM Absences WHERE EmployeePersonnelNumber = ? AND AbsenceDate = ?"
    absence_id = absence_repo.db.fetch_one(
        query, (test_employee, "2023-11-15"))
    return absence_id[0] if absence_id else None


def test_insert_absence(absence_repo, test_employee):
    """Проверяет добавление новой записи об отсутствии."""
    # Адаптируем вызов к фактической сигнатуре метода
    result = absence_repo.insert_absence(
        personnel_number=test_employee,
        absence_date="2023-12-01",
        full_day=0,
        start_time="09:00",
        end_time="12:00",
        reason="Тестовое отсутствие (неполный день)",
        schedule_id=None
    )

    assert result is True

    # Используем отдельный запрос, чтобы получить ID созданной записи
    query = "SELECT ID FROM Absences WHERE EmployeePersonnelNumber = ? AND AbsenceDate = ?"
    absence_id_record = absence_repo.db.fetch_one(
        query, (test_employee, "2023-12-01"))
    assert absence_id_record is not None
    absence_id = absence_id_record[0]

    # Проверяем, что запись об отсутствии действительно добавлена
    absence = absence_repo.get_absence_by_id(absence_id)
    assert absence is not None
    assert absence[1] == test_employee  # EmployeePersonnelNumber
    assert absence[2] == "2023-12-01"   # AbsenceDate
    assert absence[4] == "09:00"        # StartingTime
    assert absence[5] == "12:00"        # EndingTime
    assert absence[3] == 0              # FullDay
    assert absence[6] == "Тестовое отсутствие (неполный день)"  # Reason


def test_get_absence_by_id(absence_repo, test_absence):
    """Проверяет получение записи об отсутствии по ID."""
    absence = absence_repo.get_absence_by_id(test_absence)
    assert absence is not None
    assert absence[0] == test_absence  # ID
    assert absence[3] == 1             # FullDay
    assert absence[6] == "Тестовое отсутствие"  # Reason


def test_update_absence(absence_repo, test_absence, test_employee):
    """Проверяет обновление записи об отсутствии."""
    # Обновляем данные
    result = absence_repo.update_absence(
        absence_id=test_absence,
        absence_date="2023-11-15",
        full_day=1,
        start_time=None,
        end_time=None,
        reason="Обновленная причина отсутствия",
        schedule_id=None,
        personnel_number=test_employee
    )
    assert result is True

    # Проверяем обновленные данные
    absence = absence_repo.get_absence_by_id(test_absence)
    assert absence is not None
    assert absence[6] == "Обновленная причина отсутствия"  # Reason изменился


def test_delete_absence(absence_repo, test_absence):
    """Проверяет удаление записи об отсутствии."""
    # Удаляем запись
    result = absence_repo.delete_absence(test_absence)
    assert result is True

    # Проверяем, что записи больше нет
    absence = absence_repo.get_absence_by_id(test_absence)
    assert absence is None


def test_get_absences(absence_repo, test_employee):
    """Проверяет получение списка отсутствий с фильтрацией."""
    # Добавляем несколько записей об отсутствиях
    absence_repo.insert_absence(
        personnel_number=test_employee,
        absence_date="2023-12-01",
        full_day=1,
        start_time=None,
        end_time=None,
        reason="Отпуск",
        schedule_id=None
    )

    absence_repo.insert_absence(
        personnel_number=test_employee,
        absence_date="2023-12-02",
        full_day=1,
        start_time=None,
        end_time=None,
        reason="Отпуск",
        schedule_id=None
    )

    # Получаем все отсутствия
    all_absences, count = absence_repo.get_absences()
    assert all_absences is not None
    assert count >= 2  # Минимум 2 записи

    # Поиск по причине
    search_results, search_count = absence_repo.get_absences(
        search_term="Отпуск")
    assert search_results is not None
    assert search_count >= 2

    # Проверяем, что записи содержат правильные данные
    # Ищем табельный номер сотрудника в результатах
    personnel_numbers = [row[1] for row in search_results]
    assert test_employee in personnel_numbers

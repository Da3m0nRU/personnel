# Тесты для АИС "Кадры"

Этот каталог содержит модульные (unit) тесты для проверки компонентов системы АИС "Кадры".

## Структура тестов

- `tests/conftest.py` - общие фикстуры для тестов
- `tests/test_database.py` - тесты для класса Database
- `tests/test_utils.py` - тесты для вспомогательных функций
- `tests/test_repositories/` - тесты для репозиториев:
  - `test_employee_repository.py` - тесты для EmployeeRepository
  - `test_absence_repository.py` - тесты для AbsenceRepository
  - `test_user_repository.py` - тесты для UserRepository

## Запуск тестов

### Запуск всех тестов

```bash
# Из корневого каталога проекта
pytest

# С подробным выводом
pytest -v
```

### Запуск определенных модулей тестов

```bash
# Только тесты базы данных
pytest tests/test_database.py

# Только тесты репозиториев
pytest tests/test_repositories/
```

### Запуск конкретного теста

```bash
# По имени теста
pytest tests/test_database.py::test_fetch_one

# По части имени (все тесты, содержащие 'password' в имени)
pytest -k "password"
```

### Формирование отчета о покрытии кода тестами

Для получения отчета о покрытии кода тестами необходимо установить пакет `pytest-cov`:

```bash
pip install pytest-cov
```

Запуск тестов с формированием отчета:

```bash
# Базовый отчет в консоли
pytest --cov=db

# Подробный отчет HTML (будет создан в директории htmlcov)
pytest --cov=db --cov-report=html
```

## Создание новых тестов

При создании новых тестов следуйте следующим правилам:

1. Имена файлов с тестами должны начинаться с `test_`.
2. Имена тестовых функций должны начинаться с `test_`.
3. Используйте фикстуры для подготовки тестового окружения.
4. Каждый тест должен быть независимым от других тестов.
5. Используйте assert-выражения для проверки результатов.

Пример теста:

```python
def test_something(some_fixture):
    # Arrange - подготовка данных
    expected_result = 42

    # Act - выполнение тестируемого кода
    actual_result = some_function()

    # Assert - проверка результатов
    assert actual_result == expected_result
```

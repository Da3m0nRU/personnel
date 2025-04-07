"""
Модуль репозитория для взаимодействия с таблицей `Departments` (Отделы).

Содержит методы для получения данных об отделах.
"""
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class DepartmentRepository:
    """Репозиторий для работы со справочником отделов."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    def get_all(self):
        """
        Возвращает все записи из справочника отделов.

        Returns:
            list[tuple] | None: Список кортежей (ID, Name) или None в случае ошибки.
        """
        log.debug("Запрос всех записей из справочника Departments")
        result = self.db.fetch_all(q.GET_DEPARTMENTS)
        log.debug(
            f"Получено {len(result) if result else 0} записей об отделах.")
        return result

    def get_by_name(self, department_name):
        """
        Возвращает ID отдела по его названию.

        Args:
            department_name (str): Название отдела для поиска.

        Returns:
            int | None: ID найденного отдела или None, если отдел не найден или произошла ошибка.
                      Примечание: В отличие от других get_by_name, этот возвращает результат fetch_all,
                      а не fetch_one. Потенциально может вернуть несколько ID, если имена не уникальны.
                      В коде импорта (import_dialog.py) используется первый элемент списка.
        """
        log.debug(f"Запрос ID отдела по названию: '{department_name}'")
        result = self.db.fetch_all(
            q.GET_DEPARTMENT_ID_BY_NAME, (department_name,))
        # Не извлекаем [0], так как get_by_name в import_dialog ожидает список
        log.debug(f"Результат поиска ID отдела: {result}")
        return result

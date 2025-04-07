"""
Модуль репозитория для взаимодействия с таблицей `States` (Состояния сотрудников).

Содержит методы для получения данных о состояниях.
"""
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class StateRepository:
    """Репозиторий для работы со справочником состояний сотрудников."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    def get_all(self):
        """
        Возвращает все записи из справочника состояний.

        Returns:
            list[tuple] | None: Список кортежей (ID, StateName) или None в случае ошибки.
        """
        log.debug("Запрос всех записей из справочника States")
        result = self.db.fetch_all(q.GET_STATES)
        log.debug(
            f"Получено {len(result) if result else 0} записей о состояниях.")
        return result

    def get_by_id(self, state_name):
        """
        Возвращает ID состояния по его названию.

        Примечание: В текущей реализации этот метод фактически ищет по имени,
        так как параметр `state_id` (переименован в `state_name` для ясности)
        используется в запросе `GET_STATE_ID`, который ищет по `StateName`.
        Метод `get_by_name` является псевдонимом для этого метода.

        Args:
            state_name (str): Название состояния для поиска.

        Returns:
            int | None: ID найденного состояния или None, если состояние не найдено или произошла ошибка.
        """
        log.debug(f"Запрос ID состояния по названию: '{state_name}'")
        result = self.db.fetch_one(q.GET_STATE_ID, (state_name,))
        found_id = result[0] if result else None
        log.debug(f"Результат поиска ID состояния: {found_id}")
        return found_id

    def get_by_name(self, name):
        """
        Возвращает ID состояния по его названию.

        Является псевдонимом для метода `get_by_id` из-за текущей реализации запроса.

        Args:
            name (str): Название состояния для поиска.

        Returns:
            int | None: ID найденного состояния или None, если состояние не найдено или произошла ошибка.
        """
        return self.get_by_id(name)

# db/position_repository.py
"""
Модуль репозитория для взаимодействия с таблицей `Positions` (Должности).

Содержит методы для получения данных о должностях и связанных с ними отделах.
"""
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class PositionRepository:
    """Репозиторий для работы со справочником должностей."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    def get_all(self):
        """
        Возвращает все записи из справочника должностей.

        Returns:
            list[tuple] | None: Список кортежей (ID, Name) или None в случае ошибки.
        """
        log.debug("Запрос всех записей из справочника Positions")
        result = self.db.fetch_all(q.GET_ALL_POSITIONS)
        log.debug(
            f"Получено {len(result) if result else 0} записей о должностях.")
        return result

    def get_by_id(self, position_name):
        """
        Возвращает ID должности по её названию.

        Примечание: В текущей реализации этот метод фактически ищет по имени,
        так как параметр `position_id` (переименован в `position_name` для ясности)
        используется в запросе `GET_POSITION_ID`, который ищет по `Name`.
        Метод `get_by_name` является псевдонимом для этого метода.

        Args:
            position_name (str): Название должности для поиска.

        Returns:
            int | None: ID найденной должности или None, если должность не найдена или произошла ошибка.
        """
        log.debug(f"Запрос ID должности по названию: '{position_name}'")
        result = self.db.fetch_one(q.GET_POSITION_ID, (position_name,))
        found_id = result[0] if result else None
        log.debug(f"Результат поиска ID должности: {found_id}")
        return found_id

    def get_by_name(self, name):
        """
        Возвращает ID должности по её названию.

        Является псевдонимом для метода `get_by_id` из-за текущей реализации запроса.

        Args:
            name (str): Название должности для поиска.

        Returns:
            int | None: ID найденной должности или None, если должность не найдена или произошла ошибка.
        """
        return self.get_by_id(name)

    def get_departments_for_position(self, position_id):
        """
        Возвращает список названий отделов, связанных с указанной должностью.

        Args:
            position_id (int): ID должности.

        Returns:
            list[tuple] | None: Список кортежей с названиями отделов [(Name,), ...] или None в случае ошибки.
        """
        log.debug(f"Запрос отделов для должности ID={position_id}")
        result = self.db.fetch_all(
            q.GET_DEPARTMENTS_FOR_POSITION, (position_id,))
        log.debug(
            f"Найдено {len(result) if result else 0} отделов для должности ID={position_id}.")
        return result

    def get_positions(self):
        """
        Возвращает список названий всех должностей.

        Returns:
            list[tuple] | None: Список кортежей с названиями должностей [(Name,), ...] или None в случае ошибки.
        """
        log.debug("Запрос названий всех должностей")
        result = self.db.fetch_all(q.GET_POSITIONS)
        log.debug(
            f"Получено {len(result) if result else 0} названий должностей.")
        return result

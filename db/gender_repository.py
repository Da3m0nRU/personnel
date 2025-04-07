"""
Модуль репозитория для взаимодействия с таблицей `Genders` (Пол).

Содержит методы для получения данных о полах.
"""
import logging
from db.database import Database  # Database
import db.queries as q


log = logging.getLogger(__name__)


class GenderRepository:
    """Репозиторий для работы со справочником полов."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    def get_all(self):
        """
        Возвращает все записи из справочника полов.

        Returns:
            list[tuple] | None: Список кортежей (ID, GenderName) или None в случае ошибки.
        """
        log.debug("Запрос всех записей из справочника Genders")
        result = self.db.fetch_all(q.GET_GENDERS)  # Используем self.db
        log.debug(f"Получено {len(result) if result else 0} записей о полах.")
        return result

    def get_by_id(self, gender_id):
        """
        Возвращает ID пола по его названию.

        Примечание: В текущей реализации этот метод фактически ищет по имени,
        так как параметр gender_id используется в запросе GET_GENDER_ID, который ищет по GenderName.
        Метод `get_by_name` является псевдонимом для этого метода.

        Args:
            gender_id (str): Название пола для поиска.

        Returns:
            int | None: ID найденного пола или None, если пол не найден или произошла ошибка.
        """
        log.debug(f"Запрос ID пола по названию: '{gender_id}'")
        result = self.db.fetch_one(
            q.GET_GENDER_ID, (gender_id,))  # Используем self.db
        found_id = result[0] if result else None
        log.debug(f"Результат поиска ID пола: {found_id}")
        return found_id

    def get_by_name(self, name):
        """
        Возвращает ID пола по его названию.

        Является псевдонимом для метода `get_by_id` из-за текущей реализации запроса.

        Args:
            name (str): Название пола для поиска.

        Returns:
            int | None: ID найденного пола или None, если пол не найден или произошла ошибка.
        """
        return self.get_by_id(name)

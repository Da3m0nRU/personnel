# db/role_repository.py
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class RoleRepository:
    """
    Класс для взаимодействия с таблицей Roles в базе данных.
    Предоставляет методы для получения информации о ролях пользователей.
    """

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий ролей.

        Args:
            db (Database): Экземпляр объекта для работы с базой данных.
        """
        self.db = db
        log.debug("RoleRepository инициализирован.")

    def get_id_by_name(self, role_name: str) -> int | None:
        """
        Возвращает ID роли по её названию.

        Args:
            role_name (str): Название роли (например, "Администратор").

        Returns:
            int | None: ID роли, если найдена, иначе None.
        """
        log.debug(f"Запрос ID для роли: '{role_name}'")
        query = q.GET_ROLE_ID_BY_NAME
        result = self.db.fetch_one(query, (role_name,))
        if result:
            role_id = result[0]
            log.debug(f"Найден ID={role_id} для роли '{role_name}'")
            return role_id
        else:
            log.warning(f"Роль с названием '{role_name}' не найдена.")
            return None

    def get_name_by_id(self, role_id: int) -> str | None:
        """
        Возвращает название роли по её ID.

        Args:
            role_id (int): Уникальный идентификатор роли.

        Returns:
            str | None: Название роли, если найдена, иначе None.
        """
        log.debug(f"Запрос названия роли по ID={role_id}")
        query = q.GET_ROLE_NAME_BY_ID
        result = self.db.fetch_one(query, (role_id,))
        if result:
            role_name = result[0]
            log.debug(f"Найдено название='{role_name}' для роли ID={role_id}")
            return role_name
        else:
            log.warning(f"Роль с ID={role_id} не найдена.")
            return None

    def get_all_roles(self) -> list[tuple[int, str]]:
        """
        Возвращает список всех ролей из базы данных.

        Returns:
            list[tuple[int, str]]: Список кортежей, где каждый кортеж содержит (ID, RoleName),
                                   отсортированный по названию роли.
                                   Возвращает пустой список в случае ошибки или отсутствия ролей.
        """
        log.debug("Запрос списка всех ролей")
        query = q.GET_ALL_ROLES_ORDERED
        result = self.db.fetch_all(query)
        if result is None:
            log.warning(
                "Не удалось получить список ролей (fetch_all вернул None).")
            return []  # Возвращаем пустой список при ошибке
        elif not result:
            log.info("Список ролей в базе данных пуст.")
            return []  # Возвращаем пустой список, если таблица пуста
        else:
            log.debug(f"Получено {len(result)} ролей.")
            # Возвращаем список кортежей [(id1, name1), (id2, name2), ...]
            return result

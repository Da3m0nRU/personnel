"""
Модуль репозитория для взаимодействия с таблицей `Users` (Пользователи).

Содержит методы для управления пользователями системы: CRUD операции,
аутентификация, проверка уникальности логина, получение ролей
и связанных сотрудников. Использует bcrypt для хеширования паролей.
"""
import logging
import bcrypt
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class UserRepository:
    """
    Репозиторий для управления данными пользователей системы.

    Предоставляет методы для создания, чтения, обновления, удаления (CRUD)
    пользователей, проверки паролей, получения списков пользователей,
    ролей и сотрудников для связывания.
    """

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    # --- Хеширование и проверка паролей ---

    def _hash_password(self, password: str) -> str | None:
        """
        Хеширует пароль с использованием bcrypt.

        Args:
            password (str): Пароль в открытом виде.

        Returns:
            str | None: Хеш пароля в виде строки или None, если пароль пустой.
        """
        if not password:
            log.warning("Попытка хеширования пустого пароля.")
            return None
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            return hashed_password.decode('utf-8')
        except Exception as e:
            log.error(f"Ошибка хеширования пароля: {e}", exc_info=True)
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет совпадение пароля в открытом виде с хешем.

        Args:
            plain_password (str): Пароль в открытом виде.
            hashed_password (str): Хеш пароля из базы данных.

        Returns:
            bool: True, если пароли совпадают, иначе False.
        """
        if not plain_password or not hashed_password:
            return False
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_password_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_password_bytes)
        except ValueError:
            # Может возникать, если хеш имеет неверный формат
            log.warning(f"Неверный формат хеша при проверке пароля.")
            return False
        except Exception as e:
            log.error(f"Ошибка проверки пароля: {e}", exc_info=True)
            return False

    # --- CRUD Операции и получение списков ---

    def get_users(self, search_term: str | None = None) -> tuple[list[tuple], int]:
        """
        Получает список пользователей с возможностью поиска.

        Возвращает кортеж (data, total_rows), где data - список кортежей
        с данными пользователей (ID, Login, PasswordHash, EmployeeFullName,
        EmployeePN, Email, RoleName), а total_rows - общее количество
        найденных записей. ID пользователя - первый столбец.

        Args:
            search_term (str | None, optional): Строка для поиска по логину,
                                               ФИО сотрудника, email, роли.

        Returns:
            tuple[list[tuple], int]: Кортеж (список данных пользователей, общее количество).
        """
        log.debug(f"Запрос списка пользователей: search='{search_term}'")
        base_query = q.GET_USERS_BASE
        params = {}
        if search_term:
            base_query += q.GET_USERS_SEARCH
            params["search_term"] = f"%{search_term}%"
        query = base_query + q.GET_USERS_ORDER_BY

        log.debug(f"Запрос данных пользователей: {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("Запрос данных пользователей вернул None")
            data = []

        # Запрос для подсчета строк
        count_query = q.GET_USERS_COUNT_BASE
        count_params = {}
        if search_term:
            count_query += q.GET_USERS_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0
        log.debug(
            f"Найдено пользователей: {total_rows}, получено данных: {len(data)}")

        # Замена None на пустые строки для отображения (кроме ID)
        processed_data = []
        for row in data:
            processed_row = [row[0]] + \
                ["" if item is None else item for item in row[1:]]
            processed_data.append(tuple(processed_row))  # Возвращаем кортежи

        return processed_data, total_rows

    def get_user_by_id(self, user_id: int) -> tuple | None:
        """
        Получает данные одного пользователя по ID (без JOIN).

        Args:
            user_id (int): ID пользователя.

        Returns:
            tuple | None: Кортеж (ID, Login, PasswordHash, EmployeePN, RoleID, Email)
                          или None, если пользователь не найден.
        """
        log.debug(f"Запрос пользователя по ID={user_id}")
        result = self.db.fetch_one(q.GET_USER_BY_ID, (user_id,))
        if result:
            log.debug(f"Найден пользователь ID={user_id}.")
        else:
            log.warning(f"Пользователь ID={user_id} не найден.")
        return result

    def get_user_by_login(self, login: str) -> tuple | None:
        """
        Получает ключевые данные пользователя по логину (для аутентификации).

        Args:
            login (str): Логин пользователя.

        Returns:
            tuple | None: Кортеж (ID, PasswordHash, RoleID) или None,
                          если пользователь не найден.
        """
        log.debug(f"Запрос пользователя по login='{login}' для аутентификации")
        result = self.db.fetch_one(q.GET_USER_BY_LOGIN_FOR_AUTH, (login,))
        if result:
            log.debug(f"Найден пользователь login='{login}'.")
        else:
            log.warning(f"Пользователь login='{login}' не найден.")
        return result

    def add_user(self, login: str, password: str, role_id: int,
                 employee_pn: str | None, email: str | None) -> bool:
        """
        Добавляет нового пользователя с хешированием пароля.

        Args:
            login (str): Логин нового пользователя.
            password (str): Пароль нового пользователя (будет хеширован).
            role_id (int): ID роли пользователя.
            employee_pn (str | None): Табельный номер связанного сотрудника или None.
            email (str | None): Email пользователя или None.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Добавление пользователя: login='{login}', role_id={role_id}")
        hashed_password = self._hash_password(password)
        if not hashed_password:
            log.error("Не удалось хешировать пароль при добавлении пользователя.")
            return False

        params = (login, hashed_password, employee_pn if employee_pn else None,
                  role_id, email if email else None)
        result = self.db.execute_query(q.INSERT_USER, params)
        if result:
            log.info(f"Пользователь '{login}' успешно добавлен.")
        else:
            log.error(f"Ошибка добавления пользователя '{login}'.")
        return result

    def update_user(self, user_id: int, role_id: int, employee_pn: str | None,
                    email: str | None, new_password: str | None = None) -> bool:
        """
        Обновляет данные пользователя. Пароль обновляется только при передаче new_password.

        Args:
            user_id (int): ID пользователя для обновления.
            role_id (int): Новый ID роли.
            employee_pn (str | None): Новый табельный номер связанного сотрудника или None.
            email (str | None): Новый Email или None.
            new_password (str | None, optional): Новый пароль или None, если пароль не меняется.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Обновление пользователя ID={user_id}. Пароль меняется: {new_password is not None}")
        if new_password:
            hashed_password = self._hash_password(new_password)
            if not hashed_password:
                log.error(
                    f"Не удалось хешировать новый пароль для пользователя ID={user_id}.")
                return False
            params = (role_id, employee_pn if employee_pn else None,
                      email if email else None, hashed_password, user_id)
            query = q.UPDATE_USER_WITH_PASSWORD
        else:
            params = (role_id, employee_pn if employee_pn else None,
                      email if email else None, user_id)
            query = q.UPDATE_USER_WITHOUT_PASSWORD

        result = self.db.execute_query(query, params)
        if result:
            log.info(f"Пользователь ID={user_id} успешно обновлен.")
        else:
            log.error(f"Ошибка обновления пользователя ID={user_id}.")
        return result

    def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя по ID.

        Примечание: Необходимые проверки (нельзя удалить себя, последнего админа)
        должны выполняться перед вызовом этого метода (например, в UI).

        Args:
            user_id (int): ID пользователя для удаления.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(f"Удаление пользователя ID={user_id}")
        result = self.db.execute_query(q.DELETE_USER, (user_id,))
        if result:
            log.info(f"Пользователь ID={user_id} успешно удален.")
        else:
            log.error(f"Ошибка удаления пользователя ID={user_id}.")
        return result

    # --- Вспомогательные методы ---

    def is_login_unique(self, login: str, current_user_id: int | None = None) -> bool:
        """
        Проверяет уникальность логина.

        При редактировании пользователя (current_user_id задан),
        проверка исключает текущего пользователя.

        Args:
            login (str): Логин для проверки.
            current_user_id (int | None, optional): ID текущего пользователя (при редактировании).

        Returns:
            bool: True, если логин уникален, иначе False.
        """
        log.debug(
            f"Проверка уникальности логина: '{login}', исключая ID: {current_user_id}")
        query = q.CHECK_LOGIN_UNIQUE
        params = [login]
        if current_user_id is not None:
            query += " AND ID != ?"
            params.append(current_user_id)
        result = self.db.fetch_one(query, tuple(params))
        is_unique = result is None
        log.debug(f"Логин '{login}' уникален: {is_unique}")
        return is_unique

    def get_roles(self) -> list[tuple[int, str]]:
        """
        Возвращает список всех ролей, упорядоченный по названию.

        Returns:
            list[tuple[int, str]]: Список кортежей (RoleID, RoleName).
        """
        log.debug("Запрос списка ролей")
        result = self.db.fetch_all(q.GET_ALL_ROLES_ORDERED)
        if result is None:
            log.warning("Не удалось получить список ролей.")
            return []
        log.debug(f"Получено {len(result)} ролей.")
        return result

    def get_active_employees_for_linking(self) -> list[str]:
        """
        Возвращает список работающих сотрудников для привязки к пользователю.

        Returns:
            list[str]: Список строк вида "Фамилия Имя (Таб.№)".
        """
        log.debug("Запрос списка активных сотрудников для связи с пользователем")
        query = q.GET_ACTIVE_EMPLOYEES_FOR_LINKING
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить список сотрудников для связи.")
            return []
        employee_list = [f"{emp[1]} ({emp[0]})" for emp in result]
        log.debug(f"Загружено {len(employee_list)} сотрудников для связи.")
        return employee_list

    def get_admin_count(self) -> int:
        """
        Возвращает количество пользователей с ролью 'Администратор'.

        Returns:
            int: Количество администраторов.
        """
        log.debug("Запрос количества администраторов")
        query = q.GET_ADMIN_COUNT
        result = self.db.fetch_one(query)
        count = result[0] if result else 0
        log.debug(f"Найдено администраторов: {count}")
        return count

    def get_user_role_id(self, user_id: int) -> int | None:
        """
        Возвращает ID роли пользователя по его ID.

        Args:
            user_id (int): ID пользователя.

        Returns:
            int | None: ID роли или None, если пользователь не найден.
        """
        log.debug(f"Запрос RoleID для пользователя ID={user_id}")
        result = self.db.fetch_one(q.GET_USER_ROLE_ID_BY_USER_ID, (user_id,))
        role_id = result[0] if result else None
        log.debug(f"RoleID для пользователя ID={user_id}: {role_id}")
        return role_id

    def get_admin_role_id(self) -> int | None:
        """
        Возвращает ID роли 'Администратор'.

        Предполагается, что такая роль существует и имеет фиксированное название.

        Returns:
            int | None: ID роли администратора или None, если роль не найдена.
        """
        log.debug("Запрос ID роли 'Администратор'")
        result = self.db.fetch_one(q.GET_ADMIN_ROLE_ID)
        role_id = result[0] if result else None
        if role_id is None:
            log.error(
                "Не удалось найти ID роли 'Администратор'. Проверьте наличие роли в таблице Roles.")
        log.debug(f"ID роли 'Администратор': {role_id}")
        return role_id

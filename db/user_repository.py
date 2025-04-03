# db/user_repository.py
import logging
from db.database import Database
import db.queries as q  # Предполагаем, что запросы будут добавлены в queries.py
import bcrypt  # Используем bcrypt для хеширования

log = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def _hash_password(self, password):
        """Хеширует пароль с использованием bcrypt."""
        if not password:
            return None
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password.decode('utf-8')  # Храним хеш как строку

    def verify_password(self, plain_password, hashed_password):
        """Проверяет совпадение пароля с хешем."""
        if not plain_password or not hashed_password:
            return False
        password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)

    def get_users(self, search_term=None):
        """
        Получает список пользователей с поиском (логин, ФИО сотрудника, email, роль).
        Возвращает (data, total_rows). ID пользователя - первый столбец.
        Пароль (хеш) включен для отображения в таблице.
        """
        log.debug(f"Вызов get_users с search_term={search_term}")

        base_query = q.GET_USERS_BASE  # Основной запрос с JOIN
        params = {}
        if search_term:
            base_query += q.GET_USERS_SEARCH
            params["search_term"] = f"%{search_term}%"
        query = base_query + q.GET_USERS_ORDER_BY

        log.debug(f"Итоговый запрос (get_users): {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("get_users вернул None")
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
            f"get_users: Найдено строк: {total_rows}, получено данных: {len(data)}")

        # Замена None на пустые строки для отображения (кроме ID)
        processed_data = []
        for row in data:
            # ID (row[0]) оставляем как есть, остальное заменяем
            processed_row = [row[0]] + \
                ["" if item is None else item for item in row[1:]]
            processed_data.append(processed_row)

        return processed_data, total_rows

    def get_user_by_id(self, user_id):
        """Получает данные одного пользователя по ID (без JOIN)."""
        log.debug(f"Запрос пользователя по ID={user_id}")
        result = self.db.fetch_one(q.GET_USER_BY_ID, (user_id,))
        log.debug(f"get_user_by_id вернул: {result}")
        return result  # (ID, Login, PasswordHash, EmployeePN, RoleID, Email)

    def get_user_by_login(self, login):
        """Получает данные пользователя по логину (для входа)."""
        log.debug(f"Запрос пользователя по login='{login}'")
        # Нужен запрос, возвращающий как минимум ID, хеш пароля и ID роли
        result = self.db.fetch_one(q.GET_USER_BY_LOGIN_FOR_AUTH, (login,))
        log.debug(f"get_user_by_login вернул: {result}")
        return result  # (ID, PasswordHash, RoleID) или что-то подобное

    def add_user(self, login, password, role_id, employee_pn, email):
        """Добавляет нового пользователя с хешированием пароля."""
        log.debug(
            f"Добавление пользователя: login='{login}', role_id={role_id}, employee_pn='{employee_pn}', email='{email}'")
        hashed_password = self._hash_password(password)
        if not hashed_password:
            log.error("Не удалось хешировать пароль при добавлении пользователя.")
            return False

        params = (login, hashed_password, employee_pn if employee_pn else None,
                  role_id, email if email else None)
        result = self.db.execute_query(q.INSERT_USER, params)
        log.debug(f"Результат добавления пользователя: {result}")
        return result

    def update_user(self, user_id, role_id, employee_pn, email, new_password=None):
        """Обновляет данные пользователя. Пароль обновляется, только если передан new_password."""
        log.debug(
            f"Обновление пользователя ID={user_id}: role_id={role_id}, employee_pn='{employee_pn}', email='{email}', new_password есть: {new_password is not None}")

        if new_password:
            hashed_password = self._hash_password(new_password)
            if not hashed_password:
                log.error("Не удалось хешировать новый пароль при обновлении.")
                return False
            params = (role_id, employee_pn if employee_pn else None,
                      email if email else None, hashed_password, user_id)
            query = q.UPDATE_USER_WITH_PASSWORD
        else:
            params = (role_id, employee_pn if employee_pn else None,
                      email if email else None, user_id)
            query = q.UPDATE_USER_WITHOUT_PASSWORD

        result = self.db.execute_query(query, params)
        log.debug(f"Результат обновления пользователя ID={user_id}: {result}")
        return result

    def delete_user(self, user_id):
        """Удаляет пользователя по ID."""
        # !!! Важно: Добавить проверки (нельзя удалить себя, нельзя последнего админа) ЛИБО в UsersFrame, ЛИБО здесь!
        # Проще сделать в UsersFrame перед вызовом этого метода.
        log.debug(f"Удаление пользователя ID={user_id}")
        result = self.db.execute_query(q.DELETE_USER, (user_id,))
        log.debug(f"Результат удаления пользователя: {result}")
        return result

    def is_login_unique(self, login, current_user_id=None):
        """Проверяет уникальность логина. Исключает current_user_id при редактировании."""
        log.debug(
            f"Проверка уникальности логина: '{login}', исключая ID: {current_user_id}")
        query = "SELECT 1 FROM Users WHERE Login = ?"
        params = [login]
        if current_user_id is not None:
            query += " AND ID != ?"
            params.append(current_user_id)
        result = self.db.fetch_one(query, tuple(params))
        is_unique = result is None
        log.debug(f"Логин '{login}' уникален: {is_unique}")
        return is_unique

    def get_roles(self):
        """Возвращает список ролей (ID, RoleName)."""
        log.debug("Запрос списка ролей")
        result = self.db.fetch_all(
            "SELECT ID, RoleName FROM Roles ORDER BY RoleName")
        if result is None:
            log.warning("Не удалось получить список ролей.")
            return []
        return result  # Список кортежей [(1, 'Администратор'), ...]

    def get_active_employees_for_linking(self):
        """Возвращает список работающих сотрудников (Таб.№, ФИО) для связи с пользователем."""
        log.debug("Запрос списка активных сотрудников для связи")
        query = """
            SELECT PersonnelNumber, LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '') AS FullName
            FROM Employees
            WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
            ORDER BY LastName, FirstName;
        """
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить список сотрудников для связи.")
            return []
        # Формируем строки для ComboBox: "Фамилия Имя (Таб.№)"
        employee_list = [f"{emp[1]} ({emp[0]})" for emp in result]
        log.debug(f"Загружено {len(employee_list)} сотрудников для связи.")
        return employee_list

    def get_admin_count(self):
        """Возвращает количество пользователей с ролью Администратор."""
        log.debug("Запрос количества администраторов")
        query = "SELECT COUNT(U.ID) FROM Users U JOIN Roles R ON U.RoleID = R.ID WHERE R.RoleName = 'Администратор'"
        result = self.db.fetch_one(query)
        count = result[0] if result else 0
        log.debug(f"Найдено администраторов: {count}")
        return count

    def get_user_role_id(self, user_id):
        """Возвращает RoleID пользователя по его ID."""
        log.debug(f"Запрос RoleID для пользователя ID={user_id}")
        result = self.db.fetch_one(
            "SELECT RoleID FROM Users WHERE ID = ?", (user_id,))
        role_id = result[0] if result else None
        log.debug(f"RoleID для ID={user_id}: {role_id}")
        return role_id

    def get_admin_role_id(self):
        """Возвращает ID роли 'Администратор'."""
        log.debug("Запрос ID роли Администратор")
        result = self.db.fetch_one(
            "SELECT ID FROM Roles WHERE RoleName = 'Администратор'")
        role_id = result[0] if result else None
        log.debug(f"Admin Role ID: {role_id}")
        return role_id

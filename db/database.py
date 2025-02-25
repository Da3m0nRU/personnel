# db/database.py
import sqlite3
from config import DATABASE_PATH
import db.queries as q
import logging
from gui.utils import configure_logging

log = logging.getLogger(__name__)


class Database:
    """
    Класс для взаимодействия с базой данных SQLite.
    """

    def __init__(self, db_path=DATABASE_PATH):
        """
        Инициализирует подключение к базе данных.

        Args:
            db_path (str): Путь к файлу базы данных. По умолчанию берется из config.py.
        """
        log.debug(f"Инициализация объекта Database с путём к БД: {db_path}")
        self.conn = None
        self.cursor = None
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            log.debug(f"Успешное подключение к базе данных: {db_path}")
        except sqlite3.Error as e:
            log.error(f"Ошибка подключения к базе данных: {e}")

    def execute_query(self, query, params=None):
        """
        Выполняет SQL-запрос (INSERT, UPDATE, DELETE и т.д.).

        Args:
            query (str): SQL-запрос.
            params (tuple, optional): Параметры для запроса (защита от SQL-инъекций).

        Returns:
            bool: True, если запрос выполнен успешно, иначе False.
        """
        log.debug(f"Выполнение запроса: {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            log.debug("Запрос успешно выполнен")
            return True
        except sqlite3.Error as e:
            log.exception(
                f"Ошибка выполнения SQL: {e}, запрос: {query}, параметры: {params}")
            self.conn.rollback()
            return False

    def fetch_all(self, query, params=None):
        """
        Выполняет SQL-запрос и возвращает все результаты (SELECT).

        Args:
            query (str): SQL-запрос.
            params (tuple, optional): Параметры для запроса.

        Returns:
            list: Список кортежей с результатами запроса.  Пустой список, если результатов нет.
                 None в случае ошибки.
        """
        log.debug(
            f"Выполнение запроса fetch_all: {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchall()
            log.debug(f"Запрос выполнен, получено {len(result)} строк")
            return result
        except sqlite3.Error as e:
            log.exception(
                f"Ошибка выполнения SQL: {e}, запрос: {query}, параметры: {params}")
            return None

    def fetch_one(self, query, params=None):
        """
        Выполняет SQL-запрос и возвращает один результат (SELECT).

        Args:
            query (str): SQL-запрос.
            params (tuple, optional): Параметры для запроса.

        Returns:
            tuple: Кортеж с результатом запроса.  None, если результатов нет или произошла ошибка.
        """
        log.debug(
            f"Выполнение запроса fetch_one: {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchone()
            log.debug(f"Запрос выполнен, результат: {result}")
            return result

        except sqlite3.Error as e:
            log.exception(
                f"Ошибка выполнения SQL: {e}, запрос: {query}, параметры: {params}")
            return None

    def close(self):
        """
        Закрывает соединение с базой данных.
        """
        log.debug("Закрытие соединения с базой данных")
        if self.conn:
            self.conn.close()
            log.debug("Соединение с базой данных закрыто.")

    def get_employees(self, page=1, per_page=10, search_term=None):
        """
        Получает список сотрудников с пагинацией и поиском.

        Args:
            page (int): Номер страницы (начиная с 1).
            per_page (int): Количество записей на странице.
            search_term (str, optional): Строка поиска.

        Returns:
            tuple: Кортеж (data, total_rows), где:
                data - список кортежей с данными сотрудников на текущей странице.
                total_rows - общее количество найденных сотрудников (с учетом поиска).
                Если произошла ошибка, возвращает (None, 0).
        """
        log.debug(
            f"Вызов get_employees с параметрами: page={page}, per_page={per_page}, search_term={search_term}")
        offset = (page - 1) * per_page
        limit = per_page
        query = q.GET_EMPLOYEES
        params = []

        if search_term:
            log.debug(f"Добавление условия поиска: {search_term}")
            query += """
               AND (E.PersonnelNumber LIKE ?
                   OR E.LastName LIKE ?
                   OR E.FirstName LIKE ?
                   OR E.MiddleName LIKE ?)
            """
            params.extend([f"%{search_term}%"] * 4)

        query += " ORDER BY E.PersonnelNumber LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        log.debug(f"Итоговый запрос: {query}, параметры: {params}")
        data = self.fetch_all(query, params)

        if data is None:
            log.warning("get_employees вернул None")
            return None, 0

        count_query = q.GET_EMPLOYEES_COUNT
        count_params = []
        if search_term:
            count_query += """
               AND (E.PersonnelNumber LIKE ?
                   OR E.LastName LIKE ?
                   OR E.FirstName LIKE ?
                   OR E.MiddleName LIKE ?)
            """
            count_params.extend([f"%{search_term}%"] * 4)

        log.debug(
            f"Запрос для подсчета количества: {count_query}, параметры: {count_params}")
        total_rows = self.fetch_one(count_query, count_params)[0]
        log.debug(
            f"get_employees: общее количество строк: {total_rows}, получено данных {len(data) if data else 0}")
        return data, total_rows

    def get_departments_for_position(self, position_id):
        """
        Получает список отделов, связанных с указанной должностью.

        Args:
            position_id (int): ID должности.

        Returns:
            list: Список кортежей с названиями отделов.  Пустой список, если отделов нет.
                 None в случае ошибки.
        """
        log.debug(
            f"Вызов get_departments_for_position с position_id={position_id}")
        result = self.fetch_all(q.GET_DEPARTMENTS_FOR_POSITION, (position_id,))
        log.debug(f"get_departments_for_position вернул: {result}")
        return result

    def get_positions(self):
        """
        Получает список всех должностей.

        Returns:
            list: Список кортежей с названиями должностей.  Пустой список, если должностей нет.
                None в случае ошибки.
        """
        log.debug("Вызов get_positions")
        result = self.fetch_all(q.GET_POSITIONS)
        log.debug(f"get_positions вернул: {result}")
        return result

    def delete_employee(self, personnel_number):
        """
        Удаляет сотрудника по табельному номеру.

        Args:
            personnel_number (str): Табельный номер сотрудника.

        Returns:
            bool: True, если сотрудник успешно удален, False в противном случае.
        """
        log.debug(
            f"Вызов delete_employee с personnel_number={personnel_number}")
        result = self.execute_query(q.DELETE_EMPLOYEE, (personnel_number,))
        log.debug(f"delete_employee вернул: {result}")
        return result

    def get_employee_by_personnel_number(self, personnel_number):
        """
        Возвращает данные сотрудника по табельному номеру.

        Args:
            personnel_number (str): Табельный номер сотрудника.

        Returns:
            tuple: Кортеж с данными сотрудника. None, если сотрудник не найден.
        """
        log.debug(
            f"Вызов get_employee_by_personnel_number с personnel_number={personnel_number}")
        result = self.fetch_one(
            q.GET_EMPLOYEE_BY_PERSONNEL_NUMBER, (personnel_number,))
        log.debug(f"get_employee_by_personnel_number вернул: {result}")
        return result

    def update_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """
        Обновляет данные сотрудника в базе данных.

        Args:
            personnel_number (str): Табельный номер сотрудника.
            lastname (str): Фамилия.
            firstname (str): Имя.
            middlename (str): Отчество.
            birth_date_str (str): Дата рождения в формате "ГГГГ-ММ-ДД".
            gender_id (int): ID пола.
            position_id (int): ID должности.
            department_id (int): ID отдела.
            state_id (int): ID состояния.

        Returns:
            bool: True, если данные успешно обновлены, False в противном случае.
        """
        log.debug(
            f"Вызов update_employee с данными: personnel_number={personnel_number}, lastname={lastname}, firstname={firstname}, middlename={middlename}, birth_date_str={birth_date_str}, gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")

        params = (lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id, personnel_number)
        result = self.execute_query(q.UPDATE_EMPLOYEE, params)
        log.debug(f"update_employee вернул: {result}")
        return result

    def get_genders(self):
        """
        Возвращает все записи из таблицы Genders.
        Returns:
            list: Список кортежей.
        """
        log.debug(f"Вызван get_genders")
        result = self.fetch_all(q.GET_GENDERS)
        log.debug(f"get_genders вернул: {result}")
        return result

    def get_all_positions(self):
        """
        Возвращает все записи из Positions.
        Returns:
            list: Список кортежей.
        """
        log.debug(f"Вызван get_all_positions")
        result = self.fetch_all(q.GET_ALL_POSITIONS)
        log.debug(f"get_all_positions вернул: {result}")
        return result

    def get_states(self):
        """
        Возвращает все записи из States.
        Returns:
            list: Список кортежей.
        """
        log.debug(f"Вызван get_states")
        result = self.fetch_all(q.GET_STATES)
        log.debug(f"get_states вернул: {result}")
        return result

    def get_departments(self):
        """
        Возвращает все записи из Departments.
        Returns:
            list: Список кортежей.
        """
        log.debug(f"Вызван get_departments")
        result = self.fetch_all(q.GET_DEPARTMENTS)
        log.debug(f"get_departments вернул: {result}")
        return result

    def get_gender_id(self, gender_name):
        """
        Возвращает ID пола по названию.

        Args:
            gender_name (str): Название пола.

        Returns:
            int: ID пола, или None, если пол не найден.
        """
        log.debug(f"Вызван get_gender_id с gender_name={gender_name}")
        result = self.fetch_one(q.GET_GENDER_ID, (gender_name,))
        log.debug(f"get_gender_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_position_id(self, position_name):
        """
        Возвращает ID должности по названию.

        Args:
            position_name (str): Название должности.

        Returns:
            int: ID должности, или None, если должность не найдена.
        """
        log.debug(f"Вызван get_position_id с position_name={position_name}")
        result = self.fetch_one(q.GET_POSITION_ID, (position_name,))
        log.debug(f"get_position_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_state_id(self, state_name):
        """
        Возвращает ID состояния по названию.

        Args:
            state_name (str): Название состояния.

        Returns:
            int: ID состояния, или None, если состояние не найдено.
        """
        log.debug(f"Вызван get_state_id с state_name={state_name}")
        result = self.fetch_one(q.GET_STATE_ID, (state_name,))
        log.debug(f"get_state_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_department_by_name(self, department_name):
        """
        Возвращает ID отдела по его названию.

        Args:
            department_name (str): Название отдела

        Returns:
            int: ID отдела
        """
        log.debug(
            f"Вызван get_department_by_name с department_name='{department_name}'")

        result = self.fetch_all(q.GET_DEPARTMENT_BY_NAME, (department_name,))
        log.debug(f"get_department_by_name вернул: {result}")
        return result

    def insert_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """
        Добавление нового сотрудника

        Args:
            personnel_number (str): Табельный номер сотрудника.
            lastname (str): Фамилия.
            firstname (str): Имя.
            middlename (str): Отчество.
            birth_date_str (str): Дата рождения в формате "ГГГГ-ММ-ДД".
            gender_id (int): ID пола.
            position_id (int): ID должности.
            department_id (int): ID отдела.
            state_id (int): ID состояния.

        Returns:
            bool: True, если данные успешно добавлены, False в противном случае.
        """
        log.debug(
            f"Вызван insert_employee с данными: personnel_number={personnel_number}, lastname={lastname}, firstname={firstname}, middlename={middlename}, birth_date_str={birth_date_str}, gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")
        params = (personnel_number, lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id)
        result = self.execute_query(q.INSERT_EMPLOYEE, params)
        log.debug(f"insert_employee вернул: {result}")  # !!!
        return result

    def personnel_number_exists(self, personnel_number):
        """
        Проверяет, существует ли сотрудник с заданным табельным номером.

        Args:
            personnel_number (str): Табельный номер.

        Returns:
            bool: True, если существует, False в противном случае.
        """
        log.debug(
            f"Проверка существования табельного номера: {personnel_number}")  # !!!
        result = self.fetch_one(
            "SELECT 1 FROM Employees WHERE PersonnelNumber = ?", (personnel_number,))
        log.debug(f"Результат проверки: {result is not None}")  # !!!
        return result is not None

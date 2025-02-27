# db/database.py
import sqlite3
from config import DATABASE_PATH
import db.queries as q  # Импортируем модуль queries
import logging


log = logging.getLogger(__name__)


class Database:
    """
    Класс для взаимодействия с базой данных SQLite.
    """

    def __init__(self, db_path=DATABASE_PATH):
        """
        Инициализирует подключение к базе данных.
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

    def get_departments_for_position(self, position_id):
        log.debug(
            f"Вызов get_departments_for_position с position_id={position_id}")
        result = self.fetch_all(q.GET_DEPARTMENTS_FOR_POSITION, (position_id,))
        log.debug(f"get_departments_for_position вернул: {result}")
        return result

    def get_positions(self):
        log.debug("Вызов get_positions")
        result = self.fetch_all(q.GET_POSITIONS)  # !!! исправил
        log.debug(f"get_positions вернул: {result}")
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
        """
        log.debug(f"Вызван get_gender_id с gender_name={gender_name}")
        result = self.fetch_one(q.GET_GENDER_ID, (gender_name,))
        log.debug(f"get_gender_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_position_id(self, position_name):
        """
        Возвращает ID должности по названию
        """
        log.debug(f"Вызван get_position_id с position_name={position_name}")
        result = self.fetch_one(q.GET_POSITION_ID, (position_name,))
        log.debug(f"get_position_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_state_id(self, state_name):
        """
        Возвращает ID состояния по названию.
        """
        log.debug(f"Вызван get_state_id с state_name={state_name}")
        result = self.fetch_one(q.GET_STATE_ID, (state_name,))
        log.debug(f"get_state_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_department_by_name(self, department_name):
        """
        Возвращает ID отдела по его названию.
        """
        log.debug(
            f"Вызван get_department_by_name с department_name='{department_name}'")
        result = self.fetch_all(q.GET_DEPARTMENT_BY_NAME, (department_name,))
        log.debug(f"get_department_by_name вернул: {result}")
        return result

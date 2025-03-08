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

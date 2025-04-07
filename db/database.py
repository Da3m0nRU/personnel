# db/database.py
"""
Модуль для взаимодействия с базой данных SQLite.

Предоставляет класс `Database` для установки соединения, выполнения
SQL-запросов (включая SELECT, INSERT, UPDATE, DELETE), получения результатов
и управления транзакциями (commit, rollback), а также закрытия соединения.
"""
import sqlite3
import logging
from config import DATABASE_PATH

log = logging.getLogger(__name__)


class Database:
    """
    Класс-обертка для управления соединением и выполнением запросов
    к базе данных SQLite.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Инициализирует объект Database и устанавливает соединение с БД.

        Args:
            db_path (str, optional): Путь к файлу базы данных SQLite.
                                     По умолчанию используется значение из `config.DATABASE_PATH`.
        """
        log.debug(f"Инициализация Database с путем к БД: {db_path}")
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        try:
            # connect() создает файл, если он не существует
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            log.info(f"Успешное подключение к базе данных: {db_path}")
        except sqlite3.Error as e:
            log.error(
                f"Ошибка подключения к базе данных SQLite ({db_path}): {e}", exc_info=True)
            # В случае ошибки подключения self.conn и self.cursor останутся None

    def execute_query(self, query: str, params: tuple | dict | None = None) -> bool:
        """
        Выполняет SQL-запрос, изменяющий данные (INSERT, UPDATE, DELETE).

        Автоматически подтверждает (commit) транзакцию в случае успеха
        или откатывает (rollback) в случае ошибки.

        Args:
            query (str): SQL-запрос для выполнения.
            params (tuple | dict, optional): Параметры для подстановки в SQL-запрос.
                                             Может быть кортежем для `?` плейсхолдеров
                                             или словарем для именованных плейсхолдеров.

        Returns:
            bool: True в случае успешного выполнения и commit, False в случае ошибки и rollback.
        """
        if not self.conn or not self.cursor:
            log.error("Попытка выполнить запрос без активного соединения с БД.")
            return False

        log.debug(
            f"Выполнение запроса (execute): {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            log.debug(
                "Запрос успешно выполнен и транзакция подтверждена (commit).")
            return True
        except sqlite3.Error as e:
            log.exception(f"Ошибка выполнения SQL запроса (execute): {e}\n" +
                          f"Запрос: {query}\nПараметры: {params}")
            try:
                self.conn.rollback()
                log.warning("Транзакция отменена (rollback) из-за ошибки.")
            except sqlite3.Error as rb_err:
                log.error(
                    f"Ошибка при попытке отката транзакции: {rb_err}", exc_info=True)
            return False

    def fetch_all(self, query: str, params: tuple | dict | None = None) -> list[tuple] | None:
        """
        Выполняет SQL-запрос SELECT и возвращает все найденные строки.

        Args:
            query (str): SQL-запрос SELECT.
            params (tuple | dict, optional): Параметры для подстановки в SQL-запрос.

        Returns:
            list[tuple] | None: Список кортежей с результатами запроса.
                                Возвращает пустой список [], если ничего не найдено.
                                Возвращает None в случае ошибки выполнения запроса.
        """
        if not self.conn or not self.cursor:
            log.error(
                "Попытка выполнить запрос fetch_all без активного соединения с БД.")
            return None

        log.debug(
            f"Выполнение запроса (fetch_all): {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchall()
            log.debug(
                f"Запрос fetch_all выполнен, получено строк: {len(result) if result is not None else 'None'}")
            return result  # fetchall() возвращает [] если ничего не найдено
        except sqlite3.Error as e:
            log.exception(f"Ошибка выполнения SQL запроса (fetch_all): {e}\n" +
                          f"Запрос: {query}\nПараметры: {params}")
            return None

    def fetch_one(self, query: str, params: tuple | dict | None = None) -> tuple | None:
        """
        Выполняет SQL-запрос SELECT и возвращает одну (первую) строку.

        Args:
            query (str): SQL-запрос SELECT.
            params (tuple | dict, optional): Параметры для подстановки в SQL-запрос.

        Returns:
            tuple | None: Кортеж с данными первой строки результата.
                          Возвращает None, если запрос не вернул строк или произошла ошибка.
        """
        if not self.conn or not self.cursor:
            log.error(
                "Попытка выполнить запрос fetch_one без активного соединения с БД.")
            return None

        log.debug(
            f"Выполнение запроса (fetch_one): {query} с параметрами: {params}")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchone()
            log.debug(
                f"Запрос fetch_one выполнен, результат: {'Найден' if result else 'Не найден или ошибка'}")
            return result  # fetchone() возвращает None если ничего не найдено
        except sqlite3.Error as e:
            log.exception(f"Ошибка выполнения SQL запроса (fetch_one): {e}\n" +
                          f"Запрос: {query}\nПараметры: {params}")
            return None

    def close(self) -> None:
        """
        Закрывает курсор и соединение с базой данных, если они были установлены.
        """
        log.debug("Попытка закрытия соединения с базой данных")
        if self.cursor:
            try:
                self.cursor.close()
                log.debug("Курсор базы данных закрыт.")
            except sqlite3.Error as e:
                log.error(
                    f"Ошибка при закрытии курсора БД: {e}", exc_info=True)
        if self.conn:
            try:
                self.conn.close()
                log.info("Соединение с базой данных успешно закрыто.")
            except sqlite3.Error as e:
                log.error(
                    f"Ошибка при закрытии соединения с БД: {e}", exc_info=True)
        else:
            log.debug("Соединение с БД не было открыто или уже закрыто.")

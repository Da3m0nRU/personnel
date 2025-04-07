"""
Модуль репозитория для взаимодействия с таблицей `Employees` (Сотрудники).

Содержит методы для CRUD операций с сотрудниками, а также
методы для получения агрегированных данных (статистика, списки для отчетов и т.д.).
"""
from db.database import Database
import db.queries as q
import logging

log = logging.getLogger(__name__)


class EmployeeRepository:
    """Репозиторий для управления данными сотрудников."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    # --- CRUD Операции ---

    def get_employees(self, search_term=None, employee_pn_filter=None):
        """
        Получает список сотрудников с поиском и фильтрацией по табельному номеру.

        Args:
            search_term (str, optional): Строка для поиска по различным полям.
            employee_pn_filter (str, optional): Табельный номер для точной фильтрации.

        Returns:
            tuple[list[tuple] | None, int]: Кортеж, содержащий:
                - Список кортежей с данными сотрудников или None при ошибке.
                - Общее количество найденных строк (с учетом фильтров).
        """
        log.debug(
            f"Запрос сотрудников: search='{search_term}', filter_pn='{employee_pn_filter}'")
        query = q.GET_EMPLOYEES
        params = {}

        if employee_pn_filter:
            query += " AND E.PersonnelNumber = :pn_filter "
            params["pn_filter"] = employee_pn_filter

        if search_term:
            query += q.GET_EMPLOYEES_SEARCH
            params["search_term"] = f"%{search_term}%"

        query += q.GET_EMPLOYEES_ORDER_BY

        log.debug(f"Запрос данных: {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("Запрос данных сотрудников вернул None")
            return None, 0

        # Подсчет количества с теми же фильтрами
        count_query = q.GET_EMPLOYEES_COUNT
        count_params = {}
        if employee_pn_filter:
            count_query += " AND E.PersonnelNumber = :pn_filter "
            count_params["pn_filter"] = employee_pn_filter
        if search_term:
            count_query += q.GET_EMPLOYEES_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"

        log.debug(
            f"Запрос количества: {count_query}, параметры: {count_params}")
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0

        log.debug(
            f"Найдено сотрудников: {total_rows}, получено данных: {len(data)}")
        return data, total_rows

    def get_employee_by_personnel_number(self, personnel_number):
        """
        Получает данные одного сотрудника по его табельному номеру.

        Args:
            personnel_number (str): Табельный номер сотрудника.

        Returns:
            tuple | None: Кортеж с данными сотрудника или None, если не найден или произошла ошибка.
        """
        log.debug(f"Запрос сотрудника по таб. номеру: {personnel_number}")
        result = self.db.fetch_one(
            q.GET_EMPLOYEE_BY_PERSONNEL_NUMBER, (personnel_number,))
        log.debug(
            f"Результат поиска сотрудника {personnel_number}: {'Найден' if result else 'Не найден'}")
        return result

    def insert_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """
        Добавляет нового сотрудника в базу данных.

        Args:
            personnel_number (str): Табельный номер.
            lastname (str): Фамилия.
            firstname (str): Имя.
            middlename (str): Отчество.
            birth_date_str (str): Дата рождения (ГГГГ-ММ-ДД).
            gender_id (int): ID пола.
            position_id (int): ID должности.
            department_id (int): ID отдела.
            state_id (int): ID состояния.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Добавление нового сотрудника: таб.№={personnel_number}, ФИО={lastname} {firstname} {middlename}")
        params = (personnel_number, lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id)
        result = self.db.execute_query(q.INSERT_EMPLOYEE, params)
        log.debug(
            f"Результат добавления сотрудника {personnel_number}: {result}")
        return result

    def update_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """
        Обновляет данные существующего сотрудника.

        Args:
            personnel_number (str): Табельный номер сотрудника для обновления.
            lastname (str): Новая фамилия.
            firstname (str): Новое имя.
            middlename (str): Новое отчество.
            birth_date_str (str): Новая дата рождения (ГГГГ-ММ-ДД).
            gender_id (int): Новый ID пола.
            position_id (int): Новый ID должности.
            department_id (int): Новый ID отдела.
            state_id (int): Новый ID состояния.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(f"Обновление данных сотрудника: таб.№={personnel_number}")
        params = (lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id, personnel_number)
        result = self.db.execute_query(q.UPDATE_EMPLOYEE, params)
        log.debug(
            f"Результат обновления сотрудника {personnel_number}: {result}")
        return result

    def delete_employee(self, personnel_number):
        """
        Удаляет сотрудника из базы данных.

        Args:
            personnel_number (str): Табельный номер сотрудника для удаления.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(f"Удаление сотрудника: таб.№={personnel_number}")
        result = self.db.execute_query(q.DELETE_EMPLOYEE, (personnel_number,))
        log.debug(
            f"Результат удаления сотрудника {personnel_number}: {result}")
        return result

    # --- Проверки и вспомогательные методы ---

    def personnel_number_exists(self, personnel_number):
        """
        Проверяет, существует ли сотрудник с заданным табельным номером.

        Args:
            personnel_number (str): Табельный номер для проверки.

        Returns:
            bool: True, если сотрудник существует, иначе False.
        """
        log.debug(f"Проверка существования таб. номера: {personnel_number}")
        result = self.db.fetch_one(
            q.CHECK_PERSONNEL_NUMBER_EXISTS, (personnel_number,))
        exists = result is not None
        log.debug(
            f"Результат проверки таб. номера {personnel_number}: {exists}")
        return exists

    # --- Методы для статистики и отчетов ---

    def get_active_employee_count(self):
        """Возвращает количество работающих сотрудников."""
        log.debug("Запрос количества работающих сотрудников")
        query = q.GET_ACTIVE_EMPLOYEE_COUNT
        result = self.db.fetch_one(query)
        count = result[0] if result else 0
        log.debug(f"Найдено работающих сотрудников: {count}")
        return count

    def get_employees_count_by_department(self):
        """Возвращает распределение работающих сотрудников по отделам."""
        log.debug("Запрос распределения сотрудников по отделам")
        query = q.GET_EMPLOYEES_COUNT_BY_DEPARTMENT
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить распределение по отделам.")
            return []
        log.debug(f"Получено распределение по {len(result)} отделам.")
        return result

    def get_employees_count_by_position(self, limit=7):
        """Возвращает топ N должностей по количеству работающих сотрудников."""
        log.debug(f"Запрос топ-{limit} должностей по количеству сотрудников")
        query = q.GET_EMPLOYEES_COUNT_BY_POSITION_TOP_N
        result = self.db.fetch_all(query, (limit,))
        if result is None:
            log.warning("Не удалось получить распределение по должностям.")
            return []
        log.debug(f"Получено топ-{len(result)} должностей.")
        return result

    def get_active_employee_birth_dates(self):
        """Возвращает список дат рождения работающих сотрудников."""
        log.debug("Запрос дат рождения работающих сотрудников")
        query = q.GET_ACTIVE_EMPLOYEE_BIRTH_DATES
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить даты рождения.")
            return []
        birth_dates = [row[0] for row in result]
        log.debug(f"Получено {len(birth_dates)} дат рождения.")
        return birth_dates

    def get_gender_distribution(self):
        """Возвращает гендерное распределение работающих сотрудников."""
        log.debug("Запрос гендерного распределения сотрудников")
        query = q.GET_GENDER_DISTRIBUTION
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить гендерное распределение.")
            return []
        log.debug(f"Получено гендерное распределение: {result}")
        return result

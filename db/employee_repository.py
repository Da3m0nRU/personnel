# db/employee_repository.py
from db.database import Database  # Импортируем Database
import db.queries as q  # Импортируем SQL запросы

import logging
log = logging.getLogger(__name__)


class EmployeeRepository:  # !!! название класса
    def __init__(self, db: Database):
        self.db = db

    def get_employees(self, search_term=None, employee_pn_filter=None):
        """
        Получает список сотрудников с поиском и возможностью фильтрации по таб. номеру.
        """
        log.debug(
            f"Вызов get_employees с search_term={search_term}, employee_pn_filter={employee_pn_filter}")

        query = q.GET_EMPLOYEES  # Основной запрос
        # Используем словарь для параметров, чтобы избежать путаницы с позициями
        params = {}

        # --- Добавляем фильтр по сотруднику ---
        if employee_pn_filter:
            query += " AND E.PersonnelNumber = :pn_filter "  # Добавляем условие WHERE
            params["pn_filter"] = employee_pn_filter      # Добавляем параметр
        # --------------------------------------

        if search_term:
            query += q.GET_EMPLOYEES_SEARCH  # Добавляем условие поиска
            # Добавляем параметр поиска
            params["search_term"] = f"%{search_term}%"

        query += q.GET_EMPLOYEES_ORDER_BY  # Сортировка

        log.debug(
            f"Итоговый запрос (get_employees): {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)  # Передаем словарь параметров
        if data is None:
            log.warning("get_employees вернул None")
            return None, 0

        # --- Запрос для подсчета количества (тоже с фильтрами) ---
        count_query = q.GET_EMPLOYEES_COUNT
        count_params = {}

        if employee_pn_filter:
            count_query += " AND E.PersonnelNumber = :pn_filter "
            count_params["pn_filter"] = employee_pn_filter

        if search_term:
            count_query += q.GET_EMPLOYEES_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"

        log.debug(
            f"Запрос для подсчета количества: {count_query}, параметры: {count_params}")
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0
        # ---------------------------------------------------------

        log.debug(
            f"get_employees: общее количество строк: {total_rows}, получено данных {len(data) if data else 0}")
        return data, total_rows

    def get_employee_by_personnel_number(self, personnel_number):
        log.debug(
            f"Вызов get_employee_by_personnel_number с personnel_number={personnel_number}")
        result = self.db.fetch_one(
            q.GET_EMPLOYEE_BY_PERSONNEL_NUMBER, (personnel_number,))
        log.debug(f"get_employee_by_personnel_number вернул: {result}")
        return result

    def insert_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """
        Добавление нового сотрудника
        """
        log.debug(
            f"Вызван insert_employee с данными: personnel_number={personnel_number}, lastname={lastname}, firstname={firstname}, middlename={middlename}, birth_date_str={birth_date_str}, gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")
        params = (personnel_number, lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id)
        result = self.db.execute_query(q.INSERT_EMPLOYEE, params)
        log.debug(f"insert_employee вернул: {result}")  # !!!
        return result

    def delete_employee(self, personnel_number):
        log.debug(
            f"Вызов delete_employee с personnel_number={personnel_number}")
        result = self.db.execute_query(q.DELETE_EMPLOYEE, (personnel_number,))
        log.debug(f"delete_employee вернул: {result}")
        return result

    def update_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        log.debug(
            f"Вызов update_employee с данными: personnel_number={personnel_number}, lastname={lastname}, firstname={firstname}, middlename={middlename}, birth_date_str={birth_date_str}, gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")

        params = (lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id, personnel_number)
        result = self.db.execute_query(q.UPDATE_EMPLOYEE, params)
        log.debug(f"update_employee вернул: {result}")
        return result

    def personnel_number_exists(self, personnel_number):
        """Проверяет, существует ли сотрудник с заданным табельным номером."""
        log.debug(
            f"Проверка существования табельного номера: {personnel_number}")
        result = self.db.fetch_one(
            q.CHECK_PERSONNEL_NUMBER_EXISTS, (personnel_number,))
        log.debug(f"Результат проверки: {result is not None}")
        return result is not None

    def get_active_employee_count(self):
        """Возвращает количество работающих сотрудников."""
        log.debug("Запрос количества работающих сотрудников")
        query = q.GET_ACTIVE_EMPLOYEE_COUNT
        result = self.db.fetch_one(query)
        count = result[0] if result else 0
        log.debug(f"Найдено работающих сотрудников: {count}")
        return count

    def get_employees_count_by_department(self):
        """Возвращает список кортежей (Название отдела, Количество сотрудников) для работающих."""
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
        result = self.db.fetch_all(
            query, (limit,))  # Передаем limit как параметр
        if result is None:
            log.warning("Не удалось получить распределение по должностям.")
            return []
        log.debug(f"Получено топ-{len(result)} должностей.")
        return result

    def get_active_employee_birth_dates(self):
        """Возвращает список дат рождения (строки 'YYYY-MM-DD') работающих сотрудников."""
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
        """Возвращает список кортежей (Пол, Количество сотрудников) для работающих."""
        log.debug("Запрос гендерного распределения сотрудников")
        query = q.GET_GENDER_DISTRIBUTION
        result = self.db.fetch_all(query)
        if result is None:
            log.warning("Не удалось получить гендерное распределение.")
            return []
        log.debug(f"Получено гендерное распределение: {result}")
        return result

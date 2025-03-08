# db/employee_repository.py
from db.database import Database  # Импортируем Database
import db.queries as q  # Импортируем SQL запросы

import logging
log = logging.getLogger(__name__)


class EmployeeRepository:  # !!! название класса
    def __init__(self, db: Database):
        self.db = db

    def get_employees(self, search_term=None):
        """
        Получает список сотрудников с поиском.
        """
        log.debug(
            f"Вызов get_employees с параметрами: search_term={search_term}")

        #  Собираем запрос
        query = q.GET_EMPLOYEES  # Основной запрос
        params = []

        if search_term:
            # Добавляем условие поиска, используя именованные параметры
            query += q.GET_EMPLOYEES_SEARCH
            params = {"search_term": f"%{search_term}%"}  # !!!

        query += q.GET_EMPLOYEES_ORDER_BY  # Добавляем сортировку

        log.debug(f"Итоговый запрос: {query}, параметры: {params}")

        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("get_employees вернул None")
            return None, 0

        #  Запрос для подсчета количества записей (с учетом поиска).
        count_query = q.GET_EMPLOYEES_COUNT
        count_params = []
        if search_term:
            count_query += q.GET_EMPLOYEES_COUNT_SEARCH  # !!!
            count_params = {"search_term": f"%{search_term}%"}

        log.debug(
            f"Запрос для подсчета количества: {count_query}, параметры: {count_params}")
        total_rows = self.db.fetch_one(count_query, count_params)[0]
        log.debug(
            f"get_employees: общее количество строк: {total_rows}, получено данных {len(data) if data else 0}")

        return data, total_rows

    def get_employee_by_personnel_number(self, personnel_number):
        log.debug(
            f"Вызов get_employee_by_personnel_number с personnel_number={personnel_number}")
        result = self.fetch_one(
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
        result = self.execute_query(q.INSERT_EMPLOYEE, params)
        log.debug(f"insert_employee вернул: {result}")  # !!!
        return result

    def delete_employee(self, personnel_number):
        log.debug(
            f"Вызов delete_employee с personnel_number={personnel_number}")
        result = self.execute_query(q.DELETE_EMPLOYEE, (personnel_number,))
        log.debug(f"delete_employee вернул: {result}")
        return result

    def update_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        log.debug(
            f"Вызов update_employee с данными: personnel_number={personnel_number}, lastname={lastname}, firstname={firstname}, middlename={middlename}, birth_date_str={birth_date_str}, gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")

        params = (lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id, personnel_number)
        result = self.execute_query(q.UPDATE_EMPLOYEE, params)
        log.debug(f"update_employee вернул: {result}")
        return result

    def personnel_number_exists(self, personnel_number):
        """Проверяет, существует ли сотрудник с заданным табельным номером."""
        log.debug(
            f"Проверка существования табельного номера: {personnel_number}")
        result = self.fetch_one(
            "SELECT 1 FROM Employees WHERE PersonnelNumber = ?", (personnel_number,))
        log.debug(f"Результат проверки: {result is not None}")
        return result is not None

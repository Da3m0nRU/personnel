# db/employee_event_repository.py
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class EmployeeEventRepository:
    def __init__(self, db: Database):
        self.db = db

    def insert_event(self, personnel_number, event_id, event_date, department_id, position_id, reason=None):
        """Добавляет запись о кадровом событии."""
        log.debug(
            f"Добавление кадрового события: personnel_number={personnel_number}, event_id={event_id}, event_date={event_date}, department_id={department_id}, position_id={position_id}, reason={reason}")

        params = (personnel_number, event_id, event_date,
                  department_id, position_id, reason)
        result = self.db.execute_query(
            q.INSERT_EMPLOYEE_EVENT, params)

        log.debug(f"Результат добавления кадрового события: {result}")
        return result

    def get_events(self, search_term=None):
        """
        Получает список всех кадровых событий с возможностью поиска.
        Возвращает данные и общее количество строк (с учетом поиска).
        """
        log.debug(f"Вызов get_events с параметрами: search_term={search_term}")

        query = q.GET_EMPLOYEE_EVENTS
        params = {}  # Используем словарь для именованных параметров

        if search_term:
            query += q.GET_EMPLOYEE_EVENTS_SEARCH
            params["search_term"] = f"%{search_term}%"

        query += q.GET_EMPLOYEE_EVENTS_ORDER_BY  # Добавляем сортировку

        log.debug(
            f"Итоговый запрос (get_events): {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)

        if data is None:
            log.warning("get_events вернул None для данных")
            data = []  # Возвращаем пустой список, а не None

        # Запрос для подсчета общего количества строк (с учетом поиска)
        count_query = q.GET_EMPLOYEE_EVENTS_COUNT
        count_params = {}
        if search_term:
            count_query += q.GET_EMPLOYEE_EVENTS_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"

        log.debug(
            f"Запрос для подсчета (get_events): {count_query}, параметры: {count_params}")
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0

        log.debug(
            f"get_events: Найдено строк: {total_rows}, получено данных: {len(data)}")

        return data, total_rows

# db/employee_event_repository.py
import logging
from db.database import Database
import db.queries as q
import datetime

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

       # --- Методы для отчетов ---
    def get_dismissal_counts_by_month(self, start_date, end_date):
        # ... (Код метода прежний) ...
        log.debug(f"Запрос увольнений по месяцам: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_MONTH, (start_date, end_date))
        if result is None:
            log.warning(...)
            return []
        log.debug(f"Получено {len(result)} записей по месяцам.")
        return result

    # НОВЫЙ метод
    def get_dismissal_counts_by_day(self, start_date, end_date):
        """ Получает количество увольнений по дням за период. """
        log.debug(f"Запрос увольнений по дням: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_DAY, (start_date, end_date))
        if result is None:
            log.warning("Запрос увольнений по дням не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей по дням.")
        return result

    # НОВЫЙ метод
    def get_dismissal_counts_by_year(self, start_date, end_date):
        """ Получает количество увольнений по годам за период. """
        log.debug(f"Запрос увольнений по годам: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_YEAR, (start_date, end_date))
        if result is None:
            log.warning("Запрос увольнений по годам не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей по годам.")
        return result

    def get_dismissed_employees_details(self, start_date, end_date):
        # ... (Код метода прежний) ...
        log.debug(f"Запрос деталей уволенных: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSED_EMPLOYEES_DETAILS, (start_date, end_date))
        if result is None:
            log.warning(...)
            return []
        log.debug(f"Получено {len(result)} записей уволенных.")
        processed = [tuple("" if item is None else item for item in row)
                     for row in result]
        return processed

    def get_event_count_last_days(self, event_name, days=30):
        """Возвращает количество указанных событий за последние N дней."""
        log.debug(
            f"Запрос количества событий '{event_name}' за последние {days} дней")
        end_date = datetime.date.today()
        # Включая сегодняшний день
        start_date = end_date - datetime.timedelta(days=days-1)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        query = q.GET_EVENT_COUNT_LAST_DAYS

        result = self.db.fetch_one(
            query, (event_name, start_date_str, end_date_str))
        count = result[0] if result else 0
        log.debug(f"Найдено событий '{event_name}' за {days} дней: {count}")
        return count

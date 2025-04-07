"""
Модуль репозитория для взаимодействия с таблицей `EmployeeEvents` (Кадровые события).

Содержит методы для добавления и получения списка кадровых событий,
а также методы для формирования данных для отчетов.
"""
import logging
from db.database import Database
import db.queries as q
import datetime

log = logging.getLogger(__name__)


class EmployeeEventRepository:
    """Репозиторий для управления данными кадровых событий сотрудников."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    # --- Основные операции ---

    def insert_event(self, personnel_number, event_id, event_date, department_id, position_id, reason=None):
        """
        Добавляет новую запись о кадровом событии.

        Args:
            personnel_number (str): Табельный номер сотрудника.
            event_id (int): ID типа события.
            event_date (str): Дата события (ГГГГ-ММ-ДД).
            department_id (int | None): ID нового отдела (если применимо).
            position_id (int | None): ID новой должности (если применимо).
            reason (str | None, optional): Причина события.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Добавление кадрового события: PN={personnel_number}, EventID={event_id}, Date={event_date}")
        params = (personnel_number, event_id, event_date,
                  department_id, position_id, reason)
        result = self.db.execute_query(q.INSERT_EMPLOYEE_EVENT, params)
        log.debug(f"Результат добавления кадрового события: {result}")
        return result

    def get_events(self, search_term=None):
        """
        Получает список всех кадровых событий с возможностью поиска.

        Args:
            search_term (str, optional): Строка для поиска по различным полям события.

        Returns:
            tuple[list[tuple], int]: Кортеж, содержащий:
                - Список кортежей с данными событий.
                - Общее количество найденных событий (с учетом поиска).
        """
        log.debug(f"Запрос списка кадровых событий: search='{search_term}'")
        query = q.GET_EMPLOYEE_EVENTS
        params = {}

        if search_term:
            query += q.GET_EMPLOYEE_EVENTS_SEARCH
            params["search_term"] = f"%{search_term}%"

        query += q.GET_EMPLOYEE_EVENTS_ORDER_BY

        log.debug(f"Запрос данных событий: {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("Запрос данных кадровых событий вернул None")
            data = []

        # Подсчет количества с теми же фильтрами
        count_query = q.GET_EMPLOYEE_EVENTS_COUNT
        count_params = {}
        if search_term:
            count_query += q.GET_EMPLOYEE_EVENTS_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"

        log.debug(
            f"Запрос количества событий: {count_query}, параметры: {count_params}")
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0

        log.debug(
            f"Найдено кадровых событий: {total_rows}, получено данных: {len(data)}")
        return data, total_rows

    # --- Методы для отчетов --- # TODO: Перенести логику отчетов в отдельный модуль/сервис

    def get_dismissal_counts_by_month(self, start_date, end_date):
        """Получает количество увольнений по месяцам за период."""
        log.debug(f"Запрос увольнений по месяцам: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_MONTH, (start_date, end_date))
        if result is None:
            log.warning("Запрос увольнений по месяцам не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей увольнений по месяцам.")
        return result

    def get_dismissal_counts_by_day(self, start_date, end_date):
        """Получает количество увольнений по дням за период."""
        log.debug(f"Запрос увольнений по дням: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_DAY, (start_date, end_date))
        if result is None:
            log.warning("Запрос увольнений по дням не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей увольнений по дням.")
        return result

    def get_dismissal_counts_by_year(self, start_date, end_date):
        """Получает количество увольнений по годам за период."""
        log.debug(f"Запрос увольнений по годам: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSAL_COUNT_BY_YEAR, (start_date, end_date))
        if result is None:
            log.warning("Запрос увольнений по годам не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей увольнений по годам.")
        return result

    def get_dismissed_employees_details(self, start_date, end_date):
        """Получает детализированную информацию об уволенных сотрудниках за период."""
        log.debug(
            f"Запрос деталей уволенных сотрудников: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_DISMISSED_EMPLOYEES_DETAILS, (start_date, end_date))
        if result is None:
            log.warning(
                "Запрос деталей уволенных сотрудников не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей об уволенных сотрудниках.")
        # Обработка None значений в кортежах
        processed = [tuple("" if item is None else item for item in row)
                     for row in result]
        return processed

    # --- Методы для Dashboard ---

    def get_event_count_last_days(self, event_name, days=30):
        """
        Возвращает количество указанных событий за последние N дней.

        Args:
            event_name (str): Название события (например, 'Прием', 'Увольнение').
            days (int, optional): Количество последних дней для подсчета. По умолчанию 30.

        Returns:
            int: Количество событий.
        """
        log.debug(
            f"Запрос количества событий '{event_name}' за последние {days} дней")
        end_date = datetime.date.today()
        start_date = end_date - \
            datetime.timedelta(days=days-1)  # Включая сегодня
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        query = q.GET_EVENT_COUNT_LAST_DAYS
        result = self.db.fetch_one(
            query, (event_name, start_date_str, end_date_str))
        count = result[0] if result else 0
        log.debug(f"Найдено событий '{event_name}' за {days} дней: {count}")
        return count

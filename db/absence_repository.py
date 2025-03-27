# db/absence_repository.py
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class AbsenceRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_absences(self, search_term=None):
        """
        Получает список всех отсутствий с возможностью поиска.
        Возвращает данные и общее количество строк.
        """
        log.debug(
            f"Вызов get_absences с параметрами: search_term={search_term}")

        query = q.GET_ABSENCES
        params = {}

        if search_term:
            query += q.GET_ABSENCES_SEARCH
            params["search_term"] = f"%{search_term}%"

        query += q.GET_ABSENCES_ORDER_BY

        log.debug(
            f"Итоговый запрос (get_absences): {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)

        if data is None:
            log.warning("get_absences вернул None для данных")
            data = []

        # Запрос для подсчета строк
        count_query = q.GET_ABSENCES_COUNT
        count_params = {}
        if search_term:
            count_query += q.GET_ABSENCES_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"

        log.debug(
            f"Запрос для подсчета (get_absences): {count_query}, параметры: {count_params}")
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0

        log.debug(
            f"get_absences: Найдено строк: {total_rows}, получено данных: {len(data)}")

        # Замена None на пустые строки для корректного отображения в таблице
        processed_data = []
        for row in data:
            processed_row = ["" if item is None else item for item in row]
            processed_data.append(processed_row)

        return processed_data, total_rows

    # !!! Добавлен schedule_id
    def insert_absence(self, personnel_number, absence_date, full_day, start_time, end_time, reason, schedule_id):
        """
        Добавляет запись об отсутствии.
        Время start_time и end_time записываются всегда.
        """
        log.debug(
            f"Добавление отсутствия (время всегда): Таб.№={personnel_number}, Дата={absence_date}, ПолныйДень={full_day}, "
            f"Начало={start_time}, Конец={end_time}, Причина='{reason}', ScheduleID={schedule_id}"
        )

        # !!! УБИРАЕМ УСЛОВНУЮ УСТАНОВКУ В None !!!
        # actual_start_time = None if full_day == 1 else start_time
        # actual_end_time = None if full_day == 1 else end_time
        # Теперь просто используем переданные start_time и end_time

        # Проверка на случай, если из диалога всё же пришёл None (хотя не должен при новой логике)
        # Заглушка на всякий случай
        actual_start_time = start_time if start_time is not None else "00:00"
        actual_end_time = end_time if end_time is not None else "00:00"  # Заглушка

        # !!! Параметры теперь передаются как есть !!!
        params = (personnel_number, absence_date, full_day,
                  actual_start_time, actual_end_time, reason, schedule_id)
        result = self.db.execute_query(q.INSERT_ABSENCE, params)

        if result:
            log.info(
                f"Запись об отсутствии для {personnel_number} на {absence_date} успешно добавлена (время записано).")
        else:
            log.error(
                f"Ошибка добавления записи об отсутствии для {personnel_number} на {absence_date}.")

        return result

    def get_employee_list(self):
        """Возвращает список работающих сотрудников (Таб.№, ФИО) для ComboBox."""
        log.debug("Запрос списка сотрудников для диалога отсутствий")
        employees = self.db.fetch_all(q.GET_EMPLOYEE_LIST_FOR_ABSENCE)
        if employees is None:
            log.warning(
                "Не удалось получить список сотрудников для диалога отсутствий.")
            return []
        return [f"{emp[1]} ({emp[0]})" for emp in employees]

    def get_working_hours(self, position_id, day_of_week_id):
        """
        Получает ScheduleID, время начала и конца работы для должности и дня недели.

        Args:
            position_id (int): ID должности сотрудника.
            day_of_week_id (int): ID дня недели (1-7, Пн=1).

        Returns:
            tuple: (schedule_id, start_time, end_time) или None, если график не найден.
        """
        log.debug(
            f"Запрос рабочих часов для PositionID={position_id}, DayOfWeekID={day_of_week_id}")
        result = self.db.fetch_one(
            q.GET_WORKING_HOURS_FOR_POSITION_AND_DAY, (position_id, day_of_week_id))
        if result:
            log.debug(
                f"Найден график: ScheduleID={result[0]}, Start={result[1]}, End={result[2]}")
            return result  # (schedule_id, start_time, end_time)
        else:
            log.warning(
                f"График работы для PositionID={position_id}, DayOfWeekID={day_of_week_id} не найден.")
            return None

    def get_employee_position_id(self, personnel_number):
        """ Получает ID должности сотрудника по его табельному номеру. """
        log.debug(f"Запрос PositionID для сотрудника {personnel_number}")
        # Простой запрос, можно не выносить в queries.py
        query = "SELECT PositionID FROM Employees WHERE PersonnelNumber = ?"
        result = self.db.fetch_one(query, (personnel_number,))
        if result:
            log.debug(f"PositionID для {personnel_number}: {result[0]}")
            return result[0]
        else:
            log.error(
                f"Не удалось найти PositionID для сотрудника {personnel_number}")
            return None

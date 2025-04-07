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
        Получает список всех отсутствий с поиском. Возвращает (data, total_rows).
        ПЕРВЫЙ СТОЛБЕЦ в data - ЭТО A.ID!
        """
        log.debug(
            f"Вызов get_absences с параметрами: search_term={search_term}")

        query = q.GET_ABSENCES  # Уже включает A.ID
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

        # Подсчет строк
        count_query = q.GET_ABSENCES_COUNT
        count_params = {}
        if search_term:
            count_query += q.GET_ABSENCES_COUNT_SEARCH
            count_params["search_term"] = f"%{search_term}%"
        count_result = self.db.fetch_one(count_query, count_params)
        total_rows = count_result[0] if count_result else 0
        log.debug(
            f"get_absences: Найдено строк: {total_rows}, получено данных: {len(data)}")

        # Замена None на пустые строки (кроме ID)
        processed_data = []
        for row in data:
            processed_row = [row[0]] + \
                ["" if item is None else item for item in row[1:]]
            processed_data.append(processed_row)

        return processed_data, total_rows

    # --- НОВЫЕ МЕТОДЫ ---
    def get_absence_by_id(self, absence_id):
        """ Получает одну запись об отсутствии по её ID. """
        log.debug(f"Запрос записи об отсутствии по ID={absence_id}")
        result = self.db.fetch_one(q.GET_ABSENCE_BY_ID, (absence_id,))
        if result:
            log.debug(f"Найдена запись: {result}")
            return result
        else:
            log.error(f"Запись об отсутствии с ID={absence_id} не найдена.")
            return None

    def update_absence(self, absence_id, absence_date, full_day, start_time, end_time, reason, schedule_id, personnel_number):
        """ Обновляет существующую запись об отсутствии. """
        log.debug(
            f"Обновление отсутствия ID={absence_id}: Дата={absence_date}, ПолныйДень={full_day}, "
            f"Начало={start_time}, Конец={end_time}, Причина='{reason}', ScheduleID={schedule_id}, Таб№={personnel_number}"
        )
        actual_start_time = start_time if start_time is not None else "00:00"
        actual_end_time = end_time if end_time is not None else "00:00"

        params = (
            absence_date, actual_start_time, actual_end_time, reason, schedule_id, personnel_number,
            absence_id  # ID последним для WHERE
        )
        # !!! ИСПРАВЛЕНИЕ порядка параметров в UPDATE_ABSENCE запросе
        # Correct order for UPDATE_ABSENCE query based on queries.py
        params = (
            absence_date,       # 1
            full_day,         # 2 - Забыл в первой версии
            actual_start_time,  # 3
            actual_end_time,    # 4
            reason,           # 5
            schedule_id,      # 6
            personnel_number,  # 7
            absence_id        # 8 (for WHERE)
        )

        result = self.db.execute_query(q.UPDATE_ABSENCE, params)
        if result:
            log.info(
                f"Запись об отсутствии ID={absence_id} успешно обновлена.")
        else:
            log.error(
                f"Ошибка при обновлении записи об отсутствии ID={absence_id}.")
        return result

    def delete_absence(self, absence_id):
        """ Удаляет запись об отсутствии по её ID. """
        log.debug(f"Удаление записи об отсутствии с ID={absence_id}")
        result = self.db.execute_query(q.DELETE_ABSENCE, (absence_id,))
        if result:
            log.info(f"Запись об отсутствии ID={absence_id} успешно удалена.")
        else:
            log.error(
                f"Ошибка при удалении записи об отсутствии ID={absence_id}.")
        return result
    # ---------------------

    def insert_absence(self, personnel_number, absence_date, full_day, start_time, end_time, reason, schedule_id):
        """ Добавляет запись об отсутствии. Время start_time и end_time записываются всегда. """
        log.debug(
            f"Добавление отсутствия (время всегда): Таб.№={personnel_number}, Дата={absence_date}, ПолныйДень={full_day}, "
            f"Начало={start_time}, Конец={end_time}, Причина='{reason}', ScheduleID={schedule_id}"
        )
        actual_start_time = start_time if start_time is not None else "00:00"
        actual_end_time = end_time if end_time is not None else "00:00"
        params = (personnel_number, absence_date, full_day,
                  actual_start_time, actual_end_time, reason, schedule_id)
        result = self.db.execute_query(q.INSERT_ABSENCE, params)
        if result:
            log.info(
                f"Запись об отсутствии для {personnel_number} на {absence_date} успешно добавлена.")
        else:
            log.error(
                f"Ошибка добавления записи об отсутствии для {personnel_number} на {absence_date}.")
        return result

    def get_employee_list(self):
        """Возвращает список работающих сотрудников (Таб.№, ФИО) для ComboBox."""
        log.debug("Запрос списка сотрудников для диалога отсутствий")
        employees = self.db.fetch_all(q.GET_EMPLOYEE_LIST_FOR_ABSENCE)
        if employees is None:
            log.warning("Не удалось получить список сотрудников.")
            return []
        return [f"{emp[1]} ({emp[0]})" for emp in employees]

    def get_working_hours(self, position_id, day_of_week_id):
        """ Получает ScheduleID, время начала и конца работы для должности и дня недели. """
        log.debug(
            f"Запрос рабочих часов для PositionID={position_id}, DayOfWeekID={day_of_week_id}")
        result = self.db.fetch_one(
            q.GET_WORKING_HOURS_FOR_POSITION_AND_DAY, (position_id, day_of_week_id))
        if result:
            log.debug(
                f"Найден график: ScheduleID={result[0]}, Start={result[1]}, End={result[2]}")
        else:
            log.warning(
                f"График работы для PositionID={position_id}, DayOfWeekID={day_of_week_id} не найден.")
        return result  # (schedule_id, start_time, end_time) or None

    def get_employee_position_id(self, personnel_number):
        """ Получает ID должности сотрудника по его табельному номеру. """
        log.debug(f"Запрос PositionID для сотрудника {personnel_number}")
        query = q.GET_EMPLOYEE_POSITION_ID_BY_PN
        result = self.db.fetch_one(query, (personnel_number,))
        if result:
            log.debug(f"PositionID для {personnel_number}: {result[0]}")
            return result[0]
        else:
            log.error(
                f"Не удалось найти PositionID для сотрудника {personnel_number}")
            return None

    def absence_exists(self, personnel_number, absence_date):
        """
        Проверяет, существует ли уже запись об отсутствии для данного сотрудника
        на указанную дату.
        Возвращает True, если существует, иначе False.
        """
        log.debug(
            f"Проверка существования отсутствия для {personnel_number} на {absence_date}")
        query = q.CHECK_ABSENCE_EXISTS_BY_PN_DATE
        result = self.db.fetch_one(query, (personnel_number, absence_date))
        exists = result is not None
        log.debug(
            f"Результат проверки: {'Найдено' if exists else 'Не найдено'}")
        return exists

    def get_absences_details_for_period(self, start_date, end_date):
        """ Получает детали всех записей отсутствий за заданный период. """
        log.debug(
            f"Запрос деталей отсутствий для отчета: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_ABSENCES_DETAILS_FOR_REPORT, (start_date, end_date))
        if result is None:
            log.warning(
                "Запрос деталей отсутствий для отчета не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей отсутствий для отчета.")
        # Возвращаем как есть (список кортежей)
        return result

    def get_employee_fio_map(self):
        """
        Возвращает словарь {PersonnelNumber: "Фамилия Имя Отчество"}.
        Используется для быстрого получения ФИО в отчете.
        """
        log.debug("Запрос карты сотрудников (Таб.номер -> ФИО)")
        # Запрос можно не выносить в queries.py, он простой
        query = q.GET_EMPLOYEE_FIO_MAP_DATA
        employees = self.db.fetch_all(query)
        if employees is None:
            log.error("Не удалось получить список сотрудников для карты ФИО.")
            return {}
        fio_map = {emp[0]: emp[1] for emp in employees}
        log.debug(f"Создана карта ФИО для {len(fio_map)} сотрудников.")
        return fio_map

    def get_raw_absence_data(self, start_date, end_date):
        """
        Получает "сырые" данные об отсутствиях за период для последующего расчета сумм.
        Возвращает список кортежей или пустой список.
        """
        log.debug(
            f"Запрос сырых данных отсутствий за период: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_RAW_ABSENCE_DATA_FOR_SUMMATION, (start_date, end_date))
        if result is None:
            log.warning("Запрос сырых данных отсутствий не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} сырых записей об отсутствии.")
        # Здесь не делаем замену None на '', т.к. None важен для логики расчета
        return result

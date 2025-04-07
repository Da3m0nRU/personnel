"""
Модуль репозитория для взаимодействия с таблицей `Absences` (Отсутствия).

Содержит методы для CRUD операций с записями об отсутствии сотрудников,
а также методы для получения списков, проверки данных и формирования данных для отчетов.
"""
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class AbsenceRepository:
    """Репозиторий для управления данными об отсутствии сотрудников."""

    def __init__(self, db: Database):
        """
        Инициализирует репозиторий.

        Args:
            db (Database): Экземпляр подключения к базе данных.
        """
        self.db = db

    # --- CRUD Операции ---

    def get_absences(self, search_term=None):
        """
        Получает список всех отсутствий с возможностью поиска.

        Первый столбец в возвращаемых данных - ID записи об отсутствии.

        Args:
            search_term (str, optional): Строка для поиска по различным полям.

        Returns:
            tuple[list[tuple], int]: Кортеж, содержащий:
                - Список кортежей с данными отсутствий (включая ID).
                - Общее количество найденных записей (с учетом поиска).
        """
        log.debug(f"Запрос списка отсутствий: search='{search_term}'")
        query = q.GET_ABSENCES
        params = {}
        if search_term:
            query += q.GET_ABSENCES_SEARCH
            params["search_term"] = f"%{search_term}%"
        query += q.GET_ABSENCES_ORDER_BY

        log.debug(f"Запрос данных отсутствий: {query}, параметры: {params}")
        data = self.db.fetch_all(query, params)
        if data is None:
            log.warning("Запрос данных отсутствий вернул None")
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
            f"Найдено отсутствий: {total_rows}, получено данных: {len(data)}")

        # Замена None на пустые строки (кроме ID)
        processed_data = []
        for row in data:
            processed_row = [row[0]] + \
                ["" if item is None else item for item in row[1:]]
            processed_data.append(processed_row)

        return processed_data, total_rows

    def get_absence_by_id(self, absence_id):
        """
        Получает одну запись об отсутствии по её ID.

        Args:
            absence_id (int): ID записи об отсутствии.

        Returns:
            tuple | None: Кортеж с данными записи или None, если не найдено.
        """
        log.debug(f"Запрос записи об отсутствии по ID={absence_id}")
        result = self.db.fetch_one(q.GET_ABSENCE_BY_ID, (absence_id,))
        if result:
            log.debug(f"Найдена запись об отсутствии ID={absence_id}.")
        else:
            log.error(f"Запись об отсутствии с ID={absence_id} не найдена.")
        return result

    def insert_absence(self, personnel_number, absence_date, full_day, start_time, end_time, reason, schedule_id):
        """
        Добавляет новую запись об отсутствии.

        Args:
            personnel_number (str): Табельный номер сотрудника.
            absence_date (str): Дата отсутствия (ГГГГ-ММ-ДД).
            full_day (int): 1 для полного дня, 0 для частичного.
            start_time (str | None): Время начала (ЧЧ:ММ) или None.
            end_time (str | None): Время окончания (ЧЧ:ММ) или None.
            reason (str): Причина отсутствия.
            schedule_id (int | None): ID графика работы (если full_day=1) или None.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Добавление отсутствия: PN={personnel_number}, Date={absence_date}, FullDay={full_day}")
        # Записываем 00:00, если время не указано (для консистентности, хотя может быть избыточно)
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

    def update_absence(self, absence_id, absence_date, full_day, start_time, end_time, reason, schedule_id, personnel_number):
        """
        Обновляет существующую запись об отсутствии.

        Args:
            absence_id (int): ID записи для обновления.
            absence_date (str): Новая дата отсутствия.
            full_day (int): Новое значение флага полного дня.
            start_time (str | None): Новое время начала.
            end_time (str | None): Новое время окончания.
            reason (str): Новая причина.
            schedule_id (int | None): Новый ID графика.
            personnel_number (str): Табельный номер сотрудника (не изменяется, но нужен для запроса).

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(
            f"Обновление отсутствия ID={absence_id}: Date={absence_date}, FullDay={full_day}")
        actual_start_time = start_time if start_time is not None else "00:00"
        actual_end_time = end_time if end_time is not None else "00:00"
        # Параметры должны соответствовать порядку в q.UPDATE_ABSENCE
        params = (absence_date, full_day, actual_start_time, actual_end_time,
                  reason, schedule_id, personnel_number, absence_id)
        result = self.db.execute_query(q.UPDATE_ABSENCE, params)
        if result:
            log.info(
                f"Запись об отсутствии ID={absence_id} успешно обновлена.")
        else:
            log.error(
                f"Ошибка при обновлении записи об отсутствии ID={absence_id}.")
        return result

    def delete_absence(self, absence_id):
        """
        Удаляет запись об отсутствии по её ID.

        Args:
            absence_id (int): ID записи для удаления.

        Returns:
            bool: True в случае успеха, False при ошибке.
        """
        log.debug(f"Удаление записи об отсутствии с ID={absence_id}")
        result = self.db.execute_query(q.DELETE_ABSENCE, (absence_id,))
        if result:
            log.info(f"Запись об отсутствии ID={absence_id} успешно удалена.")
        else:
            log.error(
                f"Ошибка при удалении записи об отсутствии ID={absence_id}.")
        return result

    # --- Вспомогательные методы и проверки ---

    def absence_exists(self, personnel_number, absence_date):
        """
        Проверяет, существует ли запись об отсутствии для сотрудника на указанную дату.

        Args:
            personnel_number (str): Табельный номер сотрудника.
            absence_date (str): Дата для проверки (ГГГГ-ММ-ДД).

        Returns:
            bool: True, если запись существует, иначе False.
        """
        log.debug(
            f"Проверка существования отсутствия для PN={personnel_number} на {absence_date}")
        query = q.CHECK_ABSENCE_EXISTS_BY_PN_DATE
        result = self.db.fetch_one(query, (personnel_number, absence_date))
        exists = result is not None
        log.debug(
            f"Результат проверки отсутствия: {'Найдено' if exists else 'Не найдено'}")
        return exists

    def get_employee_list(self):
        """
        Возвращает список работающих сотрудников для использования в ComboBox.

        Returns:
            list[str]: Список строк вида "Фамилия Имя Отчество (Таб.№)".
        """
        log.debug("Запрос списка сотрудников для диалога отсутствий")
        employees = self.db.fetch_all(q.GET_EMPLOYEE_LIST_FOR_ABSENCE)
        if employees is None:
            log.warning(
                "Не удалось получить список сотрудников для диалога отсутствий.")
            return []
        return [f"{emp[1]} ({emp[0]})" for emp in employees]

    def get_working_hours(self, position_id, day_of_week_id):
        """
        Получает ID графика и время начала/конца работы для должности и дня недели.

        Args:
            position_id (int): ID должности.
            day_of_week_id (int): ID дня недели (1=Пн, ..., 7=Вс).

        Returns:
            tuple | None: Кортеж (schedule_id, start_time, end_time) или None, если график не найден.
        """
        log.debug(
            f"Запрос рабочих часов: PosID={position_id}, DayOfWeekID={day_of_week_id}")
        result = self.db.fetch_one(
            q.GET_WORKING_HOURS_FOR_POSITION_AND_DAY, (position_id, day_of_week_id))
        if result:
            log.debug(
                f"Найден график: SchedID={result[0]}, Start={result[1]}, End={result[2]}")
        else:
            log.warning(
                f"График работы для PosID={position_id}, DayOfWeekID={day_of_week_id} не найден.")
        return result

    def get_employee_position_id(self, personnel_number):
        """
        Получает ID должности сотрудника по его табельному номеру.

        Args:
            personnel_number (str): Табельный номер сотрудника.

        Returns:
            int | None: ID должности или None, если сотрудник или должность не найдены.
        """
        log.debug(f"Запрос PositionID для сотрудника PN={personnel_number}")
        query = q.GET_EMPLOYEE_POSITION_ID_BY_PN
        result = self.db.fetch_one(query, (personnel_number,))
        if result:
            position_id = result[0]
            log.debug(f"PositionID для PN={personnel_number}: {position_id}")
            return position_id
        else:
            log.error(
                f"Не удалось найти PositionID для сотрудника PN={personnel_number}")
            return None

    # --- Методы для отчетов --- # TODO: Перенести логику отчетов

    def get_absences_details_for_period(self, start_date, end_date):
        """
        Получает детали всех записей отсутствий за заданный период для отчета.

        Args:
            start_date (str): Начальная дата периода (ГГГГ-ММ-ДД).
            end_date (str): Конечная дата периода (ГГГГ-ММ-ДД).

        Returns:
            list[tuple]: Список кортежей с деталями отсутствий.
        """
        log.debug(
            f"Запрос деталей отсутствий для отчета: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_ABSENCES_DETAILS_FOR_REPORT, (start_date, end_date))
        if result is None:
            log.warning(
                "Запрос деталей отсутствий для отчета не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} записей отсутствий для отчета.")
        return result

    def get_employee_fio_map(self):
        """
        Возвращает словарь {PersonnelNumber: "Фамилия Имя Отчество"}.

        Используется для быстрого получения ФИО в отчете.

        Returns:
            dict[str, str]: Словарь с табельными номерами и ФИО.
        """
        log.debug("Запрос карты сотрудников (Таб.номер -> ФИО)")
        query = q.GET_EMPLOYEE_FIO_MAP_DATA
        employees = self.db.fetch_all(query)
        if employees is None:
            log.error("Не удалось получить список сотрудников для карты ФИО.")
            return {}
        fio_map = {str(emp[0]): emp[1]
                   for emp in employees}  # Убедимся, что ключ - строка
        log.debug(f"Создана карта ФИО для {len(fio_map)} сотрудников.")
        return fio_map

    def get_raw_absence_data(self, start_date, end_date):
        """
        Получает "сырые" данные об отсутствиях за период для расчета суммарного времени.

        Args:
            start_date (str): Начальная дата периода (ГГГГ-ММ-ДД).
            end_date (str): Конечная дата периода (ГГГГ-ММ-ДД).

        Returns:
            list[tuple]: Список кортежей с данными отсутствий.
        """
        log.debug(
            f"Запрос сырых данных отсутствий за период: {start_date} - {end_date}")
        result = self.db.fetch_all(
            q.GET_RAW_ABSENCE_DATA_FOR_SUMMATION, (start_date, end_date))
        if result is None:
            log.warning("Запрос сырых данных отсутствий не вернул данных.")
            return []
        log.debug(f"Получено {len(result)} сырых записей об отсутствии.")
        # Не заменяем None на '', так как None важен для логики расчета времени.
        return result

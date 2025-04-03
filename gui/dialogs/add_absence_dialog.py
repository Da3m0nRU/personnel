# gui/dialogs/add_absence_dialog.py
import customtkinter as ctk
from config import *
import logging
from tkinter import messagebox
import re
import datetime
import calendar  # Для определения количества дней в месяце

log = logging.getLogger(__name__)


class AddAbsenceDialog(ctk.CTkToplevel):
    """ Диалог для добавления записи об отсутствии сотрудника. """

    def __init__(self, master, repository):
        """
        Инициализация диалога.

        Args:
            master: Родительский виджет (AbsencesFrame).
            repository: Экземпляр AbsenceRepository.
        """
        super().__init__(master)
        self.repository = repository  # Сохраняем репозиторий

        self.title("Добавить отсутствие")
        # Увеличим размер, так как дата стала сложнее
        self.geometry("500x650")  # Больше высоты
        self.resizable(False, False)
        self.grab_set()  # Делаем модальным
        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Атрибуты для хранения промежуточных данных
        self._selected_personnel_number = None
        self._current_schedule_id = None
        self._current_working_start_time = None
        self._current_working_end_time = None

        # Словарь для месяцев и их имена
        self.month_map = {
            "Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4,
            "Май": 5, "Июнь": 6, "Июль": 7, "Август": 8,
            "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12
        }
        self.month_names = list(self.month_map.keys())

        self.create_widgets()  # Создаем все виджеты
        self.load_employee_list()  # Загружаем список сотрудников в combobox

        # Устанавливаем текущий год по умолчанию
        self.year_entry.insert(0, str(datetime.date.today().year))

        # --- Привязки событий для обновления графика ---
        # Привязываем command и bind после создания виджетов
        self.day_combo.configure(command=self.on_date_change)
        self.month_combo.configure(command=self.on_date_change)
        self.year_entry.bind("<KeyRelease>", self.on_date_change)
        self.employee_combo.configure(command=self.on_employee_or_date_change)
        # ---------------------------------------------

        self.update_days_list()   # Первичная установка списка дней для текущего месяца/года
        # Важно! Вызовем обновление графика сразу после инициализации полей,
        # на случай если комбобоксы получили какие-то начальные значения.
        self.on_employee_or_date_change()
        # Применяем начальное состояние полей времени (по умолчанию FullDay=1)
        self.toggle_time_fields()
        # Проверяем состояние кнопки "Сохранить"
        self.check_fields()
        log.debug("Инициализирован диалог AddAbsenceDialog")

    def create_widgets(self):
        """ Создает виджеты диалога. """
        log.debug("Создание виджетов AddAbsenceDialog (с датой из 3 полей)")
        dialog_frame = ctk.CTkFrame(self, fg_color="transparent")
        dialog_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # --- Сотрудник ---
        ctk.CTkLabel(dialog_frame, text="Сотрудник*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.employee_combo = ctk.CTkComboBox(
            dialog_frame,
            values=[],  # Будут загружены позже
            font=DEFAULT_FONT,
            width=400,  # Сделаем пошире
            state="readonly",
            # command привязывается в __init__
        )
        self.employee_combo.pack(anchor="w", pady=(2, 10))

        # --- Дата отсутствия (3 поля) ---
        ctk.CTkLabel(dialog_frame, text="Дата отсутствия*",
                     font=DEFAULT_FONT).pack(anchor="w")
        date_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(2, 10))

        # День
        ctk.CTkLabel(date_frame, text="День", font=DEFAULT_FONT).grid(
            row=0, column=0, padx=(0, 5), sticky="w")
        self.day_combo = ctk.CTkComboBox(
            date_frame, values=[], width=60, font=DEFAULT_FONT, state="readonly"
            # command привязывается в __init__
        )
        self.day_combo.grid(row=1, column=0, padx=(0, 5), sticky="w")

        # Месяц
        ctk.CTkLabel(date_frame, text="Месяц", font=DEFAULT_FONT).grid(
            row=0, column=1, padx=(0, 5), sticky="w")
        self.month_combo = ctk.CTkComboBox(
            date_frame, values=self.month_names, width=120, font=DEFAULT_FONT, state="readonly"
            # command привязывается в __init__
        )
        self.month_combo.grid(row=1, column=1, padx=(0, 5), sticky="w")

        # Год
        ctk.CTkLabel(date_frame, text="Год", font=DEFAULT_FONT).grid(
            row=0, column=2, padx=(0, 5), sticky="w")
        self.year_entry = ctk.CTkEntry(date_frame, width=80, font=DEFAULT_FONT)
        # bind привязывается в __init__
        self.year_entry.grid(row=1, column=2, padx=(0, 5), sticky="w")

        # --- Полный день ---
        self.full_day_var = ctk.IntVar(value=1)  # По умолчанию - полный день
        self.full_day_check = ctk.CTkCheckBox(
            dialog_frame,
            text="Полный день",
            variable=self.full_day_var,
            font=DEFAULT_FONT,
            command=self.toggle_time_fields  # Вызываем при изменении состояния
        )
        self.full_day_check.pack(anchor="w", pady=(5, 10))

        # --- Время (для неполного дня) ---
        self.time_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.time_frame, text="Начало (ЧЧ:ММ)", font=DEFAULT_FONT).grid(
            row=0, column=0, padx=(0, 10), sticky="w")
        self.start_time_entry = ctk.CTkEntry(
            self.time_frame, font=DEFAULT_FONT, width=80)
        self.start_time_entry.grid(row=1, column=0, padx=(0, 10), sticky="w")
        self.start_time_entry.bind(
            "<KeyRelease>", self.check_fields)  # Проверка при вводе

        ctk.CTkLabel(self.time_frame, text="Окончание (ЧЧ:ММ)",
                     font=DEFAULT_FONT).grid(row=0, column=1, sticky="w")
        self.end_time_entry = ctk.CTkEntry(
            self.time_frame, font=DEFAULT_FONT, width=80)
        self.end_time_entry.grid(row=1, column=1, sticky="w")
        self.end_time_entry.bind(
            "<KeyRelease>", self.check_fields)  # Проверка при вводе

        # Информационная метка о рабочих часах (пока скрыта)
        self.work_hours_label = ctk.CTkLabel(
            self.time_frame, text="", font=("Arial", 12), text_color="grey")
        self.work_hours_label.grid(
            row=2, column=0, columnspan=2, pady=(5, 0), sticky="w")

        # --- Причина ---
        ctk.CTkLabel(dialog_frame, text="Причина*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.reason_textbox = ctk.CTkTextbox(
            dialog_frame, font=DEFAULT_FONT, height=100)  # Увеличим высоту
        self.reason_textbox.pack(anchor="w", fill="x", pady=(2, 20))
        self.reason_textbox.bind(
            "<KeyRelease>", self.check_fields)  # Проверка при вводе

        # --- Кнопки ---
        buttons_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", side="bottom")  # Размещаем кнопки внизу

        self.save_button = ctk.CTkButton(
            buttons_frame, text="Сохранить", command=self.save_absence, font=DEFAULT_FONT
        )
        self.save_button.pack(side="left", padx=(0, 10))

        cancel_button = ctk.CTkButton(
            buttons_frame, text="Отмена", command=self.cancel, font=DEFAULT_FONT, fg_color="gray"
        )
        cancel_button.pack(side="left")

        log.debug("Виджеты AddAbsenceDialog созданы (дата из 3 полей)")

    # --- Методы для работы с датой ---
    def update_days_list(self, event=None):
        """ Обновляет список дней в day_combo в зависимости от месяца и года. """
        try:
            year_str = self.year_entry.get().strip()
            # Добавляем более строгую проверку года
            if not (year_str.isdigit() and len(year_str) == 4):
                year = 0  # Невалидный год
            else:
                year = int(year_str)

            month_name = self.month_combo.get()
            month = self.month_map.get(month_name)

            if not (month and 1900 <= year <= 2100):  # Базовая проверка диапазона
                days_in_month = 31  # По умолчанию, если дата некорректна
            else:
                days_in_month = calendar.monthrange(year, month)[1]

            current_day = self.day_combo.get()
            new_day_list = [str(i) for i in range(1, days_in_month + 1)]
            self.day_combo.configure(values=new_day_list)

            # Пытаемся сохранить выбранный день, если он допустим в новом списке
            if current_day in new_day_list:
                self.day_combo.set(current_day)
            else:
                # Если дня нет, очищаем поле, чтобы пользователь выбрал сам
                self.day_combo.set("")

        except ValueError:
            # В случае нечислового года
            self.day_combo.configure(values=[str(i) for i in range(1, 32)])
            self.day_combo.set("")
        except Exception as e:
            log.error(f"Ошибка обновления списка дней: {e}")
            # Ставим дефолтный список при других ошибках
            self.day_combo.configure(values=[str(i) for i in range(1, 32)])
            self.day_combo.set("")

    def get_selected_date(self):
        """
        Пытается собрать выбранную дату из трех полей.
        Возвращает объект date или None, если дата некорректна.
        """
        try:
            day_str = self.day_combo.get()
            month_name = self.month_combo.get()
            year_str = self.year_entry.get().strip()

            if not (day_str and month_name and year_str):
                return None  # Не все поля заполнены

            day = int(day_str)
            month = self.month_map.get(month_name)
            year = int(year_str)

            # Проверяем корректность года и месяца
            if not (month and 1900 <= year <= 2100):
                return None

            # Проверяем, что день соответствует месяцу и году
            max_days = calendar.monthrange(year, month)[1]
            if not (1 <= day <= max_days):
                return None

            return datetime.date(year, month, day)
        except (ValueError, TypeError):
            # Например, если в полях не числа или некорректный месяц
            return None

    def on_date_change(self, event=None):
        """Обработчик изменения дня, месяца или года."""
        self.update_days_list()  # Обновляем список дней
        self.on_employee_or_date_change()  # Запускаем основную логику обновления

    def on_employee_or_date_change(self, event=None):
        """Обработчик изменения сотрудника ИЛИ даты - центральная точка обновления."""
        log.debug("Сработало on_employee_or_date_change")
        self.update_schedule_info()  # 1. Обновить данные графика
        self.apply_schedule_to_time_fields()  # 2. Применить к полям времени
        self.check_fields()  # 3. Проверить кнопку "Сохранить"

    # --- Методы для работы с графиком ---

    def update_schedule_info(self):
        """Запрашивает из репозитория информацию о графике на выбранную дату."""
        # Сначала сбрасываем предыдущие данные графика
        self._current_schedule_id = None
        self._current_working_start_time = None
        self._current_working_end_time = None
        self.work_hours_label.configure(text="")  # Сброс информационной метки

        # Получаем текущие значения из UI
        self._selected_personnel_number = self.get_selected_personnel_number()
        selected_date = self.get_selected_date()

        # Если не выбран сотрудник или дата некорректна, ничего не делаем
        if not (self._selected_personnel_number and selected_date):
            log.debug(
                "Сотрудник или дата не выбраны/некорректны, информация о графике не запрашивается.")
            return

        log.debug(
            f"Запрос графика для: Сотрудник={self._selected_personnel_number}, Дата={selected_date}")
        try:
            # Получаем ID должности выбранного сотрудника
            position_id = self.repository.get_employee_position_id(
                self._selected_personnel_number)
            if not position_id:
                log.warning(
                    f"Не удалось получить PositionID для {self._selected_personnel_number}")
                self.work_hours_label.configure(
                    text="Не удалось определить должность.")
                return

            # Определяем ID дня недели (ISO: 1=Пн, 7=Вс)
            day_of_week_id = selected_date.isoweekday()

            # Запрашиваем график из репозитория
            schedule_data = self.repository.get_working_hours(
                position_id, day_of_week_id)

            if schedule_data:
                schedule_id_from_db, start_time, end_time = schedule_data
                # Проверяем, рабочий ли день (время не 00:00)
                if start_time == "00:00" and end_time == "00:00":
                    log.info(
                        f"Выбран нерабочий день ({selected_date.strftime('%A')}) по графику.")
                    self.work_hours_label.configure(
                        text="Выходной по графику.")
                    # График найден, но день нерабочий - время не сохраняем
                else:
                    # Сохраняем данные найденного рабочего графика
                    self._current_schedule_id = schedule_id_from_db
                    self._current_working_start_time = start_time
                    self._current_working_end_time = end_time
                    self.work_hours_label.configure(
                        text=f"График на этот день: {start_time} - {end_time}")
                    log.debug(
                        f"График найден: ScheduleID={self._current_schedule_id}, Часы={start_time}-{end_time}")
            else:
                log.warning(
                    f"График для PositionID={position_id} на {selected_date} ({day_of_week_id}) не найден.")
                self.work_hours_label.configure(
                    text="График работы не найден.")

        except Exception as e:
            log.exception(f"Ошибка при получении графика работы: {e}")
            self.work_hours_label.configure(text="Ошибка получения графика.")

    def apply_schedule_to_time_fields(self):
        """Заполняет/очищает и активирует/деактивирует поля времени."""
        is_full_day = self.full_day_var.get() == 1

        if is_full_day:
            # Если выбран "Полный день", деактивируем поля
            self.start_time_entry.configure(state="disabled")
            self.end_time_entry.configure(state="disabled")
            # И пытаемся подставить время из графика (если он есть и рабочий)
            if self._current_working_start_time and self._current_working_end_time:
                self.start_time_entry.delete(0, "end")
                self.start_time_entry.insert(
                    0, self._current_working_start_time)
                self.end_time_entry.delete(0, "end")
                self.end_time_entry.insert(0, self._current_working_end_time)
                log.debug("Время из графика подставлено в поля (Полный день).")
            else:
                # Если графика нет или выходной - оставляем поля пустыми
                self.start_time_entry.delete(0, "end")
                self.end_time_entry.delete(0, "end")
                log.debug(
                    "Поля времени очищены (Полный день, нет графика или выходной).")
        else:
            # Если НЕ "Полный день", активируем поля для ручного ввода
            self.start_time_entry.configure(state="normal")
            self.end_time_entry.configure(state="normal")
            # Не очищаем поля, пользователь может корректировать
            log.debug("Поля времени активированы (Неполный день).")

    # --- Основные методы диалога ---

    def load_employee_list(self):
        """ Загружает список сотрудников в ComboBox. """
        log.debug("Загрузка списка сотрудников в AddAbsenceDialog")
        try:
            employee_list = self.repository.get_employee_list()
            self.employee_combo.configure(values=employee_list)
            if not employee_list:
                log.warning("Список сотрудников пуст.")
                messagebox.showwarning(
                    "Предупреждение", "Список работающих сотрудников пуст. Невозможно добавить отсутствие.")
                # Состояние кнопки обновится в check_fields
            else:
                log.debug(f"Загружено {len(employee_list)} сотрудников.")
        except Exception as e:
            log.exception(
                "Ошибка при загрузке списка сотрудников в AddAbsenceDialog")
            messagebox.showerror(
                "Ошибка", "Не удалось загрузить список сотрудников.")

    def toggle_time_fields(self):
        """ Переключает состояние полей времени при клике на чекбокс 'Полный день'. """
        log.debug(
            f"Сработало toggle_time_fields, FullDay={self.full_day_var.get()}")
        self.apply_schedule_to_time_fields()  # Применяем актуальное состояние полей
        self.check_fields()  # Перепроверяем, можно ли сохранять

    def check_fields(self, event=None):
        """ Проверяет заполненность полей и доступность графика для активации кнопки 'Сохранить'. """
        employee_selected = bool(
            self.employee_combo.get() and self.get_selected_personnel_number())
        date_selected = bool(self.get_selected_date())
        reason_filled = bool(self.reason_textbox.get("1.0", "end-1c").strip())
        # Валидно ли время (либо задано для полного дня, либо введено для неполного)
        time_is_valid = False

        is_full_day = self.full_day_var.get() == 1
        if is_full_day:
            # Для полного дня время валидно, если график найден и он рабочий
            time_is_valid = bool(
                self._current_working_start_time and self._current_working_end_time)
        else:
            # Для неполного дня время валидно, если оба поля заполнены (формат проверит валидация)
            time_is_valid = bool(self.start_time_entry.get(
            ).strip() and self.end_time_entry.get().strip())

        # Кнопка активна, если все поля заполнены И время валидно (или будет введено)
        can_save = employee_selected and date_selected and reason_filled and time_is_valid
        current_state = self.save_button.cget("state")

        # Log для отладки
        # log.debug(
        #    f"CheckFields: Emp={employee_selected}, Date={date_selected}, Reason={reason_filled}, "
        #    f"FullDay={is_full_day}, ScheduleOK={(self._current_working_start_time is not None)}, "
        #    f"TimeOK={time_is_valid} => CanSave={can_save}"
        # )

        if can_save and current_state == "disabled":
            self.save_button.configure(state="normal", fg_color="#0057FC")
        elif not can_save and current_state == "normal":
            self.save_button.configure(state="disabled", fg_color="gray")

    def get_selected_personnel_number(self):
        """ Извлекает табельный номер из выбранного значения ComboBox. """
        selected_text = self.employee_combo.get()
        if not selected_text:
            return None
        # Ищем цифры в скобках в конце строки
        match = re.search(r'\((\d+)\)$', selected_text)
        return match.group(1) if match else None

    def validate_input(self):
        """
        Проводит полную валидацию введенных данных перед сохранением.
        Возвращает (bool: is_valid, dict: validated_data or None).
        """
        log.debug("Валидация данных в AddAbsenceDialog")
        # 1. Проверка сотрудника
        personnel_number = self.get_selected_personnel_number()
        if not personnel_number:
            messagebox.showerror("Ошибка валидации", "Не выбран сотрудник.")
            return False, None

        # 2. Проверка даты
        selected_date = self.get_selected_date()
        if not selected_date:
            messagebox.showerror("Ошибка валидации",
                                 "Некорректно выбрана или указана дата.")
            return False, None
        date_str = selected_date.strftime("%Y-%m-%d")  # Дата в нужном формате

        # 3. Проверка причины
        reason = self.reason_textbox.get("1.0", "end-1c").strip()
        if not reason:
            messagebox.showerror("Ошибка валидации",
                                 "Не указана причина отсутствия.")
            return False, None
        if len(reason) > 200:
            messagebox.showerror(
                "Ошибка валидации", "Причина отсутствия слишком длинная (макс. 200 символов).")
            return False, None

        # 4. Проверка времени и ScheduleID
        full_day = self.full_day_var.get()
        start_time_str = None
        end_time_str = None
        final_schedule_id = None  # ID графика для записи в БД

        if full_day == 1:  # Если выбран "Полный день"
            # Проверяем, что мы ранее УЖЕ нашли рабочий график
            if self._current_working_start_time and self._current_working_end_time:
                # Берем из сохраненного состояния
                start_time_str = self._current_working_start_time
                end_time_str = self._current_working_end_time
                final_schedule_id = self._current_schedule_id  # Используем ID найденного графика
                log.debug(
                    f"Валидация 'Полный день': Используется ScheduleID={final_schedule_id}, Время {start_time_str}-{end_time_str}")
            else:
                # График не был найден или это был выходной
                messagebox.showerror(
                    "Ошибка валидации", "Для полного дня не удалось определить рабочие часы.\nВозможно, это выходной или график не настроен.")
                return False, None
        else:  # Если выбран "Неполный день" - ручной ввод времени
            start_time_str = self.start_time_entry.get().strip()
            end_time_str = self.end_time_entry.get().strip()

            # Проверка, что поля заполнены
            if not (start_time_str and end_time_str):
                messagebox.showerror(
                    "Ошибка валидации", "Для неполного дня укажите время начала и окончания.")
                return False, None

            # Проверка формата времени ЧЧ:ММ
            time_pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
            if not re.match(time_pattern, start_time_str) or not re.match(time_pattern, end_time_str):
                messagebox.showerror(
                    "Ошибка валидации", "Неверный формат времени (ожидается ЧЧ:ММ).")
                return False, None

            # Проверка порядка времени и вхождения в график
            try:
                absence_start = datetime.datetime.strptime(
                    start_time_str, "%H:%M").time()
                absence_end = datetime.datetime.strptime(
                    end_time_str, "%H:%M").time()

                # Время окончания должно быть строго после начала
                if absence_start >= absence_end:
                    messagebox.showerror(
                        "Ошибка валидации", "Время окончания должно быть позже времени начала.")
                    return False, None

                # Проверка вхождения в график работы (если он есть)
                if self._current_working_start_time and self._current_working_end_time:
                    work_start = datetime.datetime.strptime(
                        self._current_working_start_time, "%H:%M").time()
                    work_end = datetime.datetime.strptime(
                        self._current_working_end_time, "%H:%M").time()

                    # Отсутствие должно начинаться не раньше начала рабочего дня
                    # Отсутствие должно заканчиваться не позже конца рабочего дня
                    # Начало отсутствия должно быть ДО конца рабочего дня
                    # Конец отсутствия должен быть ПОСЛЕ начала рабочего дня
                    # (Это проверяет, что интервалы пересекаются корректно внутри рабочего дня)
                    if not (work_start <= absence_start < work_end and work_start < absence_end <= work_end):
                        messagebox.showerror("Ошибка валидации",
                                             f"Введенное время ({start_time_str}-{end_time_str}) "
                                             f"выходит за пределы рабочего графика сотрудника на этот день "
                                             f"({self._current_working_start_time}-{self._current_working_end_time}).")
                        return False, None
                    log.debug(
                        "Валидация 'Неполный день': Время входит в рабочий график.")
                else:
                    # Что делать, если график не найден, а пользователь вводит время вручную?
                    # Лучше запретить, так как мы не можем проверить корректность.
                    messagebox.showerror(
                        "Ошибка валидации", "Невозможно проверить введенное время, так как график работы на этот день не определен.")
                    return False, None

                # При ручном вводе ID графика не устанавливается
                final_schedule_id = None
                log.debug(
                    "Валидация 'Неполный день': Время введено вручную, ScheduleID=None.")

            except ValueError as e:
                log.error(f"Ошибка сравнения/парсинга времени: {e}")
                messagebox.showerror(
                    "Ошибка валидации", "Ошибка при обработке введенного времени.")
                return False, None

        # Все проверки пройдены, собираем данные
        validated_data = {
            "personnel_number": personnel_number,
            "absence_date": date_str,
            "full_day": full_day,
            # Для полного дня берется из графика, для неполного - из поля
            "start_time": start_time_str,
            "end_time": end_time_str,     # Аналогично
            "reason": reason,
            "schedule_id": final_schedule_id  # ID графика или None
        }
        log.debug(f"Данные после валидации: {validated_data}")
        return True, validated_data

    def save_absence(self):
        """ Сохраняет запись об отсутствии после валидации. """
        log.info("Попытка сохранения записи об отсутствии")
        is_valid, data_to_save = self.validate_input()

        if not is_valid:
            log.warning("Валидация данных отсутствия не пройдена.")
            return  # Ошибка валидации, сообщение уже показано

        log.debug(f"Вызов repository.insert_absence с данными: {data_to_save}")

        # Вызываем метод репозитория для вставки
        success = self.repository.insert_absence(
            personnel_number=data_to_save["personnel_number"],
            absence_date=data_to_save["absence_date"],
            full_day=data_to_save["full_day"],
            start_time=data_to_save["start_time"],
            end_time=data_to_save["end_time"],
            reason=data_to_save["reason"],
            schedule_id=data_to_save["schedule_id"]  # Передаем schedule_id
        )

        if success:
            messagebox.showinfo(
                "Успех", "Запись об отсутствии успешно добавлена.")
            log.info("Запись об отсутствии успешно добавлена через диалог.")
            # Обновляем данные в родительском фрейме (AbsencesFrame)
            if self.master and hasattr(self.master, 'load_data'):
                self.master.load_data()
            if self.master and hasattr(self.master, 'display_data'):
                self.master.display_data()
            self.destroy()  # Закрываем диалог
        else:
            # Ошибка на уровне БД
            messagebox.showerror(
                "Ошибка", "Не удалось сохранить запись об отсутствии в базе данных.")
            log.error(
                "Ошибка при вызове insert_absence из диалога (вернул False).")

    def cancel(self):
        """ Закрывает диалог без сохранения. """
        log.debug("Закрытие диалога AddAbsenceDialog без сохранения")
        self.destroy()

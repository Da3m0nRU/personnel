# gui/dialogs/edit_absence_dialog.py
import customtkinter as ctk
from config import *
import logging
from tkinter import messagebox
import re
import datetime
import calendar
import db.queries as q

log = logging.getLogger(__name__)


class EditAbsenceDialog(ctk.CTkToplevel):
    """ Диалог для редактирования записи об отсутствии сотрудника. """

    def __init__(self, master, repository, absence_id):
        super().__init__(master)
        self.repository = repository
        self.absence_id = absence_id
        self.original_data = None  # Для хранения исходных данных
        self.title("Редактировать отсутствие")
        self.geometry("500x650")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self._selected_personnel_number = None
        self._current_schedule_id = None
        self._current_working_start_time = None
        self._current_working_end_time = None

        self.month_map = {"Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4, "Май": 5, "Июнь": 6,
                          "Июль": 7, "Август": 8, "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12}
        self.month_names = list(self.month_map.keys())

        self.create_widgets()
        # ЗАГРУЖАЕМ ДАННЫЕ ДО ПРИВЯЗОК И ОБНОВЛЕНИЙ
        if not self.load_data_into_dialog():
            return  # Если загрузка не удалась, диалог не должен работать

        # Привязки событий
        self.day_combo.configure(command=self.on_date_change)
        self.month_combo.configure(command=self.on_date_change)
        self.year_entry.bind("<KeyRelease>", self.on_date_change)
        self.full_day_check.configure(
            command=self.toggle_time_fields)  # Важно привязать

        # Инициализация состояния после загрузки
        # Обновляем график по загруженной дате/сотруднику
        self.on_employee_or_date_change()
        self.toggle_time_fields()  # Применяем состояние полей по full_day_var
        self.check_fields()  # Проверяем кнопку Save

        log.debug(
            f"Инициализирован диалог EditAbsenceDialog для ID={absence_id}")

    def create_widgets(self):
        """ Создает виджеты диалога. """
        log.debug("Создание виджетов EditAbsenceDialog")
        dialog_frame = ctk.CTkFrame(self, fg_color="transparent")
        dialog_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Сотрудник (Label)
        ctk.CTkLabel(dialog_frame, text="Сотрудник",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.employee_label = ctk.CTkLabel(
            dialog_frame, text="Загрузка...", font=DEFAULT_FONT, anchor="w")
        self.employee_label.pack(anchor="w", pady=(2, 10), fill="x")

        # Дата (3 поля)
        ctk.CTkLabel(dialog_frame, text="Дата отсутствия*",
                     font=DEFAULT_FONT).pack(anchor="w")
        date_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(2, 10))
        ctk.CTkLabel(date_frame, text="День", font=DEFAULT_FONT).grid(
            row=0, column=0, padx=(0, 5), sticky="w")
        self.day_combo = ctk.CTkComboBox(
            date_frame, values=[], width=60, font=DEFAULT_FONT, state="readonly")
        self.day_combo.grid(row=1, column=0, padx=(0, 5), sticky="w")
        ctk.CTkLabel(date_frame, text="Месяц", font=DEFAULT_FONT).grid(
            row=0, column=1, padx=(0, 5), sticky="w")
        self.month_combo = ctk.CTkComboBox(
            date_frame, values=self.month_names, width=120, font=DEFAULT_FONT, state="readonly")
        self.month_combo.grid(row=1, column=1, padx=(0, 5), sticky="w")
        ctk.CTkLabel(date_frame, text="Год", font=DEFAULT_FONT).grid(
            row=0, column=2, padx=(0, 5), sticky="w")
        self.year_entry = ctk.CTkEntry(date_frame, width=80, font=DEFAULT_FONT)
        self.year_entry.grid(row=1, column=2, padx=(0, 5), sticky="w")

        # Полный день (Checkbox)
        self.full_day_var = ctk.IntVar()  # Значение установится при загрузке данных
        self.full_day_check = ctk.CTkCheckBox(
            dialog_frame, text="Полный день", variable=self.full_day_var, font=DEFAULT_FONT)
        # command привязывается в __init__
        self.full_day_check.pack(anchor="w", pady=(5, 10))

        # Время (Frame + 2 Entry + Label)
        self.time_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self.time_frame, text="Начало (ЧЧ:ММ)", font=DEFAULT_FONT).grid(
            row=0, column=0, padx=(0, 10), sticky="w")
        self.start_time_entry = ctk.CTkEntry(
            self.time_frame, font=DEFAULT_FONT, width=80)
        self.start_time_entry.grid(row=1, column=0, padx=(0, 10), sticky="w")
        self.start_time_entry.bind("<KeyRelease>", self.check_fields)
        ctk.CTkLabel(self.time_frame, text="Окончание (ЧЧ:ММ)",
                     font=DEFAULT_FONT).grid(row=0, column=1, sticky="w")
        self.end_time_entry = ctk.CTkEntry(
            self.time_frame, font=DEFAULT_FONT, width=80)
        self.end_time_entry.grid(row=1, column=1, sticky="w")
        self.end_time_entry.bind("<KeyRelease>", self.check_fields)
        self.work_hours_label = ctk.CTkLabel(
            self.time_frame, text="", font=("Arial", 12), text_color="grey")
        self.work_hours_label.grid(
            row=2, column=0, columnspan=2, pady=(5, 0), sticky="w")

        # Причина (Textbox)
        ctk.CTkLabel(dialog_frame, text="Причина*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.reason_textbox = ctk.CTkTextbox(
            dialog_frame, font=DEFAULT_FONT, height=100)
        self.reason_textbox.pack(anchor="w", fill="x", pady=(2, 20))
        self.reason_textbox.bind("<KeyRelease>", self.check_fields)

        # Кнопки (Frame + 2 Button)
        buttons_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", side="bottom")
        self.update_button = ctk.CTkButton(
            buttons_frame, text="Сохранить", command=self.update_absence, font=DEFAULT_FONT)
        self.update_button.pack(side="left", padx=(0, 10))
        cancel_button = ctk.CTkButton(
            buttons_frame, text="Отмена", command=self.cancel, font=DEFAULT_FONT, fg_color="gray")
        cancel_button.pack(side="left")

        log.debug("Виджеты EditAbsenceDialog созданы")

    def load_data_into_dialog(self):
        """ Загружает данные по ID и заполняет поля. Возвращает True/False успеха. """
        log.debug(f"Загрузка данных для Absence ID={self.absence_id}")
        self.original_data = self.repository.get_absence_by_id(self.absence_id)
        if not self.original_data:
            messagebox.showerror(
                "Ошибка", f"Запись с ID={self.absence_id} не найдена.")
            log.error(...)
            # Закрыть диалог после обработки события
            self.after(10, self.destroy)
            return False

        log.debug(f"Загружены данные: {self.original_data}")
        # Индексы: 0:ID, 1:PN, 2:Date, 3:FullD, 4:StartT, 5:EndT, 6:Reason, 7:SchedID

        # 1. Сотрудник (PN сохраняем, ФИО показываем)
        self._selected_personnel_number = self.original_data[1]
        emp_info = self.repository.db.fetch_one(
            q.GET_EMPLOYEE_FIO_BY_PN, (self._selected_personnel_number,))
        emp_name_display = f"{emp_info[0]} ({self._selected_personnel_number})" if emp_info else f"({self._selected_personnel_number})"
        self.employee_label.configure(text=emp_name_display)

        # 2. Дата
        try:
            d_date = datetime.datetime.strptime(
                self.original_data[2], "%Y-%m-%d").date()
            self.year_entry.insert(0, str(d_date.year))
            self.month_combo.set(self.month_names[d_date.month - 1])
            self.update_days_list()  # Важно обновить список ДО установки дня
            self.day_combo.set(str(d_date.day))
        except Exception as e:
            log.error(f"Ошибка разбора даты '{self.original_data[2]}': {e}")
            # Оставляем поля пустыми

        # 3. Полный день
        self.full_day_var.set(self.original_data[3])

        # 4. Время (будет применено в toggle_time_fields)
        start_t = self.original_data[4] or ""
        self.start_time_entry.insert(0, start_t)
        end_t = self.original_data[5] or ""
        self.end_time_entry.insert(0, end_t)

        # 5. Причина
        reason_t = self.original_data[6] or ""
        self.reason_textbox.insert("1.0", reason_t)

        # 6. Сохраняем исходный ScheduleID
        self._current_schedule_id = self.original_data[7]  # Важно для логики

        log.debug("Поля диалога (Edit) заполнены.")
        return True

    # --- Методы работы с датой и графиком (Идентичны AddAbsenceDialog) ---
    # (Включая: update_days_list, get_selected_date, on_date_change,
    # on_employee_or_date_change, update_schedule_info, apply_schedule_to_time_fields,
    # toggle_time_fields, check_fields, validate_input)
    # КОПИРУЕМ ЭТИ МЕТОДЫ БЕЗ ИЗМЕНЕНИЙ ИЗ ПОЛНОГО КОДА AddAbsenceDialog
    # Ниже только примеры, нужно вставить весь код этих методов.

    def update_days_list(self, event=None):
        # ... КОД ИЗ AddAbsenceDialog ...
        try:
            year_str = self.year_entry.get().strip()
            if not (year_str.isdigit() and len(year_str) == 4):
                year = 0
            else:
                year = int(year_str)
            month_name = self.month_combo.get()
            month = self.month_map.get(month_name)
            if not (month and 1900 <= year <= 2100):
                days_in_month = 31
            else:
                days_in_month = calendar.monthrange(year, month)[1]
            current_day = self.day_combo.get()
            new_day_list = [str(i) for i in range(1, days_in_month + 1)]
            self.day_combo.configure(values=new_day_list)
            if current_day in new_day_list:
                self.day_combo.set(current_day)
            else:
                self.day_combo.set("")
        except (ValueError, Exception) as e:
            log.error(f"Ошибка обновления списка дней: {e}")
            self.day_combo.configure(values=[str(i) for i in range(1, 32)])
            self.day_combo.set("")

    def get_selected_date(self):
        # ... КОД ИЗ AddAbsenceDialog ...
        try:
            day_str = self.day_combo.get()
            month_name = self.month_combo.get()
            year_str = self.year_entry.get().strip()
            if not (day_str and month_name and year_str):
                return None
            day = int(day_str)
            month = self.month_map.get(month_name)
            year = int(year_str)
            if not (month and 1900 <= year <= 2100):
                return None
            max_days = calendar.monthrange(year, month)[1]
            if not (1 <= day <= max_days):
                return None
            return datetime.date(year, month, day)
        except (ValueError, TypeError):
            return None

    def on_date_change(self, event=None):
        # ... КОД ИЗ AddAbsenceDialog ...
        self.update_days_list()
        self.on_employee_or_date_change()

    def on_employee_or_date_change(self, event=None):
        # ... КОД ИЗ AddAbsenceDialog ...
        log.debug("Сработало on_employee_or_date_change (Edit Dialog)")
        self.update_schedule_info()
        self.apply_schedule_to_time_fields()
        self.check_fields()

    def update_schedule_info(self):
        # ... КОД ИЗ AddAbsenceDialog ...
        self._current_schedule_id = None
        self._current_working_start_time = None
        self._current_working_end_time = None
        self.work_hours_label.configure(text="")
        selected_date = self.get_selected_date()
        # personnel_number уже должен быть в self._selected_personnel_number из load_data...
        if not (self._selected_personnel_number and selected_date):
            log.debug("Сотрудник (в Edit) или дата не выбраны/некорректны.")
            return
        log.debug(
            f"Запрос графика для: Сотрудник={self._selected_personnel_number}, Дата={selected_date}")
        try:
            position_id = self.repository.get_employee_position_id(
                self._selected_personnel_number)
            if not position_id:
                log.warning(
                    f"Нет PositionID для {self._selected_personnel_number}")
                self.work_hours_label.configure(text="Нет должности.")
                return
            day_of_week_id = selected_date.isoweekday()
            schedule_data = self.repository.get_working_hours(
                position_id, day_of_week_id)
            if schedule_data:
                s_id, s_time, e_time = schedule_data
                if s_time == "00:00" and e_time == "00:00":
                    log.info("Выходной")
                    self.work_hours_label.configure(text="Выходной.")
                else:
                    self._current_schedule_id = s_id
                    self._current_working_start_time = s_time
                    self._current_working_end_time = e_time
                    self.work_hours_label.configure(
                        text=f"График: {s_time}-{e_time}")
                    log.debug("График найден (Edit)")
            else:
                log.warning("График не найден (Edit)")
                self.work_hours_label.configure(text="График не найден.")
        except Exception as e:
            log.exception("Ошибка графика (Edit)")
            self.work_hours_label.configure(text="Ошибка графика.")

    def apply_schedule_to_time_fields(self):
        # ... КОД ИЗ AddAbsenceDialog ...
        is_full_day = self.full_day_var.get() == 1
        if is_full_day:
            self.start_time_entry.configure(state="disabled")
            self.end_time_entry.configure(state="disabled")
            if self._current_working_start_time and self._current_working_end_time:
                self.start_time_entry.delete(0, "end")
                self.start_time_entry.insert(
                    0, self._current_working_start_time)
                self.end_time_entry.delete(0, "end")
                self.end_time_entry.insert(0, self._current_working_end_time)
                log.debug("График применен (Edit Full).")
            else:
                self.start_time_entry.delete(0, "end")
                self.end_time_entry.delete(0, "end")
                log.debug("Поля очищены (Edit Full).")
        else:
            self.start_time_entry.configure(state="normal")
            self.end_time_entry.configure(state="normal")
            log.debug("Поля активны (Edit Not Full).")

    def toggle_time_fields(self):
        # ... КОД ИЗ AddAbsenceDialog ...
        log.debug(
            f"Сработало toggle_time_fields (Edit), FullDay={self.full_day_var.get()}")
        self.apply_schedule_to_time_fields()
        self.check_fields()

    def check_fields(self, event=None):
        # ... КОД ИЗ AddAbsenceDialog ...
        # Сотрудник всегда "выбран" в Edit
        date_selected = bool(self.get_selected_date())
        reason_filled = bool(self.reason_textbox.get("1.0", "end-1c").strip())
        time_is_valid = False
        is_full_day = self.full_day_var.get() == 1
        if is_full_day:
            time_is_valid = bool(
                self._current_working_start_time and self._current_working_end_time)
        else:
            time_is_valid = bool(self.start_time_entry.get(
            ).strip() and self.end_time_entry.get().strip())

        can_save = date_selected and reason_filled and time_is_valid
        current_state = self.update_button.cget("state")

        if can_save and current_state == "disabled":
            self.update_button.configure(state="normal", fg_color="#0057FC")
        elif not can_save and current_state == "normal":
            self.update_button.configure(state="disabled", fg_color="gray")

    def validate_input(self):
        # ... КОД ИЗ AddAbsenceDialog ... (возвращает True/False, validated_data)
        log.debug("Валидация данных в EditAbsenceDialog")
        if not self._selected_personnel_number:
            messagebox.showerror("Критическая ошибка",
                                 "Не определен сотрудник.")
            return False, None

        selected_date = self.get_selected_date()
        if not selected_date:
            messagebox.showerror("Ошибка", "Некорректная дата.")
            return False, None
        date_str = selected_date.strftime("%Y-%m-%d")

        reason = self.reason_textbox.get("1.0", "end-1c").strip()
        if not reason:
            messagebox.showerror("Ошибка", "Укажите причину.")
            return False, None
        if len(reason) > 200:
            messagebox.showerror("Ошибка", "Причина > 200 симв.")
            return False, None

        full_day = self.full_day_var.get()
        start_time_str, end_time_str, final_schedule_id = None, None, None
        if full_day == 1:
            if self._current_working_start_time and self._current_working_end_time:
                start_time_str = self._current_working_start_time
                end_time_str = self._current_working_end_time
                final_schedule_id = self._current_schedule_id
                log.debug("Валидация (Edit Full): OK")
            else:
                messagebox.showerror("Ошибка", "Нет графика для полного дня.")
                return False, None
        else:
            start_time_str = self.start_time_entry.get().strip()
            end_time_str = self.end_time_entry.get().strip()
            time_pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
            if not (start_time_str and end_time_str):
                messagebox.showerror("Ошибка", "Укажите время.")
                return False, None
            if not re.match(time_pattern, start_time_str) or not re.match(time_pattern, end_time_str):
                messagebox.showerror("Ошибка", "Формат ЧЧ:ММ.")
                return False, None
            try:
                abs_s = datetime.datetime.strptime(
                    start_time_str, "%H:%M").time()
                abs_e = datetime.datetime.strptime(
                    end_time_str, "%H:%M").time()
                if abs_s >= abs_e:
                    messagebox.showerror("Ошибка", "Конец < Начала.")
                    return False, None
                if self._current_working_start_time and self._current_working_end_time:
                    w_s = datetime.datetime.strptime(
                        self._current_working_start_time, "%H:%M").time()
                    w_e = datetime.datetime.strptime(
                        self._current_working_end_time, "%H:%M").time()
                    if not (w_s <= abs_s < abs_e <= w_e):
                        messagebox.showerror(
                            "Ошибка", f"Время вне графика({self._current_working_start_time}-{self._current_working_end_time}).")
                        return False, None
                    log.debug("Валидация (Edit Not Full): ОК.")
                else:
                    messagebox.showerror("Ошибка", "Нет графика для проверки.")
                    return False, None
                final_schedule_id = None
                log.debug("Ручной ввод, SchedID=None.")
            except ValueError as e:
                log.error(e)
                messagebox.showerror("Ошибка", "Ошибка времени.")
                return False, None

        validated_data = {"absence_id": self.absence_id, "personnel_number": self._selected_personnel_number, "absence_date": date_str,
                          "full_day": full_day, "start_time": start_time_str, "end_time": end_time_str, "reason": reason, "schedule_id": final_schedule_id}
        log.debug(f"Данные валидны (Edit): {validated_data}")
        return True, validated_data

    # --- Основные действия ---
    def update_absence(self):
        """ Обновляет запись об отсутствии после валидации. """
        log.info(
            f"Попытка обновления записи об отсутствии ID={self.absence_id}")
        is_valid, data_to_update = self.validate_input()
        if not is_valid:
            log.warning("Валидация (Edit) не пройдена.")
            return

        log.debug(
            f"Вызов repository.update_absence с данными: {data_to_update}")
        success = self.repository.update_absence(
            **data_to_update)  # Используем распаковку словаря

        if success:
            messagebox.showinfo("Успех", "Запись обновлена.")
            log.info(f"ID={self.absence_id} обновлен.")
            if self.master and hasattr(self.master, 'load_data'):
                self.master.load_data()
            if self.master and hasattr(self.master, 'display_data'):
                self.master.display_data()
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить запись.")
            log.error(f"Ошибка update_absence ID={self.absence_id}.")

    def cancel(self):
        """ Закрывает диалог без сохранения изменений. """
        log.debug(
            f"Закрытие диалога EditAbsenceDialog ID={self.absence_id} без сохранения")
        self.destroy()

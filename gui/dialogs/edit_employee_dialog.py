# gui/dialogs/edit_employee_dialog.py
import customtkinter as ctk
from config import *
import re
import datetime
from tkinter import messagebox
import logging
from db.employee_repository import EmployeeRepository
from db.employee_event_repository import EmployeeEventRepository
import db.queries as q
from .confirm_event_dialog import ConfirmEventDialog

log = logging.getLogger(__name__)


class EditEmployeeDialog(ctk.CTkToplevel):
    """
    Диалог редактирования сотрудника.
    """

    def __init__(self, master, db, employee_data):
        """
        Инициализирует диалог.

        Args:
            master (ctk.CTk/ctk.CTkFrame): Родительский виджет.
            db (Database): Объект базы данных.
            employee_data (tuple): Данные о сотруднике (результат fetch_one).
        """
        super().__init__(master)
        self.employee_event_repository = EmployeeEventRepository(db)
        self.employee_data = employee_data  # Сохраняем данные
        self.employee_repository = master.repository  # !!!
        self.gender_repository = master.gender_repository  # !!!
        self.position_repository = master.position_repository  # !!!
        self.state_repository = master.state_repository  # !!!
        self.department_repository = master.department_repository  # !!!
        self.employee_data = employee_data
        self.title("Редактировать сотрудника")
        self.geometry("650x920")
        self.resizable(False, False)
        self.create_widgets()
        self.grab_set()  # Модальный диалог
        self.check_fields()
        log.debug("Инициализирован диалог EditEmployeeDialog")

    def create_widgets(self):
        """
        Создает виджеты диалога.
        """
        log.debug("Создание виджетов для EditEmployeeDialog")
        section_font = ("Arial", 20, "bold")

        # --- Заголовок ---
        main_section_label = ctk.CTkLabel(
            self,
            text="РЕДАКТИРОВАТЬ СОТРУДНИКА",
            font=("Arial", 28, "bold"),
            text_color=FORM_LABEL_TEXT_COLOR,
        )
        main_section_label.grid(
            row=0, column=0, columnspan=2, pady=(10, 20))

        # --- Разделитель ---
        separator1 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator1.grid(row=1, column=0, columnspan=2,
                        sticky="ew", padx=10)

        # --- Личные данные ---
        personal_info_label = ctk.CTkLabel(
            self, text="Личные данные", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        personal_info_label.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        personal_info_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        personal_info_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=10)

        # --- Табельный номер (нередактируемый) ---
        ctk.CTkLabel(personal_info_frame, text="Табельный номер", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.personnel_number_entry = ctk.CTkEntry(
            personal_info_frame, width=200, font=DEFAULT_FONT, state="disabled")  # disabled
        self.personnel_number_entry.grid(
            row=1, column=0, sticky="w",  pady=(0, 10))

        # --- Фамилия ---
        ctk.CTkLabel(personal_info_frame, text="Фамилия", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.lastname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.lastname_entry.grid(row=3, column=0, sticky="w",  pady=(0, 10))
        self.lastname_entry.bind("<KeyRelease>", self.check_fields)

        # --- Имя ---
        ctk.CTkLabel(personal_info_frame, text="Имя", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=4, column=0, sticky="w",  pady=(0, 2))
        self.firstname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.firstname_entry.grid(row=5, column=0, sticky="w", pady=(0, 10))
        self.firstname_entry.bind("<KeyRelease>", self.check_fields)

        # --- Отчество ---
        ctk.CTkLabel(personal_info_frame, text="Отчество", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=6, column=0, sticky="w",  pady=(0, 2))
        self.middlename_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.middlename_entry.grid(row=7, column=0, sticky="w",  pady=(0, 10))

        # --- Разделитель ---
        separator2 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator2.grid(row=4, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        # --- Дата рождения ---
        birthdate_label = ctk.CTkLabel(
            self, text="Дата рождения", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        birthdate_label.grid(
            row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        birthdate_frame = ctk.CTkFrame(self, fg_color="transparent")
        birthdate_frame.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=10)

        # --- День ---
        ctk.CTkLabel(birthdate_frame, text="День", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.birth_day_combo = ctk.CTkComboBox(
            birthdate_frame,
            values=[str(i) for i in range(1, 32)],
            width=60, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields
        )
        self.birth_day_combo.grid(
            row=1, column=0, sticky="w", padx=(0, 5), pady=(0, 10))

        # --- Месяц ---
        ctk.CTkLabel(birthdate_frame, text="Месяц", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=1, sticky="w",  pady=(0, 2))
        self.birth_month_combo = ctk.CTkComboBox(
            birthdate_frame,
            values=[
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ],
            width=100, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields
        )
        self.birth_month_combo.grid(
            row=1, column=1, sticky="w", padx=(0, 5), pady=(0, 10))

        # --- Год ---
        ctk.CTkLabel(birthdate_frame, text="Год", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=2, sticky="w", pady=(0, 2))
        self.birth_year_entry = ctk.CTkEntry(
            birthdate_frame,
            width=80, font=DEFAULT_FONT
        )
        self.birth_year_entry.grid(
            row=1, column=2, sticky="w", padx=(0, 10), pady=(0, 10))
        self.birth_year_entry.bind("<KeyRelease>", self.check_fields)

        # --- Пол ---
        ctk.CTkLabel(birthdate_frame, text="Пол", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.gender_combo = ctk.CTkComboBox(
            birthdate_frame, values=[],
            width=150, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields
        )
        self.gender_combo.grid(
            row=3, column=0, columnspan=3, sticky="w",  pady=(0, 10))

        # --- Разделитель ---
        separator3 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator3.grid(row=7, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        # --- Информация о работе ---
        work_info_label = ctk.CTkLabel(
            self, text="Информация о работе", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        work_info_label.grid(
            row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        work_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        work_info_frame.grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=10)

        # --- Должность ---
        ctk.CTkLabel(work_info_frame, text="Должность", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.position_combo = ctk.CTkComboBox(
            work_info_frame, values=[],
            width=200, font=DEFAULT_FONT,
            state="readonly",
            command=self.update_departments
        )
        self.position_combo.grid(
            row=1, column=0, sticky="w",  pady=(0, 10))

        # --- Подразделение ---
        ctk.CTkLabel(work_info_frame, text="Подразделение", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.department_label = ctk.CTkLabel(
            work_info_frame, text="", font=DEFAULT_FONT, text_color=LABEL_TEXT_COLOR, anchor="w", width=200)
        self.department_label.grid(row=3, column=0, sticky="w", pady=(0, 10))

        # --- Состояние ---
        ctk.CTkLabel(work_info_frame, text="Состояние", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=4, column=0, sticky="w",  pady=(0, 2))
        self.state_combo = ctk.CTkComboBox(
            work_info_frame, values=[],
            width=200, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields
        )
        self.state_combo.grid(row=5, column=0, sticky="w", pady=(0, 10))

        # --- Кнопки ---
        buttons_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=20)

        self.update_button = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            font=DEFAULT_FONT,
            command=self.update_employee,
            fg_color="#0057FC",
            text_color="white",
            hover_color="gray",
            border_width=1,
            border_color="#000000",
            width=87,
            height=40

        )
        self.update_button.pack(side="left", padx=10)

        self.reset_button = ctk.CTkButton(
            buttons_frame,
            text="Сбросить",
            font=DEFAULT_FONT,
            command=self.restore_fields,
            fg_color="transparent",
            text_color="white",
            hover_color="gray",
            border_width=1,
            border_color="white",
            width=87,
            height=40
        )
        self.reset_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            font=DEFAULT_FONT,
            command=self.cancel,
            fg_color="transparent",
            text_color="white",
            hover_color="gray",
            border_width=1,
            border_color="white",
            width=87,
            height=40
        )
        cancel_button.pack(side="left", padx=10)

        self.load_combobox_data()

        # --- Настройка весов строк и столбцов ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        personal_info_frame.grid_columnconfigure(0, weight=1)
        birthdate_frame.grid_columnconfigure(0, weight=0)
        birthdate_frame.grid_columnconfigure(1, weight=0)
        birthdate_frame.grid_columnconfigure(2, weight=1)
        work_info_frame.grid_columnconfigure(0, weight=1)

        # Заполняем поля данными о сотруднике
        self.fill_fields()
        log.debug("Виджеты EditEmployeeDialog созданы")

    def load_combobox_data(self):
        """Загружает данные в выпадающие списки."""
        log.debug("Загрузка данных в комбобоксы (EditEmployeeDialog)")

        # !!! Используем соответствующие репозитории
        genders = self.gender_repository.get_all()
        positions = self.position_repository.get_all()
        states = self.state_repository.get_all()

        if genders is None or positions is None or states is None:
            messagebox.showerror(
                "Ошибка", "Ошибка при загрузке данных для выпадающих списков!")
            log.error("Ошибка при загрузке данных в комбобоксы")
            return

        self.gender_combo.configure(values=[g[1] for g in genders])
        self.position_combo.configure(values=[p[1] for p in positions])
        self.state_combo.configure(values=[s[1] for s in states])

        self.update_departments()

    def update_departments(self, event=None):
        """
        Обновляет список доступных подразделений в зависимости от выбранной должности.
        """
        selected_position = self.position_combo.get()
        if not selected_position:
            self.department_label.configure(text="")
            log.debug("Подразделения не отображаются (должность не выбрана)")
            return

        #  Получаем ID
        position_id = self.position_repository.get_by_name(
            selected_position)  # !!!
        departments = self.position_repository.get_departments_for_position(
            position_id)  # !!!

        if departments is None:
            messagebox.showerror(
                "Ошибка", "Ошибка при получении списка подразделений!")
            log.warning(
                f"Не удалось получить список подразделений для должности: {selected_position}")
            self.department_label.configure(text="")
            return

        log.debug(
            f"Выбрана должность: {selected_position}, position_id={position_id}")
        department_names = [d[0] for d in departments]
        self.department_label.configure(text=", ".join(department_names))
        log.debug(f"Отображаемые подразделения: {department_names}")
        self.check_fields()

    def update_employee(self):
        """
        Обновляет данные сотрудника в базе данных,
        и, если необходимо, создает запись о кадровом событии.
        """
        log.info("Обновление данных сотрудника")

        personnel_number = self.personnel_number_entry.get().strip()
        lastname = self.lastname_entry.get().strip()
        firstname = self.firstname_entry.get().strip()
        middlename = self.middlename_entry.get().strip()
        birth_year = self.birth_year_entry.get().strip()
        birth_month = self.birth_month_combo.get()
        birth_day = self.birth_day_combo.get().strip()
        gender = self.gender_combo.get()
        position = self.position_combo.get()
        department = self.department_label.cget("text")
        state = self.state_combo.get()

        # --- Валидация ---
        if not all([personnel_number, lastname, firstname, birth_year, birth_month, birth_day, gender, position, department, state]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!")
            log.warning("Не все поля заполнены")
            return

        if not re.match(r"^[а-яА-ЯёЁ -]+$", lastname):
            messagebox.showerror(
                "Ошибка", "Некорректная фамилия! Только русские буквы, пробелы и дефисы.")
            log.warning(f"Некорректное имя: {firstname}")
            return
        if not re.match(r"^[а-яА-ЯёЁ -]+$", firstname):
            messagebox.showerror(
                "Ошибка", "Некорректное имя! Только русские буквы, пробелы и дефисы.")
            log.warning(f"Некорректное имя: {firstname}")
            return

        if middlename != "" and not re.match(r"^[а-яА-ЯёЁ -]+$", middlename):
            messagebox.showerror(
                "Ошибка", "Некорректное отчество! Только русские буквы, пробелы и дефисы.")
            log.warning(f"Некорректное отчество: {middlename}")
            return
        if len(lastname) > 50:
            messagebox.showerror("Ошибка", "Слишком длинная фамилия")
            log.warning(f"Слишком длинная фамилия: {lastname}")
            return
        if len(firstname) > 50:
            messagebox.showerror("Ошибка", "Слишком длинное имя")
            log.warning(f"Слишком длинное имя: {firstname}")
            return
        if len(middlename) > 50:
            messagebox.showerror("Ошибка", "Слишком длинное отчество")
            log.warning(f"Слишком длинное отчество: {middlename}")
            return

        try:
            birth_year = int(birth_year)
            if not (1900 <= birth_year <= datetime.date.today().year):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный год рождения!")
            log.warning(f"Некорректный год рождения: {birth_year}")
            return
        try:
            birth_day = int(birth_day)
        except ValueError:
            messagebox.showerror("Ошибка", "День должен быть числом")
            log.warning(f"День рождения не число: {birth_day}")
            return

        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        try:
            birth_month_index = month_names.index(birth_month) + 1
        except ValueError:
            messagebox.showerror("Ошибка", "Недопустимый месяц")
            log.warning(f"Недопустимый месяц: {birth_month}")
            return

        try:
            birth_date = datetime.date(
                birth_year, birth_month_index, int(birth_day))
            today = datetime.date.today()
            if birth_date > today:
                messagebox.showerror(
                    "Ошибка", "Дата рождения не может быть в будущем!")
                log.warning("Дата рождения в будущем")
                return
            age = today.year - birth_date.year - \
                ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                messagebox.showerror(
                    "Ошибка", "Сотрудник должен быть совершеннолетним!")
                log.warning("Сотрудник младше 18 лет")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная дата рождения!")
            log.warning(
                f"Некорректная дата рождения: {birth_year}-{birth_month_index}-{birth_day}")
            return

        birth_date_str = f"{birth_year}-{birth_month_index:02}-{birth_day:02}"
        # --- Конец валидации ---

        update_employee_data = True

        # --- Определение кадрового события и открытие диалога подтверждения ---
        old_state = self.employee_data[8]
        old_department = self.employee_data[7]
        old_position = self.employee_data[6]

        new_state = self.state_combo.get()
        new_department_name = self.department_label.cget("text")
        new_position = self.position_combo.get()

        event_type = None
        if new_state != old_state:
            if new_state == "Уволен":
                event_type = "Увольнение"
            elif old_state == "Уволен" and new_state == "Работает":
                event_type = "Прием"
            elif new_state == "Недоступен":
                event_type = "Недоступен"
            elif old_state == "Недоступен" and new_state == "Работает":
                event_type = "Возвращение к работе"

        elif new_department_name != old_department or new_position != old_position:
            event_type = "Перемещение"

        if event_type:
            department_id = None
            if new_department_name:
                department_ids = self.department_repository.get_by_name(
                    new_department_name)
                department_id = [
                    item[0] for item in department_ids][0] if department_ids else None

            position_id = self.position_repository.get_by_name(new_position)

            # --- Диалог подтверждения ---
            dialog = ConfirmEventDialog(self, event_type,
                                        f"{self.employee_data[2]} {self.employee_data[1]} {self.employee_data[3]}",
                                        self.employee_event_repository,  # !!!  ИСПРАВЛЕНО
                                        personnel_number,
                                        department_id,
                                        position_id)
            dialog.wait_window()

            #  Проверяем, было ли подтверждено событие.
            if not dialog.was_confirmed():  # Изменено
                update_employee_data = False

        # --- Обновление данных сотрудника (если не было отмены) ---
        if update_employee_data:
            gender_id = self.gender_repository.get_by_name(gender)
            position_id = self.position_repository.get_by_name(position)
            dep_ids = self.department_repository.get_by_name(department)
            department_id = [item[0]
                             for item in dep_ids][0] if dep_ids else None  # !!!
            state_id = self.state_repository.get_by_name(state)

            log.debug(
                f"Полученные ID: gender_id={gender_id}, position_id={position_id}, department_id={department_id}, state_id={state_id}")

            if gender_id is None or position_id is None or department_id is None or state_id is None:
                messagebox.showerror(
                    "Ошибка", "Не найдена запись в справочнике!")
                log.error("Не найдены ID в справочниках")
                return

            success = self.employee_repository.update_employee(
                personnel_number, lastname, firstname, middlename, birth_date_str,
                gender_id, position_id, department_id, state_id
            )

            if success:
                messagebox.showinfo("Успех", "Данные сотрудника обновлены!")
                log.info(f"Данные сотрудника {personnel_number} обновлены")
                self.destroy()  # Закрываем диалог редактирования
                if self.master and hasattr(self.master, "display_data"):
                    self.master.display_data()  # Обновляем данные в EmployeesFrame
            else:
                messagebox.showerror(
                    "Ошибка", "Ошибка при обновлении данных сотрудника!")
                log.error(
                    f"Ошибка при обновлении данных сотрудника {personnel_number}")

    def restore_fields(self):
        """
        Восстанавливает исходные значения полей диалога (до редактирования).
        """
        log.debug("Восстановление исходных значений полей")
        self.personnel_number_entry.configure(state="normal")
        self.personnel_number_entry.delete(0, "end")
        self.personnel_number_entry.insert(
            0, self.employee_data[0])  # Табельный номер
        self.personnel_number_entry.configure(state="disabled")

        self.lastname_entry.delete(0, "end")
        self.lastname_entry.insert(0, self.employee_data[1])  # Фамилия

        self.firstname_entry.delete(0, "end")
        self.firstname_entry.insert(0, self.employee_data[2])  # Имя

        self.middlename_entry.delete(0, "end")
        self.middlename_entry.insert(0, self.employee_data[3])  # Отчество

        # Дата рождения
        year, month, day = self.employee_data[4].split("-")
        self.birth_year_entry.delete(0, "end")
        self.birth_year_entry.insert(0, year)

        # !!! ИСПОЛЬЗУЕМ СЛОВАРЬ !!!
        month_map = {
            "January": "Январь",
            "February": "Февраль",
            "March": "Март",
            "April": "Апрель",
            "May": "Май",
            "June": "Июнь",
            "July": "Июль",
            "August": "Август",
            "September": "Сентябрь",
            "October": "Октябрь",
            "November": "Ноябрь",
            "December": "Декабрь"
        }
        month_name_en = datetime.date(
            int(year), int(month), int(day)).strftime("%B")
        self.birth_month_combo.set(
            month_map[month_name_en])  # Используем словарь!
        self.birth_day_combo.set(day)

        self.gender_combo.set(self.employee_data[5])   # Пол
        self.position_combo.set(self.employee_data[6])  # Должность
        self.department_label.configure(text=self.employee_data[7])
        self.state_combo.set(self.employee_data[8])      # Состояние

        self.check_fields()

    def fill_fields(self):
        """
        Заполняет поля диалога данными о сотруднике при открытии.
        """
        log.debug("Заполнение полей данными сотрудника")
        self.personnel_number_entry.configure(state="normal")
        self.personnel_number_entry.insert(0, self.employee_data[0])
        self.personnel_number_entry.configure(state="disabled")
        self.lastname_entry.insert(0, self.employee_data[1])
        self.firstname_entry.insert(0, self.employee_data[2])
        self.middlename_entry.insert(0, self.employee_data[3])

        year, month, day = self.employee_data[4].split("-")
        self.birth_year_entry.insert(0, year)

        # --- ИСПОЛЬЗУЕМ СЛОВАРЬ ДЛЯ МЕСЯЦЕВ ---
        month_map = {  # Словарь для перевода английских названий месяцев в русские
            "January": "Январь",
            "February": "Февраль",
            "March": "Март",
            "April": "Апрель",
            "May": "Май",
            "June": "Июнь",
            "July": "Июль",
            "August": "Август",
            "September": "Сентябрь",
            "October": "Октябрь",
            "November": "Ноябрь",
            "December": "Декабрь"
        }
        month_name_en = datetime.date(int(year), int(month), int(day)).strftime(
            "%B")  # Получаем название месяца на английском
        # Устанавливаем русское название
        self.birth_month_combo.set(month_map[month_name_en])
        # ---------------------------------------

        self.birth_day_combo.set(day)

        self.gender_combo.set(self.employee_data[5])
        self.position_combo.set(self.employee_data[6])
        self.department_label.configure(text=self.employee_data[7])
        self.state_combo.set(self.employee_data[8])
        self.check_fields()

    def check_fields(self, event=None):
        """
        Проверяет, заполнены ли все обязательные поля, и управляет состоянием кнопки "Сохранить".
        """
        current_state = self.update_button.cget("state")

        all_filled = (
            self.personnel_number_entry.get()
            and self.lastname_entry.get()
            and self.firstname_entry.get()
            and self.birth_year_entry.get()
            and self.birth_month_combo.get()
            and self.birth_day_combo.get()
            and self.gender_combo.get()
            and self.position_combo.get()
            and self.department_label.cget("text")
            and self.state_combo.get()
        )
        log.debug(
            f"Проверка заполненности полей. Результат: {all_filled}")

        if all_filled and current_state == "disabled":
            self.update_button.configure(
                state="normal", fg_color="#0057FC", text_color="white")
        elif not all_filled and current_state == "normal":
            self.update_button.configure(
                state="disabled",  fg_color="transparent", text_color=BUTTON_DISABLED_TEXT_COLOR)

    def cancel(self):
        """
        Закрывает диалог без сохранения изменений.
        """
        log.debug("Закрытие диалога EditEmployeeDialog без сохранения")
        self.destroy()

    def insert_event(self, personnel_number, event_id, event_date, department_id, position_id, reason=None):
        """Добавляет запись о кадровом событии."""

        log.debug(
            f"Добавление кадрового события: personnel_number={personnel_number}, event_id={event_id}, event_date={event_date}, department_id={department_id}, position_id={position_id}, reason={reason}")

        params = (personnel_number, event_id, event_date,
                  department_id, position_id, reason)
        result = self.db.execute_query(
            q.INSERT_EMPLOYEE_EVENT, params)  # !!! ЗАПРОС НИЖЕ!!!

        log.debug(f"Результат добавления кадрового события: {result}")  # !!!
        return result

import customtkinter as ctk
from config import *  # Для констант
import re  # Для валидации
from tkinter import messagebox  # !!!  Для messagebox
import datetime


class AddEmployeeDialog(ctk.CTkToplevel):  # !!! Наследуемся от CTkToplevel
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("Добавить сотрудника")
        self.geometry("650x920")  # Увеличил высоту
        self.resizable(False, False)
        self.create_widgets()
        self.grab_set()
        self.check_fields()

    def create_widgets(self):
        # Шрифт для заголовков разделов
        section_font = ("Arial", 20, "bold")

        # Раздел 1:  Добавить сотрудника
        main_section_label = ctk.CTkLabel(
            self,
            text="ДОБАВИТЬ СОТРУДНИКА",
            font=("Arial", 28, "bold"),
            text_color=BUTTON_ACTIVE_BG_COLOR,
        )
        main_section_label.grid(
            row=0, column=0, columnspan=2, pady=(10, 20))

        # --- Разделитель (белая линия) ---
        separator1 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator1.grid(row=1, column=0, columnspan=2,
                        sticky="ew", padx=10)

        # --- Раздел 2: Личные данные ---
        personal_info_label = ctk.CTkLabel(
            self, text="Личные данные", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        personal_info_label.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        personal_info_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        personal_info_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=10)

        # Табельный номер
        ctk.CTkLabel(personal_info_frame, text="Табельный номер", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.personnel_number_entry = ctk.CTkEntry(
            personal_info_frame, width=200, font=DEFAULT_FONT)
        self.personnel_number_entry.grid(
            row=1, column=0, sticky="w",  pady=(0, 10))
        self.personnel_number_entry.bind(
            "<KeyRelease>", self.check_fields)

        # Фамилия
        ctk.CTkLabel(personal_info_frame, text="Фамилия", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.lastname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.lastname_entry.grid(row=3, column=0, sticky="w",  pady=(0, 10))
        self.lastname_entry.bind("<KeyRelease>", self.check_fields)

        # Имя
        ctk.CTkLabel(personal_info_frame, text="Имя", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=4, column=0, sticky="w",  pady=(0, 2))
        self.firstname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.firstname_entry.grid(row=5, column=0, sticky="w", pady=(0, 10))
        self.firstname_entry.bind("<KeyRelease>", self.check_fields)

        # Отчество
        ctk.CTkLabel(personal_info_frame, text="Отчество", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=6, column=0, sticky="w",  pady=(0, 2))
        self.middlename_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.middlename_entry.grid(row=7, column=0, sticky="w",  pady=(0, 10))

        # --- Разделитель (белая линия) ---
        separator2 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator2.grid(row=4, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        # --- Раздел 3: Дата рождения ---

        birthdate_label = ctk.CTkLabel(
            self, text="Дата рождения", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        birthdate_label.grid(
            row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        # !!!  Создаем отдельный фрейм
        birthdate_frame = ctk.CTkFrame(self, fg_color="transparent")
        birthdate_frame.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=10)

        # День
        ctk.CTkLabel(birthdate_frame, text="День", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.birth_day_combo = ctk.CTkComboBox(
            birthdate_frame,
            values=[str(i) for i in range(1, 32)],  # Дни (1-31)
            width=60, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields
        )
        self.birth_day_combo.grid(
            row=1, column=0, sticky="w", padx=(0, 5), pady=(0, 10))

        # Месяц
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

        # Год
        ctk.CTkLabel(birthdate_frame, text="Год", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=2, sticky="w", pady=(0, 2))
        self.birth_year_entry = ctk.CTkEntry(
            birthdate_frame,
            width=80, font=DEFAULT_FONT
        )
        self.birth_year_entry.grid(
            row=1, column=2, sticky="w", padx=(0, 10), pady=(0, 10))
        self.birth_year_entry.bind("<KeyRelease>", self.check_fields)

        # Пол
        ctk.CTkLabel(birthdate_frame, text="Пол", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))  # !!!
        self.gender_combo = ctk.CTkComboBox(
            birthdate_frame, values=[],
            width=150, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields  # !!!
        )
        self.gender_combo.grid(
            row=3, column=0, columnspan=3, sticky="w",  pady=(0, 10))

        # --- Разделитель (белая линия) ---
        separator3 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator3.grid(row=7, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        # --- Раздел 4: Информация о работе ---
        work_info_label = ctk.CTkLabel(
            self, text="Информация о работе", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        work_info_label.grid(
            row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        work_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        work_info_frame.grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=10)

        # Должность
        ctk.CTkLabel(work_info_frame, text="Должность", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        self.position_combo = ctk.CTkComboBox(
            work_info_frame, values=[],
            width=200, font=DEFAULT_FONT,
            state="readonly",
            command=self.update_departments  # !!!
        )
        self.position_combo.grid(
            row=1, column=0, sticky="w",  pady=(0, 10))

        # Подразделение
        ctk.CTkLabel(work_info_frame, text="Подразделение", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        # !!!  Заменили на CTkLabel
        self.department_label = ctk.CTkLabel(
            work_info_frame, text="", font=DEFAULT_FONT, text_color=LABEL_TEXT_COLOR, anchor="w", width=200)
        self.department_label.grid(row=3, column=0, sticky="w", pady=(0, 10))

        # Состояние
        ctk.CTkLabel(work_info_frame, text="Состояние", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=4, column=0, sticky="w",  pady=(0, 2))
        self.state_combo = ctk.CTkComboBox(
            work_info_frame, values=[],
            width=200, font=DEFAULT_FONT,
            state="readonly",
            command=self.check_fields  # !!!
        )
        self.state_combo.grid(row=5, column=0, sticky="w", pady=(0, 10))

        # Кнопки
        buttons_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=20)

        self.save_button = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            font=DEFAULT_FONT,
            command=self.save_employee,
            fg_color="transparent",
            text_color="white",
            hover_color="gray",
            border_width=1,
            border_color="#000000",
            width=87,
            height=40

        )
        self.save_button.pack(side="left", padx=10)

        self.reset_button = ctk.CTkButton(
            buttons_frame,
            text="Сбросить",
            font=DEFAULT_FONT,
            command=self.reset_fields,
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

        # Настраиваем веса столбцов и строк
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        personal_info_frame.grid_columnconfigure(0, weight=1)
        birthdate_frame.grid_columnconfigure(0, weight=0)
        birthdate_frame.grid_columnconfigure(1, weight=0)
        birthdate_frame.grid_columnconfigure(2, weight=1)
        work_info_frame.grid_columnconfigure(0, weight=1)

    def load_combobox_data(self):
        genders = self.db.fetch_all("SELECT GenderName FROM Genders")
        positions = self.db.fetch_all("SELECT Name FROM Positions")
        states = self.db.fetch_all("SELECT StateName FROM States")
        # departments = self.db.fetch_all("SELECT Name FROM Departments") #Убираем

        if genders is None or positions is None or states is None:  # departments больше нет
            messagebox.showerror(
                "Ошибка", "Ошибка при загрузке данных для выпадающих списков!")
            return

        self.gender_combo.configure(values=[g[0] for g in genders])
        self.position_combo.configure(values=[p[0] for p in positions])
        # self.department_combo.configure(values=[d[0] for d in departments]) #Убираем
        self.state_combo.configure(values=[s[0] for s in states])
        # !!!  Вызываем update_departments, чтобы изначально установить правильные значения
        self.update_departments()

    # !!! Новый метод для обновления списка подразделений
    def update_departments(self, event=None):
        selected_position = self.position_combo.get()
        if not selected_position:
            self.department_label.configure(text="")  # Пустое
            return
        # Получаем ID
        position_id = self.db.fetch_one(
            "SELECT ID FROM Positions WHERE Name = ?", (selected_position,))[0]

        departments = self.db.get_departments_for_position(position_id)

        if departments is None:
            messagebox.showerror(
                "Ошибка", "Ошибка при получении списка подразделений!")
            self.department_label.configure(text="")  # Пустое
            return

        # Отображаем название подразделения в label
        # !!!  Распаковываем кортежи и объединяем названия через запятую
        department_names = [d[0] for d in departments]  # !!!
        self.department_label.configure(
            text=", ".join(department_names))  # !!!
        self.check_fields()

    def save_employee(self):
        personnel_number = self.personnel_number_entry.get().strip()
        lastname = self.lastname_entry.get().strip()
        firstname = self.firstname_entry.get().strip()
        middlename = self.middlename_entry.get().strip()
        birth_year = self.birth_year_entry.get().strip()
        birth_month = self.birth_month_combo.get()
        birth_day = self.birth_day_combo.get().strip()
        gender = self.gender_combo.get()
        position = self.position_combo.get()
        department = self.department_label.cget("text")  # !!!
        state = self.state_combo.get()

        # ---  ВАЛИДАЦИЯ  ---
        if not all([personnel_number, lastname, firstname, birth_year, birth_month, birth_day, gender, position, department, state]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!")
            return

        # Табельный номер (только цифры, максимум 10 символов)
        if not re.match(r"^\d{1,10}$", personnel_number):
            messagebox.showerror(
                "Ошибка", "Некорректный табельный номер! До 10 цифр.")
            return

        # ФИО (буквы, пробелы, дефисы, ограничения по длине)
        if not re.match(r"^[а-яА-ЯёЁ -]+$", lastname):
            messagebox.showerror(
                "Ошибка", "Некорректная фамилия! Только русские буквы, пробелы и дефисы.")
            return
        if not re.match(r"^[а-яА-ЯёЁ -]+$", firstname):
            messagebox.showerror(
                "Ошибка", "Некорректное имя! Только русские буквы, пробелы и дефисы.")
            return
        if middlename != "" and not re.match(r"^[а-яА-ЯёЁ -]+$", middlename):
            messagebox.showerror(
                "Ошибка", "Некорректное отчество! Только русские буквы, пробелы и дефисы.")
            return
        if len(lastname) > 50:
            messagebox.showerror("Ошибка", "Слишком длинная фамилия")
            return
        if len(firstname) > 50:
            messagebox.showerror("Ошибка", "Слишком длинное имя")
            return
        if len(middlename) > 50:
            messagebox.showerror("Ошибка", "Слишком длинное отчество")
            return
        # Год (число, 4 цифры, диапазон)
        try:
            birth_year = int(birth_year)
            if not (1900 <= birth_year <= datetime.date.today().year):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный год рождения!")
            return
        # Проверка дня
        try:
            birth_day = int(birth_day)
        except:
            messagebox.showerror("Ошибка", "День должен быть числом")
            return
        # Преобразуем месяц (текст) в число
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        try:
            birth_month_index = month_names.index(birth_month) + 1
        except ValueError:
            messagebox.showerror("Ошибка", "Недопустимый месяц")
            return
        # Дата рождения (корректность, не в будущем, не слишком давно)
        try:
            birth_date = datetime.date(
                birth_year, birth_month_index, int(birth_day))
            today = datetime.date.today()
            if birth_date > today:
                messagebox.showerror(
                    "Ошибка", "Дата рождения не может быть в будущем!")
                return

            age = today.year - birth_date.year - ((today.month, today.day) < (
                birth_date.month, birth_date.day))  # Мне лень делать datetime объект
            if age < 18:
                messagebox.showerror(
                    "Ошибка", "Сотрудник должен быть совершеннолетним!")
                return

        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная дата рождения!")
            return
            # Формируем строку
        birth_date_str = f"{birth_year}-{birth_month_index:02}-{birth_day:02}"
        # Проверка уникальности табельного номера
        if self.db.fetch_one("SELECT 1 FROM Employees WHERE PersonnelNumber = ?", (personnel_number,)):
            messagebox.showerror(
                "Ошибка", "Сотрудник с таким табельным номером уже существует!")
            return

        # 3. Получаем ID связанных сущностей
        gender_id = self.db.fetch_one(
            "SELECT ID FROM Genders WHERE GenderName = ?", (gender,))[0]
        position_id = self.db.fetch_one(
            "SELECT ID FROM Positions WHERE Name = ?", (position,))[0]
        department_id = self.db.fetch_one(
            "SELECT ID FROM Departments WHERE Name = ?", (department,))[0]
        state_id = self.db.fetch_one(
            "SELECT ID FROM States WHERE StateName=?", (state,))[0]
        if gender_id is None or position_id is None or department_id is None or state_id is None:
            messagebox.showerror("Ошибка", "Не найдена запись в справочнике!")
            return
        # 4. Формируем SQL-запрос
        query = """
            INSERT INTO Employees (PersonnelNumber, LastName, FirstName, MiddleName, BirthDate,
                                  GenderID, PositionID, DepartmentID, StateID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (personnel_number, lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id)

        # 5. Выполняем запрос
        if self.db.execute_query(query, params):
            messagebox.showinfo("Успех", "Сотрудник успешно добавлен!")
            self.destroy()
            if self.master and hasattr(self.master, "display_data"):
                self.master.display_data()
        else:
            messagebox.showerror("Ошибка", "Ошибка при добавлении сотрудника!")

    def reset_fields(self):
        # Очищаем текстовые поля
        self.personnel_number_entry.delete(0, "end")
        self.lastname_entry.delete(0, "end")
        self.firstname_entry.delete(0, "end")
        self.middlename_entry.delete(0, "end")
        self.birth_year_entry.delete(0, "end")

        # Устанавливаем combobox'ы в начальное состояние
        self.gender_combo.set("")
        self.position_combo.set("")
        self.department_label.configure(text="")  # !!!
        self.state_combo.set("")
        self.birth_day_combo.set("")
        self.birth_month_combo.set("")

        self.check_fields()  # !!!

    def check_fields(self, event=None):
        # !!!  Сохраняем текущее состояние кнопки
        current_state = self.save_button.cget("state")

        # Проверяем, заполнены ли все обязательные поля
        all_filled = (
            self.personnel_number_entry.get()
            and self.lastname_entry.get()
            and self.firstname_entry.get()
            and self.birth_year_entry.get()
            and self.birth_month_combo.get()
            and self.birth_day_combo.get()
            and self.gender_combo.get()
            and self.position_combo.get()
            and self.department_label.cget("text")  # !!!
            and self.state_combo.get()
        )

        # !!!  Изменяем состояние кнопки *только если оно изменилось*
        if all_filled and current_state == "disabled":
            self.save_button.configure(
                state="normal", fg_color="#0057FC", text_color="white")
        elif not all_filled and current_state == "normal":
            self.save_button.configure(
                state="disabled", fg_color="transparent", text_color="white")

    def cancel(self):
        self.destroy()

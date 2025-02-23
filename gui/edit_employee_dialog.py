import customtkinter as ctk
from config import *
import re
import datetime
from tkinter import messagebox


class EditEmployeeDialog(ctk.CTkToplevel):
    def __init__(self, master, db, employee_data):  # !!! Добавлен employee_data
        super().__init__(master)
        self.db = db
        self.employee_data = employee_data  # !!! Сохраняем данные о сотруднике
        self.title("Редактировать сотрудника")  # !!! Изменен заголовок
        self.geometry("650x920")
        self.resizable(False, False)
        self.create_widgets()
        self.grab_set()
        self.check_fields()

    def create_widgets(self):
        section_font = ("Arial", 20, "bold")

        main_section_label = ctk.CTkLabel(
            self,
            text="РЕДАКТИРОВАТЬ СОТРУДНИКА",  # !!!
            font=("Arial", 28, "bold"),
            text_color=FORM_LABEL_TEXT_COLOR,
        )
        main_section_label.grid(
            row=0, column=0, columnspan=2, pady=(10, 20))

        separator1 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator1.grid(row=1, column=0, columnspan=2,
                        sticky="ew", padx=10)

        personal_info_label = ctk.CTkLabel(
            self, text="Личные данные", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        personal_info_label.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        personal_info_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        personal_info_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=10)

        ctk.CTkLabel(personal_info_frame, text="Табельный номер", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w",  pady=(0, 2))
        # !!!  Поле для табельного номера *нередактируемое*
        self.personnel_number_entry = ctk.CTkEntry(
            personal_info_frame, width=200, font=DEFAULT_FONT, state="disabled")  # !!! disabled
        self.personnel_number_entry.grid(
            row=1, column=0, sticky="w",  pady=(0, 10))
        # !!!  Убрали привязку check_fields, т.к. поле нередактируемое

        ctk.CTkLabel(personal_info_frame, text="Фамилия", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.lastname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.lastname_entry.grid(row=3, column=0, sticky="w",  pady=(0, 10))
        self.lastname_entry.bind("<KeyRelease>", self.check_fields)

        ctk.CTkLabel(personal_info_frame, text="Имя", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=4, column=0, sticky="w",  pady=(0, 2))
        self.firstname_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.firstname_entry.grid(row=5, column=0, sticky="w", pady=(0, 10))
        self.firstname_entry.bind("<KeyRelease>", self.check_fields)

        ctk.CTkLabel(personal_info_frame, text="Отчество", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=6, column=0, sticky="w",  pady=(0, 2))
        self.middlename_entry = ctk.CTkEntry(
            personal_info_frame, width=250, font=DEFAULT_FONT)
        self.middlename_entry.grid(row=7, column=0, sticky="w",  pady=(0, 10))

        separator2 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator2.grid(row=4, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        birthdate_label = ctk.CTkLabel(
            self, text="Дата рождения", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        birthdate_label.grid(
            row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        birthdate_frame = ctk.CTkFrame(self, fg_color="transparent")
        birthdate_frame.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=10)

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

        ctk.CTkLabel(birthdate_frame, text="Год", font=DEFAULT_FONT, text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=0, column=2, sticky="w", pady=(0, 2))
        self.birth_year_entry = ctk.CTkEntry(
            birthdate_frame,
            width=80, font=DEFAULT_FONT
        )
        self.birth_year_entry.grid(
            row=1, column=2, sticky="w", padx=(0, 10), pady=(0, 10))
        self.birth_year_entry.bind("<KeyRelease>", self.check_fields)

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

        separator3 = ctk.CTkFrame(self, height=2, fg_color="white")
        separator3.grid(row=7, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(10, 5))

        work_info_label = ctk.CTkLabel(
            self, text="Информация о работе", font=section_font, text_color=FORM_LABEL_TEXT_COLOR)
        work_info_label.grid(
            row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        work_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        work_info_frame.grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=10)

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

        ctk.CTkLabel(work_info_frame, text="Подразделение", font=DEFAULT_FONT,
                     text_color=FORM_LABEL_TEXT_COLOR
                     ).grid(row=2, column=0, sticky="w",  pady=(0, 2))
        self.department_label = ctk.CTkLabel(
            work_info_frame, text="", font=DEFAULT_FONT, text_color=LABEL_TEXT_COLOR, anchor="w", width=200)
        self.department_label.grid(row=3, column=0, sticky="w", pady=(0, 10))

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

        # Кнопки
        buttons_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=20)

        # !!!  Изменили текст кнопки
        self.update_button = ctk.CTkButton(  # !!!  Другое имя переменной
            buttons_frame,
            text="Сохранить",
            font=DEFAULT_FONT,
            command=self.update_employee,  # !!!  Другой метод
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
            text="Сбросить",  # !!!  Другой текст
            font=DEFAULT_FONT,
            command=self.restore_fields,  # !!!  Другой метод
            fg_color="transparent",
            text_color="white",
            hover_color="gray",
            border_width=1,
            border_color="white",
            width=87,  # !!!
            height=40  # !!!
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
            width=87,  # !!!
            height=40  # !!!
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

        # !!!  Заполняем поля данными о сотруднике
        self.fill_fields()

    def load_combobox_data(self):
        genders = self.db.fetch_all("SELECT GenderName FROM Genders")
        positions = self.db.fetch_all("SELECT Name FROM Positions")
        # departments = self.db.fetch_all("SELECT Name FROM Departments")
        states = self.db.fetch_all("SELECT StateName FROM States")

        if genders is None or positions is None or states is None:
            messagebox.showerror(
                "Ошибка", "Ошибка при загрузке данных для выпадающих списков!")
            return

        self.gender_combo.configure(values=[g[0] for g in genders])
        self.position_combo.configure(values=[p[0] for p in positions])
        # self.department_combo.configure(values=[d[0] for d in departments])
        self.state_combo.configure(values=[s[0] for s in states])
        self.update_departments()

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
            self.department_label.configure(text="")
            return

        department_names = [d[0] for d in departments]
        self.department_label.configure(text=", ".join(department_names))
        self.check_fields()
    # !!!  Переименовали метод

    def update_employee(self):
        # 1. Получаем данные (изменен способ получения подразделения)
        personnel_number = self.personnel_number_entry.get().strip()
        lastname = self.lastname_entry.get().strip()
        firstname = self.firstname_entry.get().strip()
        middlename = self.middlename_entry.get().strip()
        birth_year = self.birth_year_entry.get().strip()
        birth_month = self.birth_month_combo.get()
        birth_day = self.birth_day_combo.get().strip()
        gender = self.gender_combo.get()
        position = self.position_combo.get()
        # !!!  Теперь получаем значение из label
        department = self.department_label.cget("text")
        state = self.state_combo.get()

        # ---  ВАЛИДАЦИЯ  ---
        # (Такая же, как в AddEmployeeDialog, можно вынести в отдельную функцию)
        if not all([personnel_number, lastname, firstname, birth_year, birth_month, birth_day, gender, position, department, state]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!")
            return
        try:
            birth_year = int(birth_year)
            birth_day = int(birth_day)
        except ValueError:
            messagebox.showerror("Ошибка", "Год рождения должен быть числом")
            return

        if birth_year > 2024 or birth_year < 1924:
            messagebox.showerror("Ошибка", "Введите корректный год")
            return
        if birth_day > 31 or birth_day < 1:
            messagebox.showerror("Ошибка", "Введите корректный день")
            return

        #  Эта проверка больше не нужна, т.к. мы *обновляем* запись, а не добавляем новую
        # if self.db.fetch_one("SELECT 1 FROM Employees WHERE PersonnelNumber = ?", (personnel_number,)):
        #     messagebox.showerror("Ошибка", "Сотрудник с таким табельным номером уже существует!")
        #     return

        if len(lastname) > 50:
            messagebox.showerror(
                "Ошибка", "Фамилия слишком длинная (максимум 50 символов)!")
            return
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        try:
            birth_month_index = month_names.index(birth_month) + 1
        except ValueError:
            messagebox.showerror("Ошибка", "Недопустимый месяц")
            return

        # Формируем строку с датой в формате ГГГГ-ММ-ДД
        birth_date_str = f"{birth_year}-{birth_month_index:02}-{birth_day:02}"
        try:
            birth_date = datetime.date.fromisoformat(birth_date_str)
            today = datetime.date.today()
            if birth_date > today:
                messagebox.showerror(
                    "Ошибка", "Дата рождения не может быть в будущем!")
                return

            age = today.year - birth_date.year - \
                ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                messagebox.showerror(
                    "Ошибка", "Сотрудник должен быть совершеннолетним!")
                return

        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная дата рождения!")
            return

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
           UPDATE Employees
           SET LastName = ?,
               FirstName = ?,
               MiddleName = ?,
               BirthDate = ?,
               GenderID = ?,
               PositionID = ?,
               DepartmentID = ?,
               StateID = ?
           WHERE PersonnelNumber = ?  -- !!!  Обязательно добавляем условие WHERE
       """
        params = (lastname, firstname, middlename, birth_date_str, gender_id,
                  position_id, department_id, state_id, personnel_number)  # !!!

        if self.db.execute_query(query, params):
            messagebox.showinfo("Успех", "Данные сотрудника обновлены!")
            self.destroy()
            if self.master and hasattr(self.master, "display_data"):
                self.master.display_data()   # !!! Вызываем обновление таблицы
        else:
            messagebox.showerror(
                "Ошибка", "Ошибка при обновлении данных сотрудника!")

    def reset_fields(self):
        # Этот метод теперь называется restore, и он не здесь
        pass

    # !!!  Новый метод для восстановления исходных значений
    def restore_fields(self):
        # !!!  Используем данные из self.employee_data
        self.personnel_number_entry.configure(
            state="normal")  # !!! Нужно временно включить
        self.personnel_number_entry.delete(0, "end")
        self.personnel_number_entry.insert(
            0, self.employee_data[0])  # Табельный номер
        self.personnel_number_entry.configure(
            state="disabled")  # !!! Отключаем обратно

        self.lastname_entry.delete(0, "end")
        self.lastname_entry.insert(0, self.employee_data[1])  # Фамилия

        self.firstname_entry.delete(0, "end")
        self.firstname_entry.insert(0, self.employee_data[2])  # Имя

        self.middlename_entry.delete(0, "end")
        self.middlename_entry.insert(0, self.employee_data[3])  # Отчество

        # Дата рождения (разбиваем строку на части)
        year, month, day = self.employee_data[4].split("-")  # !!!
        self.birth_year_entry.delete(0, "end")
        self.birth_year_entry.insert(0, year)  # !!!
        self.birth_month_combo.set(datetime.date(int(year), int(
            month), int(day)).strftime("%B"))  # !!!  Используем strftime
        self.birth_day_combo.set(day)    # !!!

        self.gender_combo.set(self.employee_data[5])          # Пол
        self.position_combo.set(self.employee_data[6])        # Должность
        # !!! Подразделение (теперь label)
        self.department_label.configure(text=self.employee_data[7])
        self.state_combo.set(self.employee_data[8])          # Состояние

        self.check_fields()

    # !!!
    def fill_fields(self):
        # Заполняем поля данными о сотруднике при открытии диалога
        self.personnel_number_entry.configure(state="normal")
        # Табельный номер - в первую очередь
        self.personnel_number_entry.insert(0, self.employee_data[0])
        self.personnel_number_entry.configure(state="disabled")
        self.lastname_entry.insert(0, self.employee_data[1])  # Фамилия
        self.firstname_entry.insert(0, self.employee_data[2])  # Имя
        self.middlename_entry.insert(0, self.employee_data[3])  # Отчество

        year, month, day = self.employee_data[4].split("-")

        self.birth_year_entry.insert(0, year)  # !!!

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

        # получаем название месяца на английском
        month_name_en = datetime.date(
            int(year), int(month), int(day)).strftime("%B")

        # !!!  Используем словарь
        self.birth_month_combo.set(month_map[month_name_en])
        self.birth_day_combo.set(day)    # !!!
        #!!!

        self.gender_combo.set(self.employee_data[5])  # Пол
        self.position_combo.set(self.employee_data[6])  # !!!
        self.department_label.configure(text=self.employee_data[7])  # !!!
        self.state_combo.set(self.employee_data[8])  # !!!
        self.check_fields()

    def check_fields(self, event=None):
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

        if all_filled and current_state == "disabled":
            self.update_button.configure(
                state="normal", fg_color="#0057FC", text_color="white")
        elif not all_filled and current_state == "normal":
            self.update_button.configure(
                state="disabled",  fg_color="transparent", text_color=BUTTON_DISABLED_TEXT_COLOR)

    def cancel(self):
        self.destroy()

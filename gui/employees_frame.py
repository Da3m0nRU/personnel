# gui/employees_frame.py

import customtkinter as ctk
from config import *
from tksheet import Sheet
from .utils import load_icon
from .dialogs.add_employee_dialog import AddEmployeeDialog
from .dialogs.edit_employee_dialog import EditEmployeeDialog
from tkinter import messagebox
import logging

log = logging.getLogger(__name__)


class EmployeesFrame(ctk.CTkFrame):
    """
    Вкладка "Сотрудники".

    Отображает список сотрудников, позволяет добавлять, редактировать и удалять записи.
    """

    def __init__(self, master, db):
        """
        Инициализирует вкладку "Сотрудники".

        Args:
            master (ctk.CTkFrame): Родительский виджет (область контента главного окна).
            db (Database): Объект базы данных.
        """
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        self.current_page = 1
        self.rows_per_page = 10
        self.total_rows = 0
        self.all_data = []
        self.data = []
        self.create_widgets()
        self.load_data()
        self.display_data()
        log.debug("Инициализирован фрейм EmployeesFrame")

    def create_widgets(self):
        """
        Создает виджеты вкладки.
        """
        log.debug("Создание виджетов для EmployeesFrame")
        section_font = ("Arial", 20, "bold")

        # --- Заголовок ---
        title_label = ctk.CTkLabel(
            self,
            text="СОТРУДНИКИ",
            font=("Arial", 46, "bold"),
            text_color=LABEL_TEXT_COLOR,
            anchor="w"
        )
        title_label.place(x=27, y=40)

        # --- Кнопка "Добавить" ---
        self.add_button = ctk.CTkButton(
            self,
            text="  НОВАЯ ЗАПИСЬ",
            font=("Arial", 18, "bold"),
            command=self.add_employee,
            fg_color=BUTTON_BG_COLOR,
            text_color="#0057FC",
            border_width=2,
            border_color="#0057FC",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=220,
            height=40,
            image=load_icon("plus.png", size=(20, 20)),
            compound="left"
        )
        self.add_button.place(x=27, y=139)

        # --- Кнопка "Редактировать" ---
        self.edit_button = ctk.CTkButton(
            self,
            text="  ИЗМЕНИТЬ",
            font=("Arial", 18, "bold"),
            command=self.edit_employee,
            fg_color=BUTTON_BG_COLOR,
            text_color="#FF8C00",
            border_width=2,
            border_color="#FF8C00",
            hover_color="#FFB347",
            corner_radius=12,
            width=180,
            height=40,
            image=load_icon("edit.png", size=(20, 20)),
            compound="left"
        )
        self.edit_button.place(x=27 + 220 + 27 + 150 + 20, y=139)

        # --- Кнопка "Удалить" ---
        self.delete_button = ctk.CTkButton(
            self,
            text="  УДАЛИТЬ",
            font=("Arial", 18, "bold"),
            command=self.delete_employee,
            fg_color=BUTTON_BG_COLOR,
            text_color="#FF4136",
            border_width=2,
            border_color="#FF4136",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=150,
            height=40,
            image=load_icon("cross.png", size=(20, 20)),
            compound="left"
        )
        self.delete_button.place(x=27 + 220 + 27, y=139)

        # --- Поле поиска ---
        search_entry_width = 257
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search...",
            width=search_entry_width,
            height=40,
            font=DEFAULT_FONT,
            text_color=LABEL_TEXT_COLOR,
            placeholder_text_color="gray",
            fg_color="white"
        )
        self.search_entry.place(x=27 + 220 + 27 + 150 + 20 + 180 + 20, y=139)
        self.search_entry.bind("<KeyRelease>", self.search)

        # --- Таблица ---
        self.table_wrapper = ctk.CTkFrame(self, fg_color="white")
        self.table_wrapper.place(x=27, y=195)
        self.table = Sheet(
            self.table_wrapper,
            width=1136,
            height=450,
        )
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self.table.headers(
            ["Таб. номер", "Фамилия", "Имя", "Отчество", "Дата рожд.", "Пол", "Должность", "Отдел", "Состояние"])

        self.table.enable_bindings(("single_select",
                                    "row_select",
                                    "column_width_resize",
                                    "arrowkeys",
                                    "row_height_resize",
                                    "copy",
                                    "cut",
                                    "paste",
                                    "delete",
                                    "undo",
                                    "redo",
                                    "rc_select",
                                    "rc_insert_row",
                                    "rc_delete_row",
                                    "rc_insert_column",
                                    "rc_delete_column",
                                    "hide_rows",
                                    "hide_columns",
                                    "edit_cell"
                                    ))
        # --- Пагинация ---
        self.pagination_frame = ctk.CTkFrame(
            self.table_wrapper, fg_color="transparent")
        self.pagination_frame.pack(
            side="bottom", fill="x", padx=10, pady=(0, 10))

        self.prev_button = ctk.CTkButton(
            self.pagination_frame,
            text="<",
            font=DEFAULT_FONT,
            command=self.prev_page,
            width=30,
            height=30,
            fg_color="#E9ECEF",
            hover_color=BUTTON_HOVER_COLOR,
            text_color="#000000",
            border_width=0,
            border_color="#CED4DA",
            state="disabled"
        )
        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text=">",
            font=DEFAULT_FONT,
            command=self.next_page,
            width=30,
            height=30,
            fg_color=BUTTON_BG_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color="#000000",
            border_width=1,
            border_color="#CED4DA",
        )

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Страница 1",
            font=("Arial", 16, "bold"),
            text_color="#000000"
        )
        #  Размещение
        self.prev_button.pack(side="left", padx=(0, 5))
        self.page_label.pack(side="left", padx=5)
        self.next_button.pack(side="left", padx=(5, 0))

        log.debug("Виджеты EmployeesFrame созданы")

    # --- Методы для работы с данными и отображением ---

    def add_employee(self):
        """
        Открывает диалог добавления нового сотрудника.
        """
        log.info("Открытие диалога добавления сотрудника")
        dialog = AddEmployeeDialog(self, self.db)
        dialog.wait_window()
        self.load_data()
        self.display_data()

    def edit_employee(self):
        """
        Открывает диалог редактирования сотрудника.
        """
        log.info("Открытие диалога редактирования сотрудника")
        selected_row = self.table.get_selected_rows()
        if not selected_row:
            messagebox.showerror(
                "Ошибка", "Выберите сотрудника для редактирования!")
            log.warning("Попытка редактирования без выбора сотрудника")  # !!!
            return

        selected_row_index = list(selected_row)[0]
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        employee_data = self.db.get_employee_by_personnel_number(
            personnel_number)
        if employee_data is None:
            messagebox.showerror(
                "Ошибка", "Не удалось получить данные о сотруднике!")
            log.error(
                f"Не удалось получить данные сотрудника с табельным номером {personnel_number}")  # !!!
            return

        dialog = EditEmployeeDialog(self, self.db, employee_data)
        dialog.wait_window()
        self.load_data()
        self.display_data()

    def delete_employee(self):
        """
        Удаляет выбранного сотрудника.
        """
        log.info("Попытка удаления сотрудника")   # !!!
        selected_row = self.table.get_selected_rows()

        if not selected_row:
            messagebox.showerror("Ошибка", "Выберите сотрудника для удаления!")
            log.warning("Попытка удаления без выбора сотрудника")  # !!!
            return

        selected_row_index = list(selected_row)[0]
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить сотрудника с табельным номером {personnel_number}?"):
            if self.db.delete_employee(personnel_number):
                messagebox.showinfo("Успех", "Сотрудник удален.")
                log.info(
                    f"Сотрудник с табельным номером {personnel_number} удален")  # !!!
                self.load_data()
                self.display_data()
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось удалить сотрудника.")
                log.error(
                    f"Не удалось удалить сотрудника с табельным номером {personnel_number}")   # !!!

    def prev_page(self):
        """
        Переходит на предыдущую страницу.
        """
        if self.current_page > 1:
            self.current_page -= 1
            log.debug(
                f"Переход на предыдущую страницу: {self.current_page}")    # !!!
            self.display_data()

    def next_page(self):
        """
        Переходит на следующую страницу.
        """
        if self.current_page < (self.total_rows + self.rows_per_page - 1) // self.rows_per_page:
            self.current_page += 1
            log.debug(
                f"Переход на следующую страницу: {self.current_page}")  # !!!
            self.display_data()

    def update_page_label(self):
        """
        Обновляет метку с номером текущей страницы.
        """
        self.page_label.configure(text=f"Страница {self.current_page}")

    def update_buttons_state(self):
        """
        Обновляет состояние кнопок пагинации (включены/выключены).
        """
        if self.current_page == 1:
            self.prev_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.prev_button.configure(
                state="normal", border_width=1, fg_color="transparent")

        if self.current_page == (self.total_rows + self.rows_per_page - 1) // self.rows_per_page:
            self.next_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.next_button.configure(
                state="normal", border_width=1, fg_color="transparent")

    def load_data(self):
        """
        Загружает данные из базы данных.
        """
        log.debug("Загрузка данных для EmployeesFrame")   # !!!
        self.all_data, self.total_rows = self.db.get_employees()
        if self.all_data is None:
            log.warning("get_employees вернул None")   # !!!
            self.all_data = []
            self.total_rows = 0

    def search(self, event):
        """
        Выполняет поиск по данным таблицы.

        Args:
            event: Событие (нажатие клавиши в поле поиска).
        """
        search_term = self.search_entry.get().lower()
        log.debug(f"Поиск: {search_term}")  # !!!
        self.current_page = 1
        self.display_data(search_term)

    def display_data(self, search_term=None):
        """
        Отображает данные в таблице с учетом пагинации и поиска.

        Args:
            search_term (str, optional): Строка поиска.
        """
        log.debug(
            f"Отображение данных с параметром поиска: {search_term}")  # !!!
        if search_term:
            filtered_data = []
            for row in self.all_data:
                if any(search_term in str(value).lower() for value in row):
                    filtered_data.append(row)
            self.total_rows = len(filtered_data)
        else:
            filtered_data = self.all_data
            self.total_rows = len(self.all_data)

        self.data = filtered_data
        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        current_page_data = self.data[start_index:end_index]

        old_data = self.table.get_sheet_data()

        if self.table.total_rows() > 0:
            self.table.set_sheet_data([[None for _ in range(
                len(self.table.headers()))] for _ in range(self.table.total_rows())])

        if current_page_data != old_data:
            self.table.set_sheet_data(current_page_data)
            self.table.set_column_widths(
                [100, 150, 100, 150, 120, 100, 180, 150, 100])

        self.table.refresh()
        self.update_page_label()
        self.update_buttons_state()

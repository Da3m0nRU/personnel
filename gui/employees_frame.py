# gui/employees_frame.py
import customtkinter as ctk
from config import *
from tksheet import Sheet
from .utils import load_icon
from .dialogs.add_employee_dialog import AddEmployeeDialog
from .dialogs.edit_employee_dialog import EditEmployeeDialog
from .dialogs.import_dialog import ImportDialog  # Импорт диалога импорта
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
import os
import datetime
import codecs


log = logging.getLogger(__name__)


class EmployeesFrame(ctk.CTkFrame):
    """
    Вкладка "Сотрудники".

    Отображает список сотрудников, позволяет добавлять, редактировать и удалять записи,
    а также импортировать и экспортировать данные.
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
        self.display_data()  # Вызываем display_data, чтобы установить начальные значения
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

        # --- Кнопка "Импорт" ---
        self.import_button = ctk.CTkButton(
            self,
            text="  ИМПОРТ",
            font=("Arial", 18, "bold"),
            command=self.import_data,
            fg_color=BUTTON_BG_COLOR,
            text_color="#4CAF50",
            border_width=2,
            border_color="#4CAF50",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=220,
            height=40,
            image=load_icon("import.png", size=(20, 20)),
            compound="left"
        )
        self.import_button.place(x=27, y=139 + 40 + 20)

        # --- Кнопка "Экспорт" ---
        self.export_button = ctk.CTkButton(
            self,
            text="  ЭКСПОРТ",
            font=("Arial", 18, "bold"),
            command=self.export_data,
            fg_color=BUTTON_BG_COLOR,
            text_color="#2196F3",
            border_width=2,
            border_color="#2196F3",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=180,
            height=40,
            image=load_icon("export.png", size=(20, 20)),
            compound="left"
        )
        self.export_button.place(x=27 + 220 + 27 + 150 + 20, y=139 + 40 + 20)

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
        self.table_wrapper.place(x=27, y=195 + 40 + 27)
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
            state="disabled"  # Начальное состояние
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
            state="disabled"  # Начальное состояние
        )

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Страница 1 / 1",  # Начальный текст
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
        """Открывает диалог добавления нового сотрудника."""
        log.info("Открытие диалога добавления сотрудника")
        dialog = AddEmployeeDialog(self, self.db)
        dialog.wait_window()
        self.load_data()
        self.display_data()

    def edit_employee(self):
        """Открывает диалог редактирования сотрудника."""
        log.info("Открытие диалога редактирования сотрудника")
        selected_row = self.table.get_selected_rows()
        if not selected_row:
            messagebox.showerror(
                "Ошибка", "Выберите сотрудника для редактирования!")
            log.warning("Попытка редактирования без выбора сотрудника")
            return

        selected_row_index = list(selected_row)[0]
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        employee_data = self.db.get_employee_by_personnel_number(
            personnel_number)
        if employee_data is None:
            messagebox.showerror(
                "Ошибка", "Не удалось получить данные о сотруднике!")
            log.error(
                f"Не удалось получить данные сотрудника с табельным номером {personnel_number}")
            return

        dialog = EditEmployeeDialog(self, self.db, employee_data)
        dialog.wait_window()
        self.load_data()
        self.display_data()

    def delete_employee(self):
        """Удаляет выбранного сотрудника."""
        log.info("Попытка удаления сотрудника")
        selected_row = self.table.get_selected_rows()

        if not selected_row:
            messagebox.showerror("Ошибка", "Выберите сотрудника для удаления!")
            log.warning("Попытка удаления без выбора сотрудника")
            return

        selected_row_index = list(selected_row)[0]
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        if messagebox.askyesno("Подтверждение",
                               f"Вы уверены, что хотите удалить сотрудника с табельным номером {personnel_number}?"):
            if self.db.delete_employee(personnel_number):
                messagebox.showinfo("Успех", "Сотрудник удален.")
                log.info(
                    f"Сотрудник с табельным номером {personnel_number} удален")
                self.load_data()
                self.display_data()  # Обновляем после удаления
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось удалить сотрудника.")
                log.error(
                    f"Не удалось удалить сотрудника с табельным номером {personnel_number}")

    def prev_page(self):
        """Переходит на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            log.debug(f"Переход на предыдущую страницу: {self.current_page}")
            self.display_data()  # Обновляем данные и интерфейс

    def next_page(self):
        """Переходит на следующую страницу."""
        if self.current_page < self.get_total_pages():  # Исправлено!
            self.current_page += 1
            log.debug(f"Переход на следующую страницу: {self.current_page}")
            self.display_data()  # Обновляем данные и интерфейс

    def update_page_label(self):
        """Обновляет метку с номером текущей страницы и общим количеством страниц."""
        total_pages = self.get_total_pages()  # Получаем общее количество страниц
        self.page_label.configure(
            text=f"Страница {self.current_page} / {total_pages}")

    def get_total_pages(self):
        """Вычисляет и возвращает общее количество страниц."""
        return (self.total_rows + self.rows_per_page - 1) // self.rows_per_page

    def update_buttons_state(self):
        """Обновляет состояние кнопок пагинации (включены/выключены)."""
        if self.current_page == 1:
            self.prev_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.prev_button.configure(
                state="normal", border_width=1, fg_color="transparent")

        if self.current_page >= self.get_total_pages():  # Исправлено!
            self.next_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.next_button.configure(
                state="normal", border_width=1, fg_color="transparent")

    def load_data(self):
        """Загружает данные из базы данных (с учетом поиска)."""
        log.debug("Загрузка данных для EmployeesFrame")
        search_term = self.search_entry.get()  # Получаем текст поиска
        self.all_data, self.total_rows = self.db.get_employees(
            search_term=search_term)  # Передаем search_term
        if self.all_data is None:  # Проверяем на None
            log.warning("get_employees вернул None")
            self.all_data = []
            self.total_rows = 0

    def search(self, event):
        """Выполняет поиск по данным таблицы."""
        search_term = self.search_entry.get().lower()  # Получаем текст поиска
        log.debug(f"Поиск: {search_term}")
        self.current_page = 1  # Сбрасываем на первую страницу при новом поиске
        self.display_data()  # Передаем search_term

    def display_data(self, search_term=None):
        """
        Отображает данные в таблице с учетом пагинации и поиска.
        """
        log.debug(f"Отображение данных с параметром поиска: {search_term}")

        # Если есть параметр поиска, используем его. Иначе берем из self.search_entry
        search_term = search_term if search_term is not None else self.search_entry.get().lower()

        # Загружаем данные с учетом поиска и текущей страницы
        self.data, self.total_rows = self.db.get_employees(
            page=self.current_page, per_page=self.rows_per_page, search_term=search_term)

        if self.data is None:
            log.warning("get_employees (в display_data) вернул None")
            self.data = []  # Если ошибка, отображаем пустую таблицу
            self.total_rows = 0

        # Очищаем таблицу
        if self.table.total_rows() > 0:
            self.table.set_sheet_data([[None for _ in range(len(self.table.headers()))] for _ in range(
                self.table.total_rows())], redraw=False)  # Очищаем, но пока не перерисовываем
        # Заполняем данными
        if self.data:
            self.table.set_sheet_data(self.data)

        self.table.set_column_widths(
            [100, 150, 100, 150, 120, 100, 180, 150, 100])
        self.table.refresh()  # Перерисовываем
        self.update_page_label()  # Обновляем номер страницы
        self.update_buttons_state()  # Обновляем состояние кнопок

    def import_data(self):
        """
        Обработчик нажатия на кнопку "Импорт". Открывает диалог импорта.
        """
        log.info("Открытие диалога импорта")
        dialog = ImportDialog(self, self.db)
        dialog.wait_window()
        self.load_data()
        self.display_data()  # Обновляем после импорта

    def export_data(self):
        """
        Экспортирует данные о сотрудниках в форматы CSV и XML.
        """
        log.info("Экспорт данных о сотрудниках")

        # 1. Получаем данные (все, без пагинации и фильтров)
        data, _ = self.db.get_employees(page=1, per_page=999999)
        if not data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            log.info("Нет данных для экспорта")
            return

        # 2. Создаем папку export/дата
        export_dir = "export"
        now = datetime.datetime.now()
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(date_dir, exist_ok=True)  # Создаем, если нет

        # 3. Формируем имена файлов с датой и временем
        timestamp = now.strftime("%H-%M-%S")  # Часы-минуты-секунды
        csv_filename = os.path.join(date_dir, f"employees_{timestamp}.csv")
        xml_filename = os.path.join(date_dir, f"employees_{timestamp}.xml")

        # --- Экспорт в CSV ---
        try:
            # Добавляем BOM (UTF-8 with BOM)
            with codecs.open(csv_filename, "w", "utf-8-sig") as csvfile:  # Изменено здесь
                # Заголовки столбцов (из структуры БД)
                fieldnames = [
                    "PersonnelNumber", "LastName", "FirstName", "MiddleName",
                    "BirthDate", "GenderName", "PositionName", "DepartmentName", "StateName"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in data:
                    # Преобразуем кортеж в словарь
                    row_dict = {
                        "PersonnelNumber": row[0],
                        "LastName": row[1],
                        "FirstName": row[2],
                        "MiddleName": row[3],
                        "BirthDate": row[4],
                        "GenderName": row[5],
                        "PositionName": row[6],
                        "DepartmentName": row[7],
                        "StateName": row[8]
                    }
                    writer.writerow(row_dict)
            log.info(f"Данные экспортированы в CSV: {csv_filename}")  # !!!
        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в CSV: {e}")
            log.exception(f"Ошибка при экспорте в CSV: {e}")  # !!!
            return

        # --- Экспорт в XML ---
        try:
            root = ET.Element("Employees")
            for row in data:
                employee = ET.SubElement(root, "Employee")
                ET.SubElement(employee, "PersonnelNumber").text = str(row[0])
                ET.SubElement(employee, "LastName").text = row[1]
                ET.SubElement(employee, "FirstName").text = row[2]
                ET.SubElement(
                    employee, "MiddleName").text = row[3] if row[3] else ""
                ET.SubElement(employee, "BirthDate").text = row[4]
                ET.SubElement(employee, "GenderName").text = row[5]
                ET.SubElement(employee, "PositionName").text = row[6]
                ET.SubElement(employee, "DepartmentName").text = row[7]
                ET.SubElement(employee, "StateName").text = row[8]

            tree = ET.ElementTree(root)
            ET.indent(tree, "  ")
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Данные экспортированы в XML: {xml_filename}")

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в XML: {e}")
            log.exception(f"Ошибка при экспорте в XML: {e}")
            return

        messagebox.showinfo(
            "Экспорт", f"Данные успешно экспортированы в:\n{csv_filename}\n{xml_filename}")

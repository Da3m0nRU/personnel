# gui/employees_frame.py

import customtkinter as ctk
from config import *
from .utils import load_icon  # load_icon
# !!! Sheet больше не импортируется здесь!
from .dialogs.add_employee_dialog import AddEmployeeDialog
from .dialogs.edit_employee_dialog import EditEmployeeDialog
from .dialogs.import_dialog import ImportDialog
from db.employee_repository import EmployeeRepository
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
import os
import datetime
import codecs

# !!! Импортируем базовый класс
from .base_table_frame import BaseTableFrame

log = logging.getLogger(__name__)

# !!! Наследуемся от BaseTableFrame


class EmployeesFrame(BaseTableFrame):

    def __init__(self, master, db):
        super().__init__(master, db)  # Вызываем конструктор BaseTableFrame
        self.repository = EmployeeRepository(db)  # !!! Создаем репозиторий
        self.create_widgets()  # !!!
        self.load_data()       # !!!
        self.display_data()   # !!!

    def create_widgets(self):
        """
        Создает виджеты, специфичные для EmployeesFrame.
        """
        log.debug("Создание виджетов для EmployeesFrame")

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
            text_color="#FF8C00",  # Оранжевый
            border_width=2,
            border_color="#FF8C00",
            hover_color="#FFB347",  # Светлее при наведении
            corner_radius=12,
            width=180,  # Ширина по тексту
            height=40,
            image=load_icon("edit.png", size=(20, 20)),  # Другая иконка
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
            text_color="#FF4136",  # Красный
            border_width=2,
            border_color="#FF4136",
            hover_color=BUTTON_HOVER_COLOR,  # Тот же, что и у других
            corner_radius=12,
            width=150,  # Ширина по тексту
            height=40,
            image=load_icon("cross.png", size=(20, 20)),  # Другая иконка
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
            font=DEFAULT_FONT,  # шрифт из конфига
            text_color=LABEL_TEXT_COLOR,  # из конфига
            placeholder_text_color="gray",
            fg_color="white"  # Белый фон
        )
        self.search_entry.place(
            x=27 + 220 + 27 + 150 + 20 + 180 + 20, y=139)  # Размещение
        self.search_entry.bind("<KeyRelease>", self.search)
        # !!! Создаем виджеты таблицы !!!
        self.create_table_widgets()
        # !!!  Заголовки
        self.table.headers(["Таб. номер", "Фамилия", "Имя", "Отчество", "Дата рожд.",
                            "Пол", "Должность", "Отдел", "Состояние"])
        log.debug("Виджеты EmployeesFrame созданы")

    def load_data(self, search_term=None):
        """Загружает данные о сотрудниках из базы данных."""
        log.debug("Загрузка данных для EmployeesFrame")
        if search_term is None:
            search_term = self.search_entry.get()
        #  Используем метод get_employees из *репозитория* (пока это self.repository).
        self.all_data, self.total_rows = self.repository.get_employees(
            search_term=search_term)
        if self.all_data is None:
            log.warning("get_employees вернул None")
            self.all_data = []
            self.total_rows = 0

    def display_data(self, search_term=None):
        """Отображает данные."""
        log.debug(f"Отображение данных")

        if not self.all_data:  # Если данных нет, загружаем
            self.load_data()

        if search_term := self.search_entry.get().lower():  # Фильтрация
            filtered_data = []
            for row in self.all_data:
                if any(search_term in str(value).lower() for value in row):  # !!!
                    filtered_data.append(row)
            self.data = filtered_data  # filtered_data в self.data.
            self.total_rows = len(filtered_data)
        else:
            self.data = self.all_data  # Используем self.all_data.
            self.total_rows = len(self.all_data)

        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        current_page_data = self.data[start_index:end_index]
        if self.table.total_rows() > 0:
            self.table.set_sheet_data([[None for _ in range(len(
                self.table.headers()))] for _ in range(self.table.total_rows())], redraw=False)

        if current_page_data:  # Если данные есть
            self.table.set_sheet_data(current_page_data)
        self.table.refresh()
        self.update_page_label()
        self.update_buttons_state()
    # --- Методы, специфичные ИМЕННО для EmployeesFrame ---

    def add_employee(self):
        """Открывает диалог добавления нового сотрудника."""
        log.info("Открытие диалога добавления сотрудника")
        dialog = AddEmployeeDialog(self, self.repository)
        dialog.wait_window()  # Ждём
        self.load_data()    #
        self.display_data()  # после закрытия

    def edit_employee(self):
        """Открывает диалог редактирования сотрудника."""
        log.info("Открытие диалога редактирования сотрудника")
        selected_row = self.table.get_selected_rows()  # Получаем
        if not selected_row:
            messagebox.showerror(
                "Ошибка", "Выберите сотрудника для редактирования!")
            log.warning("Попытка редактирования без выбора сотрудника")
            return

        selected_row_index = list(selected_row)[0]
        personnel_number = self.table.get_cell_data(selected_row_index, 0)
        employee_data = self.repository.get_employee_by_personnel_number(
            personnel_number)

        if employee_data is None:
            messagebox.showerror(
                "Ошибка", "Не удалось получить данные о сотруднике!")
            log.error(
                f"Не удалось получить данные сотрудника с табельным номером {personnel_number}")
            return

        dialog = EditEmployeeDialog(
            self, self.repository, employee_data)  # Передаем данные в
        dialog.wait_window()  # Ждем
        self.load_data()          # Обновляем
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
            if self.repository.delete_employee(personnel_number):
                messagebox.showinfo("Успех", "Сотрудник удален.")
                log.info(
                    f"Сотрудник с табельным номером {personnel_number} удален")
                self.load_data()
                self.display_data()
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось удалить сотрудника.")
                log.error(
                    f"Не удалось удалить сотрудника с табельным номером {personnel_number}")

    def search(self, event):
        self.load_data()
        self.display_data()

    def import_data(self):
        """Открытие диалога импорта"""
        log.info("Открытие диалога импорта")
        dialog = ImportDialog(self, self.repository)
        dialog.wait_window()
        self.load_data()
        self.display_data()  # После импорта

    def export_data(self):
        """Экспортирует данные в CSV и XML."""
        log.info("Экспорт данных о сотрудниках")

        data, _ = self.repository.get_employees()
        if not data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            log.info("Нет данных для экспорта")  # !!!
            return
        export_dir = "export"  # Путь
        now = datetime.datetime.now()
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(date_dir, exist_ok=True)
        timestamp = now.strftime("%H-%M-%S")  #
        csv_filename = os.path.join(date_dir, f"employees_{timestamp}.csv")
        xml_filename = os.path.join(date_dir, f"employees_{timestamp}.xml")

        # --- Экспорт в CSV ---
        try:
            with codecs.open(csv_filename, "w", "utf-8-sig") as csvfile:  # BOM
                #  Заголовки столбцов
                fieldnames = [
                    "PersonnelNumber", "LastName", "FirstName", "MiddleName",
                    "BirthDate", "GenderName", "PositionName", "DepartmentName", "StateName"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    #  Преобразуем в словарь
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
            log.info(f"Данные экспортированы в CSV: {csv_filename}")

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в CSV: {e}")
            log.exception(f"Ошибка при экспорте в CSV: {e}")
            return

        # --- Экспорт в XML ---
        try:
            root = ET.Element("Employees")
            for row in data:  # Перебираем
                employee = ET.SubElement(root, "Employee")
                ET.SubElement(employee, "PersonnelNumber").text = str(row[0])
                ET.SubElement(employee, "LastName").text = row[1]
                ET.SubElement(employee, "FirstName").text = row[2]
                ET.SubElement(
                    employee, "MiddleName").text = row[3] if row[3] else ""  # !!!
                ET.SubElement(employee, "BirthDate").text = row[4]          #
                ET.SubElement(employee, "GenderName").text = row[5]          #
                ET.SubElement(employee, "PositionName").text = row[6]   #
                ET.SubElement(employee, "DepartmentName").text = row[7]
                ET.SubElement(employee, "StateName").text = row[8]    #

            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Данные экспортированы в XML: {xml_filename}")

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в XML: {e}")
            log.exception(f"Ошибка при экспорте в XML: {e}")
            return

        messagebox.showinfo("Экспорт",
                            f"Данные успешно экспортированы в:\n{csv_filename}\n{xml_filename}")

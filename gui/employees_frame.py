# gui/employees_frame.py
import customtkinter as ctk
from config import *
from tksheet import Sheet
from .utils import load_icon
from .dialogs.add_employee_dialog import AddEmployeeDialog
from .dialogs.edit_employee_dialog import EditEmployeeDialog
from .dialogs.import_dialog import ImportDialog
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
import os
import datetime
import codecs

log = logging.getLogger(__name__)


class EmployeesFrame(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        self.current_page = 1
        self.rows_per_page = 10
        self.total_rows = 0  # Общее количество записей (с учетом поиска)
        self.all_data = []
        self.data = []  # Данные для текущей страницы (после фильтрации)
        self.create_widgets()
        self.load_data()       # Загружаем данные (с учетом поиска)
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
            text_color="#4CAF50",  # Зеленый цвет
            border_width=2,
            border_color="#4CAF50",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=220,
            height=40,
            image=load_icon("import.png", size=(20, 20)),
            compound="left"
        )
        # Под кнопкой "Добавить"
        self.import_button.place(x=27, y=139 + 40 + 20)

        # --- Кнопка "Экспорт" ---
        self.export_button = ctk.CTkButton(
            self,
            text="  ЭКСПОРТ",
            font=("Arial", 18, "bold"),
            command=self.export_data,
            fg_color=BUTTON_BG_COLOR,
            text_color="#2196F3",  # Синий цвет
            border_width=2,
            border_color="#2196F3",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=180,
            height=40,
            image=load_icon("export.png", size=(20, 20)),
            compound="left"
        )
        # Под кнопкой "Удалить"
        self.export_button.place(x=27 + 220 + 27 + 150 + 20, y=139 + 40 + 20)

        # --- Поле поиска ---
        search_entry_width = 257  # переменная
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
        self.search_entry.bind("<KeyRelease>", self.search)  # Привязка поиска

        # --- Таблица (Sheet) ---
        self.table_wrapper = ctk.CTkFrame(self, fg_color="white")  # Рамка
        # Размещение под кнопками
        self.table_wrapper.place(x=27, y=195 + 40 + 27)
        self.table = Sheet(self.table_wrapper,
                           width=1220,
                           height=450,
                           font=TABLE_FONT,  # !!!
                           header_font=TABLE_HEADER_FONT
                           )  # Размеры

        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        #  Заголовки столбцов
        self.table.headers(["Таб. номер", "Фамилия", "Имя", "Отчество",
                            "Дата рожд.", "Пол", "Должность", "Отдел", "Состояние"])

        #  Включаем/отключаем привязки событий
        self.table.enable_bindings(("single_select",
                                    "row_select",
                                    "column_width_resize",
                                    "arrowkeys",
                                    "copy",  # Копирование
                                    "paste",  # Вставка
                                    "delete",
                                    "edit_cell",
                                    "rc_select"  # Добавили
                                    ))
        self.table.disable_bindings("row_height_resize", "cut", "undo", "redo",
                                    "rc_insert_row", "rc_delete_row",
                                    "rc_insert_column", "rc_delete_column",
                                    "hide_rows", "hide_columns"
                                    )

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
            border_width=0,  # Убрал рамку
            border_color="#CED4DA",  # Серый цвет
            state="disabled"
        )
        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text=">",
            font=DEFAULT_FONT,
            command=self.next_page,
            width=30,
            height=30,
            fg_color=BUTTON_BG_COLOR,  # Белый фон
            hover_color=BUTTON_HOVER_COLOR,  # Тот же, что у других
            text_color="#000000",  # Черный
            border_width=1,      # Тонкая рамка
            border_color="#CED4DA",   # Серый
            state="disabled"  # По умолчанию выключена
        )

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Страница 1 / 1",
                                       font=("Arial", 16, "bold"),
                                       text_color="#000000")  # Черный
        #  Размещение
        self.prev_button.pack(side="left", padx=(0, 5))
        self.page_label.pack(side="left", padx=5)
        self.next_button.pack(side="left", padx=(5, 0))
        log.debug("Виджеты EmployeesFrame созданы")
    # Методы работы с данными:

    def add_employee(self):
        """Открывает диалог добавления нового сотрудника."""
        log.info("Открытие диалога добавления сотрудника")
        dialog = AddEmployeeDialog(self, self.db)
        dialog.wait_window()
        self.load_data()    # Обновляем данные.
        self.display_data()  # после закрытия

    def edit_employee(self):
        """Открывает диалог редактирования сотрудника."""
        log.info("Открытие диалога редактирования сотрудника")
        # Получаем *индексы* выделенных строк.
        selected_row = self.table.get_selected_rows()
        if not selected_row:
            messagebox.showerror(
                "Ошибка", "Выберите сотрудника для редактирования!")
            log.warning("Попытка редактирования без выбора сотрудника")
            return
        #  !!! tksheet возвращает генератор, поэтому нужен list
        selected_row_index = list(selected_row)[0]
        # Получаем табельный номер.
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        employee_data = self.db.get_employee_by_personnel_number(
            personnel_number)
        if employee_data is None:
            messagebox.showerror(
                "Ошибка", "Не удалось получить данные о сотруднике!")
            log.error(
                f"Не удалось получить данные сотрудника с табельным номером {personnel_number}")
            return

        # Передаем данные в диалог.
        dialog = EditEmployeeDialog(self, self.db, employee_data)
        dialog.wait_window()  # Ждем закрытия
        self.load_data()          # Обновляем данные.
        self.display_data()  # Отображаем

    def delete_employee(self):
        """Удаляет выбранного сотрудника."""
        log.info("Попытка удаления сотрудника")
        # Получаем индексы выделенных строк.
        selected_row = self.table.get_selected_rows()

        if not selected_row:  # Проверяем, выбрана ли строка.
            messagebox.showerror("Ошибка", "Выберите сотрудника для удаления!")
            log.warning("Попытка удаления без выбора сотрудника")
            return

        # !!! tksheet возвращает генератор
        selected_row_index = list(selected_row)[0]
        # Получаем табельный номер.
        personnel_number = self.table.get_cell_data(selected_row_index, 0)

        if messagebox.askyesno("Подтверждение",
                               f"Вы уверены, что хотите удалить сотрудника с табельным номером {personnel_number}?"):
            if self.db.delete_employee(personnel_number):
                messagebox.showinfo("Успех", "Сотрудник удален.")
                log.info(
                    f"Сотрудник с табельным номером {personnel_number} удален")  # !!!
                self.load_data()          # Обновляем данные
                self.display_data()       # и отображение.
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
            self.display_data()

    def update_page_label(self):
        """Обновляет метку с номером текущей/общее количество."""
        total_pages = self.get_total_pages()  # Получаем
        #  Если 0 страниц
        if total_pages == 0:
            self.page_label.configure(text="Страница 1 / 1")
        else:
            self.page_label.configure(
                text=f"Страница {self.current_page} / {total_pages}")  # Обновляем

    def get_total_pages(self):
        """Вычисляет общее количество страниц."""
        return (self.total_rows + self.rows_per_page - 1) // self.rows_per_page

    def update_buttons_state(self):
        """Обновляет состояние кнопок пагинации (включены/выключены)."""
        if self.current_page == 1:
            self.prev_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")  # Стиль
        else:
            self.prev_button.configure(
                state="normal", border_width=1, fg_color="transparent")

        #  Если  >= , значит последняя, лог в else
        if self.current_page >= self.get_total_pages():
            self.next_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.next_button.configure(
                state="normal", border_width=1, fg_color="transparent")

    def load_data(self):
        """Загружает данные из базы данных (с учетом поиска)."""
        log.debug("Загрузка данных для EmployeesFrame")
        #  search_term берем из search_entry (поля в self)
        search_term = self.search_entry.get()
        #  Вызываем get_employees, передавая search_term. page и per_page  НЕ передаём
        self.all_data, self.total_rows = self.db.get_employees(
            search_term=search_term)  #
        if self.all_data is None:  # Проверяем
            log.warning("get_employees вернул None")   # !!!
            self.all_data = []  # Пустой список
            self.total_rows = 0

    def search(self, event):
        # search не нужен

        self.load_data()  # Загружаем данные,
        self.display_data()
        # self.current_page = 1 #, сброс

    def display_data(self, search_term=None):
        """Отображает данные в таблице с учетом пагинации."""
        log.debug(f"Отображение данных")
        #  search_term больше не нужен
        #  Данные, если есть, в all data.
        if not self.all_data:
            self.load_data()

        #  Фильтрация.
        if search_term := self.search_entry.get().lower():  # := (морж)
            filtered_data = []
            for row in self.all_data:
                #  Проверяем вхождение search_term в ЛЮБОЕ значение строки.
                if any(search_term in str(value).lower() for value in row):
                    filtered_data.append(row)
            self.data = filtered_data  # filtered_data в self.data.
            self.total_rows = len(filtered_data)
        else:
            self.data = self.all_data  # Используем self.all_data.
            self.total_rows = len(self.all_data)
            # total rows = len(filtered_data)

        start_index = (self.current_page - 1) * self.rows_per_page  # пагинация
        end_index = start_index + self.rows_per_page
        current_page_data = self.data[start_index:end_index]
        #  Очищаем таблицу.
        if self.table.total_rows() > 0:
            self.table.set_sheet_data([[None for _ in range(len(
                self.table.headers()))] for _ in range(self.table.total_rows())], redraw=False)
        # Заполняем данными.
        if current_page_data:  # Если данные есть
            # Отображаем данные текущей страницы.
            self.table.set_sheet_data(current_page_data)

        self.table.set_column_widths(
            [100, 150, 100, 150, 120, 100, 180, 150, 100])
        self.table.refresh()
        self.update_page_label()  # Обновляем
        self.update_buttons_state()  # Обновляем

    def import_data(self):
        """Открытие диалога импорта"""
        log.info("Открытие диалога импорта")  # !!!
        dialog = ImportDialog(self, self.db)
        dialog.wait_window()
        self.load_data()
        self.display_data()  # После импорта

    def export_data(self):
        """Экспортирует данные в CSV и XML."""
        log.info("Экспорт данных о сотрудниках")
        # Получаем *все* данные, без пагинации.
        data, _ = self.db.get_employees()
        if not data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            log.info("Нет данных для экспорта")  # !!!
            return
        #  Создание папки export/дата.
        export_dir = "export"  # Путь
        now = datetime.datetime.now()  # Текущее время
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))  # Папка
        os.makedirs(date_dir, exist_ok=True)  # Если нет - создать

        #  Имена файлов с датой и временем.
        timestamp = now.strftime("%H-%M-%S")  #
        csv_filename = os.path.join(
            date_dir, f"employees_{timestamp}.csv")  # Имя файла
        xml_filename = os.path.join(
            date_dir, f"employees_{timestamp}.xml")  # Имя файла

        # --- Экспорт в CSV ---
        try:
            with codecs.open(csv_filename, "w", encoding="utf-8-sig") as csvfile:  # BOM
                fieldnames = ["PersonnelNumber", "LastName", "FirstName", "MiddleName", "BirthDate",
                              "GenderName", "PositionName", "DepartmentName", "StateName"]  # Заголовки
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()  # Записываем заголовки
                for row in data:
                    # Преобразуем в словарь
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
                    writer.writerow(row_dict)  # Записываем строку
            log.info(f"Данные экспортированы в CSV: {csv_filename}")  # !!!

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в CSV: {e}")
            log.exception(f"Ошибка при экспорте в CSV: {e}")  # !!!
            return

        # --- Экспорт в XML ---
        try:

            root = ET.Element("Employees")  # Корневой
            for row in data:  # Перебираем
                employee = ET.SubElement(
                    root, "Employee")  # Создаем <Employee>
                ET.SubElement(employee, "PersonnelNumber").text = str(
                    row[0])  # Добавляем
                ET.SubElement(employee, "LastName").text = row[1]          #
                ET.SubElement(employee, "FirstName").text = row[2]          #
                ET.SubElement(
                    employee, "MiddleName").text = row[3] if row[3] else ""
                ET.SubElement(employee, "BirthDate").text = row[4]      #
                ET.SubElement(employee, "GenderName").text = row[5]       #
                ET.SubElement(employee, "PositionName").text = row[6]    #
                ET.SubElement(employee, "DepartmentName").text = row[7]
                ET.SubElement(employee, "StateName").text = row[8]     #

            tree = ET.ElementTree(root)  # Создаем
            ET.indent(tree, space="  ")  # Добавляем
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Данные экспортированы в XML: {xml_filename}")

        except Exception as e:  # Если ошибка,
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в XML: {e}")  # Сообщение
            log.exception(f"Ошибка при экспорте в XML: {e}")  # !!!
            return  #

        messagebox.showinfo("Экспорт",  # Сообщение
                            f"Данные успешно экспортированы в:\n{csv_filename}\n{xml_filename}")

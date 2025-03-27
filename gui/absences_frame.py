# gui/absences_frame.py
import customtkinter as ctk
from config import *
import logging
import os
import datetime
import codecs
import csv
import xml.etree.ElementTree as ET
from tkinter import messagebox

from .base_table_frame import BaseTableFrame
from db.absence_repository import AbsenceRepository
from .dialogs.add_absence_dialog import AddAbsenceDialog
# Импортируем диалог редактирования
from .dialogs.edit_absence_dialog import EditAbsenceDialog
from .dialogs.import_absences_dialog import ImportAbsencesDialog
from .utils import load_icon

log = logging.getLogger(__name__)


class AbsencesFrame(BaseTableFrame):
    """
    Фрейм для отображения и управления записями об отсутствиях сотрудников.
    Включает CRUD, импорт и экспорт.
    """
    ID_COLUMN_INDEX = 0  # Индекс колонки с ID в self.all_data

    def __init__(self, master, db):
        super().__init__(master, db, table_height=350)
        self.repository = AbsenceRepository(db)
        self.db = db
        self.create_widgets()
        self.load_data()
        self.display_data()
        # Скрываем колонку ID после первого отображения
        if hasattr(self, 'table') and self.table.winfo_exists() and self.table.get_total_columns() > 0:
            try:
                # Убедимся, что индексы видимых колонок соответствуют скрытию первой
                self.table.hide_columns(columns=[self.ID_COLUMN_INDEX])
                log.debug("Колонка ID в таблице отсутствий скрыта.")
            except Exception as e:
                log.error(f"Ошибка при попытке скрыть колонку ID: {e}")

    def create_widgets(self):
        """ Создает виджеты, включая кнопки управления. """
        log.debug(
            "Создание виджетов для AbsencesFrame (с полным CRUD + Import/Export)")

        # --- Заголовок ---
        title_label = ctk.CTkLabel(self, text="ОТСУТСТВИЯ", font=(
            "Arial", 46, "bold"), text_color=LABEL_TEXT_COLOR, anchor="w")
        title_label.place(x=27, y=40)

        # --- Ряд 1 Кнопок ---
        # Кнопка "Новая запись" (Add)
        self.add_button = ctk.CTkButton(
            self, text="  НОВАЯ ЗАПИСЬ", font=BOLD_FONT, command=self.add_absence, width=220, height=40,
            image=load_icon("plus.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#0057FC", border_width=2, border_color="#0057FC", hover_color=BUTTON_HOVER_COLOR
        )
        self.add_button.place(x=27, y=139)

        # Кнопка "Удалить" (Delete)
        delete_button_x = 27 + 220 + 27
        self.delete_button = ctk.CTkButton(
            self, text="  УДАЛИТЬ", font=BOLD_FONT, command=self.delete_absence, width=150, height=40,
            image=load_icon("cross.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#FF4136", border_width=2, border_color="#FF4136", hover_color=BUTTON_HOVER_COLOR
        )
        self.delete_button.place(x=delete_button_x, y=139)

        # Кнопка "Изменить" (Edit)
        edit_button_x = delete_button_x + 150 + 20
        self.edit_button = ctk.CTkButton(
            self, text="  ИЗМЕНИТЬ", font=BOLD_FONT, command=self.edit_absence, width=180, height=40,
            image=load_icon("edit.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#FF8C00", border_width=2, border_color="#FF8C00", hover_color="#FFB347"
        )
        self.edit_button.place(x=edit_button_x, y=139)

        # --- Ряд 2 Кнопок ---
        # Кнопка "Импорт"
        import_button_y = 139 + 40 + 20
        self.import_button = ctk.CTkButton(
            self, text="  ИМПОРТ", font=BOLD_FONT, command=self.import_absences, width=220, height=40,
            image=load_icon("import.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#4CAF50", border_width=2, border_color="#4CAF50", hover_color=BUTTON_HOVER_COLOR
        )
        self.import_button.place(x=27, y=import_button_y)

        # Кнопка "Экспорт"
        export_button_x = edit_button_x  # Выровнять с "Изменить"
        self.export_button = ctk.CTkButton(
            self, text="  ЭКСПОРТ", font=BOLD_FONT, command=self.export_data, width=180, height=40,
            image=load_icon("export.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#2196F3", border_width=2, border_color="#2196F3", hover_color=BUTTON_HOVER_COLOR
        )
        self.export_button.place(x=export_button_x, y=import_button_y)

        # --- Поле поиска ---
        search_entry_width = 257
        search_entry_x = export_button_x + 180 + 20
        search_entry_y = import_button_y  # На уровне второго ряда кнопок
        self.search_entry = ctk.CTkEntry(
            self, placeholder_text="Поиск отсутствий...", width=search_entry_width, height=40,
            font=DEFAULT_FONT, text_color=LABEL_TEXT_COLOR, placeholder_text_color="gray", fg_color="white"
        )
        self.search_entry.place(x=search_entry_x, y=search_entry_y)
        self.search_entry.bind("<KeyRelease>", self.search)

        # --- Таблица и пагинация ---
        self.create_table_widgets()
        table_wrapper_y = import_button_y + 40 + 27  # Под вторым рядом кнопок/поиска
        self.table_wrapper.place(x=27, y=table_wrapper_y)

        # Заголовки ВИДИМЫХ колонок
        self.visible_table_headers = [
            "Таб.№", "ФИО", "Дата", "Полный день", "Начало", "Окончание", "Причина"]
        self.table.headers(self.visible_table_headers)
        self.table.readonly(True)  # Редактирование только через диалог

        log.debug("Виджеты AbsencesFrame созданы (с кнопками CRUD и Import/Export)")

    def load_data(self, search_term=None):
        """ Загружает данные об отсутствиях, включая ID. """
        log.debug(f"Загрузка данных отсутствий (search_term: {search_term})")
        if search_term is None:
            search_term = self.search_entry.get().strip()
        # Данные приходят с ID в первом столбце
        self.all_data, self.total_rows = self.repository.get_absences(
            search_term=search_term)
        log.debug(
            f"AbsencesFrame.load_data: Загружено {self.total_rows} строк.")

    def display_data(self, search_term=None):
        """ Отображает данные отсутствий, пропуская колонку ID. """
        log.debug(f"Отображение данных отсутствий (Стр: {self.current_page})")

        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        # Данные с ID
        current_page_raw_data = self.all_data[start_index:end_index]

        # Готовим данные БЕЗ ID для отображения
        current_page_display_data = [row[1:] for row in current_page_raw_data]

        # Очистка и заполнение таблицы
        num_display_cols = len(self.visible_table_headers)
        # Очищаем достаточным кол-вом пустых строк, чтобы избежать "фантомов" при переключении страниц
        self.table.set_sheet_data(data=[[None for _ in range(num_display_cols)] for _ in range(
            self.rows_per_page)], redraw=False, verify=False)
        if current_page_display_data:
            # Заполняем реальными данными (столько строк, сколько есть)
            self.table.set_sheet_data(
                data=current_page_display_data, redraw=False, verify=False)

        self.table.refresh()
        self.update_page_label()
        self.update_buttons_state()

        # Скрытие ID колонки здесь может вызвать мерцание. Лучше в __init__.
        # if self.table.get_total_columns() > 0:
        #      try: self.table.hide_columns(columns=[self.ID_COLUMN_INDEX])
        #      except: pass # Игнорировать ошибку, если уже скрыто

        log.debug(
            f"Отображено {len(current_page_display_data)} строк на стр {self.current_page}.")

    def get_selected_absence_id(self):
        """ Возвращает ID отсутствия выбранной строки или None. """
        selected_rows = self.table.get_selected_rows(get_cells_as_rows=False)
        if not selected_rows:
            return None
        selected_row_index_in_view = list(selected_rows)[0]
        # Рассчитываем индекс в полном списке self.all_data
        actual_data_index = (self.current_page - 1) * \
            self.rows_per_page + selected_row_index_in_view
        if 0 <= actual_data_index < len(self.all_data):
            absence_id = self.all_data[actual_data_index][self.ID_COLUMN_INDEX]
            log.debug(
                f"Выбрана стр. {selected_row_index_in_view} (данные {actual_data_index}), ID={absence_id}")
            return absence_id
        else:
            log.error(
                f"Неверный индекс данных {actual_data_index} для выбранной строки {selected_row_index_in_view}")
            return None

    # --- Обработчики кнопок ---
    def add_absence(self):
        """ Открывает диалог добавления. """
        log.info("Открытие диалога добавления отсутствия")
        dialog = AddAbsenceDialog(self, self.repository)
        dialog.wait_window()
        self.load_data()
        self.display_data()  # Обновить после закрытия

    def edit_absence(self):
        """ Открывает диалог редактирования для выбранной записи. """
        log.info("Попытка открытия диалога редактирования отсутствия")
        absence_id = self.get_selected_absence_id()
        if absence_id is None:
            messagebox.showwarning(
                "Редактирование", "Выберите запись для редактирования.")
            return
        log.info(
            f"Открытие диалога редактирования для Absence ID={absence_id}")
        dialog = EditAbsenceDialog(self, self.repository, absence_id)
        dialog.wait_window()
        self.load_data()
        self.display_data()  # Обновить после закрытия

    def delete_absence(self):
        """ Удаляет выбранную запись об отсутствии. """
        log.info("Попытка удаления отсутствия")
        absence_id = self.get_selected_absence_id()
        if absence_id is None:
            messagebox.showwarning("Удаление", "Выберите запись для удаления.")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить запись об отсутствии (ID={absence_id})?"):
            log.info(f"Подтверждено удаление Absence ID={absence_id}")
            if self.repository.delete_absence(absence_id):
                messagebox.showinfo("Успех", "Запись удалена.")
                log.info(f"Absence ID={absence_id} удален.")
                # Корректировка страницы и перезагрузка данных
                current_total = self.total_rows
                self.load_data()
                new_total_pages = self.get_total_pages()
                if self.current_page > new_total_pages > 0:
                    self.current_page = new_total_pages
                elif current_total > 0 and self.total_rows == 0:
                    self.current_page = 1
                # Проверка случая удаления последней записи на странице (кроме первой)
                elif self.current_page > 1 and (current_total - 1) % self.rows_per_page == 0 and self.total_rows < current_total:
                    self.current_page -= 1

                self.display_data()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить запись.")
                log.error(f"Ошибка удаления Absence ID={absence_id}.")
        else:
            log.info("Удаление отменено.")

    def export_data(self):
        """ Экспортирует ВСЕ записи об отсутствиях в CSV и XML. """
        log.info("Экспорт данных об отсутствиях")
        all_absences_raw, _ = self.repository.get_absences(search_term=None)
        if not all_absences_raw:
            messagebox.showinfo(...)
            log.info(...)
            return

        all_absences_export = [row[1:] for row in all_absences_raw]  # Без ID

        export_dir = "export"
        now = datetime.datetime.now()
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(date_dir, exist_ok=True)
        timestamp = now.strftime("%H-%M-%S")
        csv_filename = os.path.join(date_dir, f"absences_{timestamp}.csv")
        xml_filename = os.path.join(date_dir, f"absences_{timestamp}.xml")

        headers = self.visible_table_headers
        xml_keys = ["PersonnelNumber", "FullName", "AbsenceDate",
                    "IsFullDay", "StartTime", "EndTime", "Reason"]

        csv_success, xml_success = False, False
        try:
            with codecs.open(csv_filename, "w", "utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(all_absences_export)
            log.info(f"Экспорт в CSV: {csv_filename}")
            csv_success = True
        except Exception as e:
            messagebox.showerror("Ошибка CSV", f"{e}")
            log.exception(...)
        try:
            root = ET.Element("Absences")
            for row_data in all_absences_export:
                absence_elem = ET.SubElement(root, "Absence")
                for key, value in zip(xml_keys, row_data):
                    ET.SubElement(absence_elem, key).text = str(value)
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Экспорт в XML: {xml_filename}")
            xml_success = True
        except Exception as e:
            messagebox.showerror("Ошибка XML", f"{e}")
            log.exception(...)

        if csv_success and xml_success:
            messagebox.showinfo(
                "Экспорт", f"Экспорт завершен:\n{csv_filename}\n{xml_filename}")
        elif csv_success:
            messagebox.showinfo("Экспорт", f"CSV готов.\nОшибка XML.")
        elif xml_success:
            messagebox.showinfo("Экспорт", f"XML готов.\nОшибка CSV.")

    def import_absences(self):
        """ Открывает диалог импорта данных об отсутствиях. """
        log.info("Открытие диалога импорта отсутствий")
        # Используем актуальный класс диалога
        dialog = ImportAbsencesDialog(self, self.repository)
        dialog.wait_window()  # Ждем закрытия
        # Перезагружаем данные после импорта
        self.load_data()
        self.display_data()

    def search(self, event=None):
        """ Обработчик поиска. """
        log.debug(f"Поиск отсутствий: '{self.search_entry.get()}'")
        self.current_page = 1
        self.load_data()
        self.display_data()
        # Скрытие колонки ID (лучше делать в __init__)
        # if hasattr(self, 'table') and self.table.winfo_exists(): self.table.hide_columns(...)

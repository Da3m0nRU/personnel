# gui/events_frame.py
import customtkinter as ctk
from config import *
import logging
from .base_table_frame import BaseTableFrame  # Импортируем базовый класс
# Импортируем репозиторий
from db.employee_event_repository import EmployeeEventRepository
from .utils import load_icon  # !!! Импортируем загрузчик иконок
import os  # !!! Для работы с путями
import datetime  # !!! Для временных меток
import codecs  # !!! Для корректной записи CSV в UTF-8 с BOM
import csv  # !!! Для работы с CSV
import xml.etree.ElementTree as ET  # !!! Для работы с XML
from tkinter import messagebox  # !!! Для сообщений пользователю


log = logging.getLogger(__name__)


class EventsFrame(BaseTableFrame):
    """
    Фрейм для отображения таблицы кадровых событий (только чтение) с экспортом.
    Стилизован под EmployeesFrame.
    """

    def __init__(self, master, db):
        super().__init__(master, db, table_height=350)
        self.repository = EmployeeEventRepository(db)
        self.db = db
        self.create_widgets()
        self.load_data()
        self.display_data()

    def create_widgets(self):
        """
        Создает виджеты для EventsFrame, включая кнопку "Экспорт".
        """
        log.debug("Создание виджетов для EventsFrame в стиле EmployeesFrame")

        # --- Заголовок ---
        title_label = ctk.CTkLabel(
            self,
            text="КАДРОВЫЕ СОБЫТИЯ",
            font=("Arial", 46, "bold"),
            text_color=LABEL_TEXT_COLOR,
            anchor="w"
        )
        title_label.place(x=27, y=40)

        # --- Кнопка "Экспорт" ---
        # Копируем стиль и расчеты из EmployeesFrame
        export_button_width = 180  # Как в EmployeesFrame
        export_button_x = 27 + 220 + 27 + 150 + 20  # Рассчитываем X левее поиска
        export_button_y = 139  # Та же высота Y, что и у поиска

        self.export_button = ctk.CTkButton(
            self,
            text="  ЭКСПОРТ",
            font=("Arial", 18, "bold"),
            command=self.export_data,  # !!! Привязываем метод
            fg_color=BUTTON_BG_COLOR,  # Стандартный фон кнопки
            text_color="#2196F3",  # Синий цвет текста (как в EmployeesFrame)
            border_width=2,  # Рамка
            border_color="#2196F3",  # Синий цвет рамки
            hover_color=BUTTON_HOVER_COLOR,  # Стандартный цвет при наведении
            corner_radius=12,  # Скругление углов
            width=export_button_width,  # Ширина кнопки
            height=40,  # Высота кнопки
            image=load_icon("export.png", size=(20, 20)),  # Иконка экспорта
            compound="left"  # Иконка слева от текста
        )
        self.export_button.place(
            x=export_button_x, y=export_button_y)  # Размещаем кнопку

        # --- Поле поиска ---
        search_entry_width = 257
        # Размещаем правее кнопки экспорта
        search_entry_x_coordinate = export_button_x + \
            export_button_width + 20  # Кнопка + отступ
        search_entry_y_coordinate = 139

        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Поиск событий...",
            width=search_entry_width,
            height=40,
            font=DEFAULT_FONT,
            text_color=LABEL_TEXT_COLOR,
            placeholder_text_color="gray",
            fg_color="white"
        )
        self.search_entry.place(
            x=search_entry_x_coordinate, y=search_entry_y_coordinate)
        self.search_entry.bind("<KeyRelease>", self.search)

        # --- Таблица и пагинация ---
        self.create_table_widgets()
        table_wrapper_y_coordinate = 139 + 40 + 27
        self.table_wrapper.place(x=27, y=table_wrapper_y_coordinate)

        # --- Заголовки таблицы ---
        self.table_headers = ["Дата", "Событие", "Таб.№", "ФИО сотрудника",
                              "Новая должность", "Новый отдел", "Причина"]  # Сохраняем для экспорта
        self.table.headers(self.table_headers)

        # --- Делаем таблицу только для чтения ---
        self.table.readonly(True)

        log.debug("Виджеты EventsFrame созданы (с кнопкой Экспорт)")

    def load_data(self, search_term=None):
        """ Загружает данные о кадровых событиях из репозитория. """
        log.debug(
            f"Загрузка данных кадровых событий (search_term: {search_term})")
        if search_term is None:
            search_term = self.search_entry.get().strip()

        # Запрашиваем данные с учетом поиска для корректного отображения total_rows
        self.all_data, self.total_rows = self.repository.get_events(
            search_term=search_term)

        if self.all_data is None:
            log.warning(
                "EventsFrame.load_data: Репозиторий вернул None, устанавливаем пустой список.")
            self.all_data = []
            self.total_rows = 0
        else:
            # Заменяем None на пустые строки для tksheet
            processed_data = []
            for row in self.all_data:
                processed_row = ["" if item is None else item for item in row]
                processed_data.append(processed_row)
            self.all_data = processed_data
            log.debug(
                f"EventsFrame.load_data: Загружено {self.total_rows} строк событий.")

    def display_data(self, search_term=None):
        """ Отображает данные кадровых событий в таблице с учетом пагинации. """
        log.debug(
            f"Отображение данных кадровых событий (Страница: {self.current_page}, Поиск: '{search_term or self.search_entry.get().strip()}')")

        # Пагинация применяется к self.all_data, которые уже загружены (и потенциально отфильтрованы)
        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        current_page_data = self.all_data[start_index:end_index]

        # Очистка таблицы
        num_cols = len(self.table_headers)  # Используем сохраненные заголовки
        self.table.set_sheet_data(data=[[None for _ in range(num_cols)] for _ in range(
            self.rows_per_page)], redraw=False, verify=False)

        if current_page_data:
            self.table.set_sheet_data(
                data=current_page_data, redraw=False, verify=False)

        self.table.refresh()
        self.update_page_label()
        self.update_buttons_state()
        log.debug(
            f"Отображено {len(current_page_data)} строк событий на странице {self.current_page}.")

    def search(self, event=None):
        """ Обработчик события ввода в поле поиска. """
        log.debug(f"Событие поиска: '{self.search_entry.get()}'")
        self.current_page = 1
        self.load_data()      # Перезагружаем данные с учетом поиска
        self.display_data()   # Отображаем отфильтрованные и обрезанные пагинацией данные

    # !!! НОВЫЙ МЕТОД ЭКСПОРТА !!!
    def export_data(self):
        """Экспортирует все кадровые события в CSV и XML."""
        log.info("Экспорт данных кадровых событий")

        # Получаем ВСЕ данные, игнорируя текущий поиск и пагинацию в UI
        all_events_data, _ = self.repository.get_events(
            search_term=None)  # Передаем None, чтобы получить всё

        if not all_events_data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            log.info("Нет данных событий для экспорта")
            return

        # Заменяем None на пустые строки перед экспортом
        export_ready_data = []
        for row in all_events_data:
            processed_row = ["" if item is None else item for item in row]
            export_ready_data.append(processed_row)

        export_dir = "export"
        now = datetime.datetime.now()
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(date_dir, exist_ok=True)
        timestamp = now.strftime("%H-%M-%S")
        # Указываем префикс 'events_' для файлов
        csv_filename = os.path.join(date_dir, f"events_{timestamp}.csv")
        xml_filename = os.path.join(date_dir, f"events_{timestamp}.xml")

        # Названия полей для CSV и тегов для XML (согласуем с заголовками таблицы и порядком в SQL)
        field_map = {
            "EventDate": "Дата",
            "EventType": "Событие",
            "PersonnelNumber": "Таб.№",
            "FullName": "ФИО сотрудника",
            "NewPosition": "Новая должность",
            "NewDepartment": "Новый отдел",
            "Reason": "Причина"
        }
        # Порядок ключей важен для DictWriter и XML
        fieldnames_keys_ordered = ["EventDate", "EventType", "PersonnelNumber",
                                   "FullName", "NewPosition", "NewDepartment", "Reason"]
        # Используем русские заголовки для CSV
        fieldnames_ru_ordered = [field_map[key]
                                 for key in fieldnames_keys_ordered]

        # --- Экспорт в CSV ---
        try:
            # Используем codecs для BOM
            with codecs.open(csv_filename, "w", "utf-8-sig") as csvfile:
                # Используем обычный writer, так как у нас список списков
                writer = csv.writer(csvfile)
                # Записываем русские заголовки
                writer.writerow(fieldnames_ru_ordered)
                # Записываем все подготовленные строки
                writer.writerows(export_ready_data)
            log.info(f"Данные событий экспортированы в CSV: {csv_filename}")

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в CSV: {e}")
            log.exception(f"Ошибка при экспорте событий в CSV: {e}")
            # Не выходим, пробуем экспортировать в XML
        else:
            # Переменная для отслеживания успешности хотя бы одного экспорта
            csv_export_successful = True

        # --- Экспорт в XML ---
        xml_export_successful = False  # Изначально неуспешен
        try:
            root = ET.Element("EmployeeEvents")  # Корневой элемент
            for row_list in export_ready_data:
                event_elem = ET.SubElement(root, "Event")
                for i, key in enumerate(fieldnames_keys_ordered):
                    # Используем английские названия как имена тегов
                    ET.SubElement(event_elem, key).text = str(row_list[i])

            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")  # Форматируем для читаемости
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Данные событий экспортированы в XML: {xml_filename}")
            xml_export_successful = True  # Отмечаем успех

        except Exception as e:
            messagebox.showerror(
                "Ошибка экспорта", f"Ошибка при экспорте в XML: {e}")
            log.exception(f"Ошибка при экспорте событий в XML: {e}")
            # Ничего страшного, если CSV уже успешно экспортировался

        # --- Финальное сообщение ---
        if csv_export_successful and xml_export_successful:
            messagebox.showinfo("Экспорт завершен",
                                f"Данные кадровых событий успешно экспортированы в:\n{csv_filename}\n{xml_filename}")
        elif csv_export_successful:
            messagebox.showinfo("Экспорт CSV завершен",
                                f"Данные кадровых событий успешно экспортированы в:\n{csv_filename}\n(Ошибка при экспорте в XML)")
        elif xml_export_successful:
            messagebox.showinfo("Экспорт XML завершен",
                                f"Данные кадровых событий успешно экспортированы в:\n(Ошибка при экспорте в CSV)\n{xml_filename}")
        # Если оба не удались, ошибки уже были показаны

# gui/absences_frame.py
import customtkinter as ctk
from config import *
import logging
from .base_table_frame import BaseTableFrame
from db.absence_repository import AbsenceRepository
from .dialogs.add_absence_dialog import AddAbsenceDialog  # Импортируем будущий диалог
from .utils import load_icon  # Для иконки кнопки


log = logging.getLogger(__name__)


class AbsencesFrame(BaseTableFrame):
    """
    Фрейм для отображения и добавления записей об отсутствиях сотрудников.
    """

    def __init__(self, master, db):
        super().__init__(master, db, table_height=350)  # Стандартная высота
        self.repository = AbsenceRepository(db)
        self.db = db
        self.create_widgets()
        self.load_data()
        self.display_data()

    def create_widgets(self):
        """
        Создает виджеты для AbsencesFrame (заголовок, кнопка добавления, поиск, таблица).
        """
        log.debug("Создание виджетов для AbsencesFrame")

        # --- Заголовок ---
        title_label = ctk.CTkLabel(
            self,
            text="ОТСУТСТВИЯ",  # Новый заголовок
            font=("Arial", 46, "bold"),
            text_color=LABEL_TEXT_COLOR,
            anchor="w"
        )
        title_label.place(x=27, y=40)  # Стандартное расположение

        # --- Кнопка "Новая запись" ---
        # Размещаем там же, где кнопка "Добавить" в EmployeesFrame
        self.add_button = ctk.CTkButton(
            self,
            text="  НОВАЯ ЗАПИСЬ",
            font=("Arial", 18, "bold"),
            command=self.add_absence,  # Вызываем метод добавления
            fg_color=BUTTON_BG_COLOR,  # Стандартный фон
            text_color="#0057FC",  # Синий текст (как в EmployeesFrame)
            border_width=2,
            border_color="#0057FC",
            hover_color=BUTTON_HOVER_COLOR,
            corner_radius=12,
            width=220,  # Стандартная ширина
            height=40,
            image=load_icon("plus.png", size=(20, 20)),  # Иконка "+"
            compound="left"
        )
        # Стандартное расположение для кнопки "Добавить"
        self.add_button.place(x=27, y=139)

        # --- Поле поиска ---
        search_entry_width = 257
        # Расположение как в EmployeesFrame и EventsFrame
        search_entry_x_coordinate = 27 + 220 + 27 + 150 + 20 + 180 + 20
        search_entry_y_coordinate = 139

        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Поиск отсутствий...",
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
        # В соответствии с ТЗ 4.1 и запросом GET_ABSENCES
        self.table_headers = ["Таб.№", "ФИО", "Дата",
                              "Полный день", "Начало", "Окончание", "Причина"]
        self.table.headers(self.table_headers)

        # Таблица только для чтения (изменения через диалог)
        self.table.readonly(True)

        log.debug("Виджеты AbsencesFrame созданы")

    def load_data(self, search_term=None):
        """ Загружает данные об отсутствиях из репозитория. """
        log.debug(f"Загрузка данных отсутствий (search_term: {search_term})")
        if search_term is None:
            search_term = self.search_entry.get().strip()

        # Используем метод get_absences из репозитория
        # Он уже возвращает обработанные данные (без None)
        self.all_data, self.total_rows = self.repository.get_absences(
            search_term=search_term)

        # Проверка на None уже внутри get_absences
        log.debug(
            f"AbsencesFrame.load_data: Загружено {self.total_rows} строк отсутствий.")

    def display_data(self, search_term=None):
        """ Отображает данные отсутствий в таблице с учетом пагинации. """
        log.debug(
            f"Отображение данных отсутствий (Страница: {self.current_page}, Поиск: '{search_term or self.search_entry.get().strip()}')")

        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        current_page_data = self.all_data[start_index:end_index]

        # Очистка таблицы
        num_cols = len(self.table_headers)
        self.table.set_sheet_data(data=[[None for _ in range(num_cols)] for _ in range(
            self.rows_per_page)], redraw=False, verify=False)

        if current_page_data:
            self.table.set_sheet_data(
                data=current_page_data, redraw=False, verify=False)

        self.table.refresh()
        self.update_page_label()
        self.update_buttons_state()
        log.debug(
            f"Отображено {len(current_page_data)} строк отсутствий на странице {self.current_page}.")

    def search(self, event=None):
        """ Обработчик события ввода в поле поиска. """
        log.debug(f"Событие поиска отсутствий: '{self.search_entry.get()}'")
        self.current_page = 1
        self.load_data()
        self.display_data()

    def add_absence(self):
        """ Открывает диалог добавления новой записи об отсутствии. """
        log.info("Открытие диалога добавления отсутствия")
        # Передаем репозиторий отсутствий
        dialog = AddAbsenceDialog(self, self.repository)
        dialog.wait_window()  # Ждем закрытия диалога

        # После закрытия диалога перезагружаем и отображаем данные
        self.load_data()
        self.display_data()

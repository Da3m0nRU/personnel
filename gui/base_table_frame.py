# gui/base_table_frame.py
import customtkinter as ctk
from tksheet import Sheet
from config import *
import logging
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class BaseTableFrame(ctk.CTkFrame, ABC):
    """
    Абстрактный базовый класс для вкладок с табличным отображением данных.
    """

    def __init__(self, master, db, table_width=1136, table_height=350):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        self.current_page = 1
        self.rows_per_page = 10
        self.total_rows = 0
        self.data = []
        self.table_width = table_width  # !!!
        self.table_height = table_height  # !!!

    @abstractmethod
    def load_data(self, search_term=None):
        """Абстрактный метод: загрузка данных"""
        raise NotImplementedError

    @abstractmethod
    def display_data(self, search_term=None):
        """
        Абстрактный метод: отображает данные в таблице
        """
        raise NotImplementedError  # абстрактный!

    def create_table_widgets(self):
        """
        Создает виджеты таблицы и пагинации.
        """
        log.debug("Создание виджетов таблицы (BaseTableFrame)")

        self.table_wrapper = ctk.CTkFrame(
            self, fg_color="white", width=1136, height=400)
        # !!! table_wrapper размещается *относительно* BaseTableFrame (self).
        #     Координаты и размеры пока оставим, как есть, потом настроим.
        self.table_wrapper.place(x=27, y=195 + 40 + 27)

        self.table = Sheet(self.table_wrapper,  # Родитель
                           width=self.table_width,     # !!!
                           height=self.table_height,    # !!!
                           font=TABLE_FONT,  # шрифты
                           header_font=TABLE_HEADER_FONT
                           )

        # !!! Используем grid ВНУТРИ table_wrapper
        self.table.grid(row=0, column=0, sticky="nsew",
                        padx=10, pady=10)  # !!!

        self.table.enable_bindings(("single_select",
                                    "row_select",
                                    "column_width_resize",
                                    "arrowkeys",
                                    "copy",
                                    "paste",
                                    "delete",
                                    "edit_cell",
                                    "rc_select"
                                    ))
        self.table.disable_bindings("row_height_resize", "cut", "undo", "redo",
                                    "rc_insert_row", "rc_delete_row",
                                    "rc_insert_column", "rc_delete_column", "hide_rows", "hide_columns")
        # --- Пагинация (теперь *вне* table_wrapper) ---
        self.pagination_frame = ctk.CTkFrame(
            self.table_wrapper, fg_color="transparent")
        # !!! Используем grid, строка 1, колонка 0
        self.pagination_frame.grid(
            row=1, column=0, sticky="ew", padx=10, pady=(0, 10))  # !!!

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
            state="disabled"
        )

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Страница 1 / 1",
                                       font=("Arial", 16, "bold"), text_color="#000000")

        self.prev_button.pack(side="left", padx=(0, 5))
        self.page_label.pack(side="left", padx=5)
        self.next_button.pack(side="left", padx=(5, 0))

        # !!! Очень важно: конфигурируем grid, чтобы таблица растягивалась !!!
        self.table_wrapper.grid_rowconfigure(0, weight=1)
        self.table_wrapper.grid_columnconfigure(0, weight=1)

    def prev_page(self):
        """Переходит на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_data()

    def next_page(self):
        """Переходит на следующую страницу."""
        if self.current_page < self.get_total_pages():
            self.current_page += 1
            self.display_data()

    def update_page_label(self):
        """Обновляет метку с номером текущей страницы и общим количеством страниц."""
        total_pages = self.get_total_pages()
        if total_pages == 0:
            self.page_label.configure(text="Страница 1 / 1")
        else:
            self.page_label.configure(
                text=f"Страница {self.current_page} / {total_pages}")

    def get_total_pages(self):
        """Вычисляет и возвращает общее количество страниц."""
        return (self.total_rows + self.rows_per_page - 1) // self.rows_per_page

    def update_buttons_state(self):
        """Обновляет состояние кнопок пагинации."""
        if self.current_page == 1:
            self.prev_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.prev_button.configure(
                state="normal", border_width=1, fg_color="transparent")

        if self.current_page >= self.get_total_pages():
            self.next_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.next_button.configure(
                state="normal", border_width=1, fg_color="transparent")

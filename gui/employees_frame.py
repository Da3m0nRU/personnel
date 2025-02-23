# gui/employees_frame.py
import customtkinter as ctk
from config import *  # Импортируем все из config
from tksheet import Sheet
from .utils import load_icon


class EmployeesFrame(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        # Пагинация
        self.current_page = 1
        self.rows_per_page = 10  # Количество строк на странице
        self.total_rows = 0      # Общее количество строк (будет обновляться)
        self.data = []           # !!! Добавляем атрибут для хранения данных

        self.create_widgets()
        self.display_data()  # !!! Отображаем данные при инициализации

    def create_widgets(self):
        # Заголовок (все большими буквами, изменен шрифт и размер, выравнивание по левому краю)
        title_label = ctk.CTkLabel(
            self,
            text="СОТРУДНИКИ",
            font=("Arial", 46, "bold"),
            text_color=LABEL_TEXT_COLOR,
            anchor="w"
        )
        title_label.place(x=27, y=40)

        # Кнопка "Новая запись"
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

        # Поле поиска
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
        self.search_entry.place(x=27 + 220 + 27, y=139)

        # Wrapper для таблицы
        self.table_wrapper = ctk.CTkFrame(
            self, fg_color="white")
        self.table_wrapper.place(x=27, y=195)

        # Создаем таблицу (Sheet)
        self.table = Sheet(self.table_wrapper,
                           width=1136,
                           height=300
                           )
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table.headers(
            ["Таб. номер", "Фамилия", "Имя", "Отчество", "Дата рожд.", "Пол", "Должность", "Отдел", "Состояние"])

        # self.table.set_all_row_heights(40)  # Высота всех строк
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

        # Контейнер для пагинации
        self.pagination_frame = ctk.CTkFrame(
            self.table_wrapper,  fg_color="transparent")
        self.pagination_frame.pack(
            side="bottom", fill="x", padx=10, pady=(0, 10))

        # Кнопки пагинации
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

        # Label для текущей страницы
        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Страница 1",
            font=("Arial", 16, "bold"),
            text_color="#000000"
        )

        # Размещаем кнопки и label внутри pagination_frame
        self.prev_button.pack(side="left", padx=(0, 5))
        self.page_label.pack(side="left", padx=5)
        self.next_button.pack(side="left", padx=(5, 0))

    def add_employee(self):
        print("Добавить сотрудника")

    def prev_page(self):
        if self.current_page > 1:  # !!! Проверяем, можно ли перейти назад
            self.current_page -= 1
            self.display_data()  # !!! Обновляем данные

    def next_page(self):
        # !!!  Проверяем, можно ли перейти вперед
        if self.current_page < (self.total_rows + self.rows_per_page - 1) // self.rows_per_page:
            self.current_page += 1
            self.display_data()  # !!! Обновляем данные

    def update_page_label(self):
        self.page_label.configure(text=f"Страница {self.current_page}")

    def update_buttons_state(self):
        if self.current_page == 1:
            self.prev_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.prev_button.configure(
                state="normal", border_width=1, fg_color="transparent")
        # !!!  Исправлено условие для последней страницы
        if self.current_page == (self.total_rows + self.rows_per_page - 1) // self.rows_per_page:
            self.next_button.configure(
                state="disabled", border_width=0, fg_color="#E9ECEF")
        else:
            self.next_button.configure(
                state="normal", border_width=1, fg_color="transparent")

    def display_data(self):
        # Заглушка с данными
        data = [
            ["1001", "Иванов", "Иван", "Иванович", "1980-05-10",
                "Мужской", "Программист", "IT-отдел", "Работает"],
            ["1002", "Петрова", "Мария", "Сергеевна", "1992-11-20",
             "Женский", "Менеджер", "Отдел продаж", "Работает"],
            ["1003", "Сидоров", "Петр", "Алексеевич", "1975-03-15",
             "Мужской", "Бухгалтер", "Бухгалтерия", "Работает"],
            ["1004", "Смирнова", "Анна", "Васильевна", "1988-07-22",
             "Женский", "Юрист", "Юридический отдел", "Работает"],
            ["1005", "Кузнецов", "Дмитрий", "Николаевич", "1995-01-18",
             "Мужской", "Дизайнер", "IT-отдел", "Работает"],
            ["1006", "Михайлова", "Елена", "Петровна", "1983-09-05",
             "Женский", "Секретарь", "Отдел кадров", "Работает"],
            ["1007", "Лебедев", "Андрей", "Викторович", "1970-12-01",
             "Мужской", "Директор", "Администрация", "Работает"],
            ["1008", "Соколова", "Ольга", "Игоревна", "1998-04-28",
             "Женский", "Программист", "IT-отдел", "Работает"],
            ["1009", "Морозов", "Сергей", "Владимирович", "1986-06-14",
             "Мужской", "Менеджер", "Отдел продаж", "Работает"],
            ["1010", "Новикова", "Татьяна", "Андреевна", "1978-02-09",
             "Женский", "Бухгалтер", "Бухгалтерия", "Работает"],
            ["1011", "Федоров", "Александр", "Михайлович", "1990-08-30",
             "Мужской", "Юрист", "Юридический отдел", "Работает"],
            ["1012", "Волкова", "Светлана", "Александровна", "1981-10-12",
             "Женский", "Дизайнер", "IT-отдел", "Работает"],
            ["1013", "Зайцев", "Максим", "Сергеевич", "1997-03-25",
             "Мужской", "Секретарь", "Отдел кадров", "Работает"],
            ["1014", "Павлова", "Наталья", "Дмитриевна", "1972-05-03",
             "Женский", "Директор", "Администрация", "Работает"],
            ["1015", "Козлов", "Владимир", "Иванович", "1989-11-07",
             "Мужской", "Программист", "IT-отдел", "Работает"],
            ["1016", "Белова", "Екатерина", "Алексеевна", "1984-01-19",
             "Женский", "Менеджер", "Отдел продаж", "Работает"],
            ["1017", "Орлов", "Денис", "Валерьевич", "1977-07-29",
             "Мужской", "Бухгалтер", "Бухгалтерия", "Работает"],
            ["1018", "Григорьева", "Ирина", "Сергеевна", "1993-04-16",
             "Женский", "Юрист", "Юридический отдел", "Работает"],
            ["1019", "Васильев", "Роман", "Андреевич", "1982-06-08",
             "Мужской", "Дизайнер", "IT-отдел", "Работает"],
            ["1020", "Антонова", "Юлия", "Михайловна", "1979-12-24",
             "Женский", "Секретарь", "Отдел кадров", "Работает"],
        ]
        self.data = data  # !!! Сохраняем данные
        self.total_rows = len(data)  # !!! Обновляем общее количество строк

        # Вычисляем срез данных для текущей страницы
        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        current_page_data = self.data[start_index:end_index]

        # Очищаем таблицу перед отображением новых данных
        self.table.set_sheet_data([[None for _ in range(
            len(self.table.headers()))] for _ in range(self.table.total_rows())])

        # Отображаем данные
        self.table.set_sheet_data(current_page_data)

        self.update_page_label()  # Обновляем текст метки страницы
        self.update_buttons_state()  # Обновляем состояние кнопок

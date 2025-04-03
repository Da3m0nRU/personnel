# gui/users_frame.py
import customtkinter as ctk
from config import *
import logging
import os
import datetime
import codecs
import csv
import xml.etree.ElementTree as ET
from tkinter import messagebox

# Импортируем базовый класс и репозиторий
from .base_table_frame import BaseTableFrame
from db.user_repository import UserRepository
# Импортируем диалоги
from .dialogs.add_user_dialog import AddUserDialog
from .dialogs.edit_user_dialog import EditUserDialog
from .dialogs.import_users_dialog import ImportUsersDialog
# Импортируем утилиты
from .utils import load_icon

log = logging.getLogger(__name__)


class UsersFrame(BaseTableFrame):
    """
    Фрейм для управления пользователями системы (только для Администратора).
    Отображает ВСЕ колонки из запроса, включая ID.
    """
    # ID_COLUMN_INDEX больше не нужен для скрытия, но оставляем для информации
    ID_COLUMN_INDEX = 0

    def __init__(self, master, db, current_user_id):
        """
        Инициализатор фрейма управления пользователями.

        Args:
            master: Родительский виджет.
            db: Экземпляр базы данных.
            current_user_id: ID текущего пользователя (Администратора).
        """
        # Инициализируем базовый класс с нужной высотой таблицы
        super().__init__(master, db, table_height=450)
        self.repository = UserRepository(db)
        self.db = db
        # Сохраняем ID текущего пользователя для проверок безопасности
        self.current_user_id = current_user_id
        # Получаем и сохраняем ID роли администратора для проверок
        self.admin_role_id = self.repository.get_admin_role_id()

        # --- Определяем ПОЛНЫЙ набор заголовков таблицы ---
        # Порядок должен ТОЧНО соответствовать SELECT в q.GET_USERS_BASE
        # ID(0), Login(1), Hash(2), EmpInfo(3), Role(4), Email(5)
        self.visible_table_headers = [
            "ID", "Логин", "Хеш пароля", "Сотрудник", "Роль", "Email"]
        # ----------------------------------------------------

        # Создаем все виджеты интерфейса
        self.create_widgets()
        # Загружаем данные из репозитория
        self.load_data()
        # Отображаем первую страницу данных
        self.display_data()

        # Скрытие колонки ID теперь не выполняется

    def create_widgets(self):
        """Создает все виджеты интерфейса для вкладки Управление Пользователями."""
        log.debug("Создание виджетов для UsersFrame")

        # --- Заголовок вкладки ---
        title_label = ctk.CTkLabel(
            self, text="УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ", font=TITLE_BOLD_FONT,
            text_color=LABEL_TEXT_COLOR, anchor="w"
        )
        title_label.place(x=27, y=40)

        # --- Кнопки управления (Ряд 1) ---
        btn_y1 = 139  # Вертикальная позиция первого ряда кнопок
        # Кнопка "Новая запись"
        self.add_button = ctk.CTkButton(
            self, text="  НОВАЯ ЗАПИСЬ", font=BOLD_FONT, command=self.add_user, width=220, height=40,
            image=load_icon("plus.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#0057FC", border_width=2, border_color="#0057FC", hover_color=BUTTON_HOVER_COLOR
        )
        self.add_button.place(x=27, y=btn_y1)

        # Кнопка "Удалить"
        delete_btn_x = 27 + 220 + 27  # Позиция X кнопки "Удалить"
        self.delete_button = ctk.CTkButton(
            self, text="  УДАЛИТЬ", font=BOLD_FONT, command=self.delete_user, width=150, height=40,
            image=load_icon("cross.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#FF4136", border_width=2, border_color="#FF4136", hover_color=BUTTON_HOVER_COLOR
        )
        self.delete_button.place(x=delete_btn_x, y=btn_y1)

        # Кнопка "Изменить"
        edit_btn_x = delete_btn_x + 150 + 20  # Позиция X кнопки "Изменить"
        self.edit_button = ctk.CTkButton(
            self, text="  ИЗМЕНИТЬ", font=BOLD_FONT, command=self.edit_user, width=180, height=40,
            image=load_icon("edit.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#FF8C00", border_width=2, border_color="#FF8C00", hover_color="#FFB347"
        )
        self.edit_button.place(x=edit_btn_x, y=btn_y1)

        # --- Кнопки управления (Ряд 2) ---
        btn_y2 = btn_y1 + 40 + 20  # Вертикальная позиция второго ряда кнопок
        # Кнопка "Импорт"
        self.import_button = ctk.CTkButton(
            self, text="  ИМПОРТ", font=BOLD_FONT, command=self.import_users, width=220, height=40,
            image=load_icon("import.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#4CAF50",  # Зеленый стиль
            border_width=2, border_color="#4CAF50",
            hover_color=BUTTON_HOVER_COLOR
        )
        self.import_button.place(x=27, y=btn_y2)

        # Кнопка "Экспорт"
        export_btn_x = edit_btn_x  # Выравниваем с кнопкой "Изменить"
        self.export_button = ctk.CTkButton(
            self, text="  ЭКСПОРТ", font=BOLD_FONT, command=self.export_users, width=180, height=40,
            image=load_icon("export.png", size=(20, 20)), compound="left", corner_radius=12,
            fg_color=BUTTON_BG_COLOR, text_color="#2196F3", border_width=2, border_color="#2196F3", hover_color=BUTTON_HOVER_COLOR
        )
        self.export_button.place(x=export_btn_x, y=btn_y2)

        # --- Поле поиска ---
        search_entry_width = 257  # Ширина поля поиска
        search_entry_x = export_btn_x + 180 + 20  # Позиция X поля поиска
        # Позиция Y поля поиска (на уровне 2-го ряда кнопок)
        search_entry_y = btn_y2
        self.search_entry = ctk.CTkEntry(
            self, placeholder_text="Поиск пользователей...", width=search_entry_width, height=40,
            font=DEFAULT_FONT, text_color=LABEL_TEXT_COLOR, placeholder_text_color="gray", fg_color="white"
        )
        self.search_entry.place(x=search_entry_x, y=search_entry_y)
        # Привязываем обработчик поиска к событию отпускания клавиши
        self.search_entry.bind("<KeyRelease>", self.search)

        # --- Создаем виджеты таблицы и пагинации из базового класса ---
        self.create_table_widgets()
        # Размещаем контейнер для таблицы и пагинации
        table_wrapper_y = btn_y2 + 40 + 27  # Позиция Y контейнера
        table_wrapper_height = self.table_height + 60  # Высота контейнера
        # Устанавливаем позицию и размеры контейнера
        self.table_wrapper.place(
            x=27, y=table_wrapper_y)

        # --- Устанавливаем заголовки таблицы ---
        # Используем self.visible_table_headers, определенные в __init__
        self.table.headers(self.visible_table_headers)
        # Устанавливаем режим "только для чтения" для таблицы
        self.table.readonly(True)

        log.debug("Виджеты UsersFrame созданы")

    def load_data(self, search_term=None):
        """
        Загружает данные пользователей из репозитория с учетом поиска.
        Обновляет self.all_data и self.total_rows.
        """
        log.debug(
            f"Загрузка данных пользователей (search_term: {search_term})")
        if search_term is None:
            search_term = self.search_entry.get().strip()
        # Запрос к репозиторию возвращает данные включая ID первым столбцом
        self.all_data, self.total_rows = self.repository.get_users(
            search_term=search_term)
        # Обработка случая, если репозиторий вернул None
        if self.all_data is None:
            log.warning(
                "UsersFrame.load_data: Репозиторий вернул None, устанавливаем пустой список.")
            self.all_data = []
            self.total_rows = 0
        log.debug(
            f"UsersFrame.load_data: Загружено {self.total_rows} строк пользователей.")

    def display_data(self):
        """
        Отображает данные текущей страницы в таблице tksheet (включая ID).
        """
        log.debug(
            f"Отображение данных пользователей (Страница: {self.current_page})")

        # 1. Вычисляем индексы строк для текущей страницы
        start_index = (self.current_page - 1) * self.rows_per_page
        end_index = start_index + self.rows_per_page
        # 2. Получаем срез данных для текущей страницы (включая ID)
        current_page_display_data = self.all_data[start_index:end_index]
        num_display_rows = len(current_page_display_data)
        # 3. Определяем количество колонок по заголовкам
        num_display_cols = len(self.visible_table_headers)

        try:
            # Проверяем, существует ли виджет таблицы
            if self.table.winfo_exists():
                # 4. Устанавливаем заголовки (на всякий случай, если они сбились)
                self.table.headers(self.visible_table_headers, redraw=True)
                log.debug(
                    f"Установлены заголовки (вкл. ID): {self.visible_table_headers}")

                # 5. Очищаем таблицу перед заполнением
                #    Создаем пустые строки для надежной очистки
                blank_rows = [[None for _ in range(
                    num_display_cols)] for _ in range(self.rows_per_page)]
                self.table.set_sheet_data(
                    data=blank_rows, redraw=False, verify=False)
                log.debug(
                    f"Таблица очищена {self.rows_per_page} пустыми строками.")

                # 6. Заполняем таблицу данными текущей страницы (если они есть)
                if current_page_display_data:
                    # Передаем все данные строки (включая ID)
                    self.table.set_sheet_data(
                        data=current_page_display_data, redraw=False, verify=False)
                    log.debug(
                        f"Таблица заполнена {num_display_rows} строками данных (вкл. ID).")
                else:
                    log.debug("Нет данных для отображения на текущей странице.")

                # 7. Обновляем элементы управления пагинацией
                self.update_page_label()
                self.update_buttons_state()

                # 8. Обновляем отображение таблицы
                self.table.refresh()
            else:
                log.warning(
                    "Виджет таблицы не существует при попытке отобразить данные.")
        except Exception as e:
            # Обработка непредвиденных ошибок при работе с таблицей
            log.exception(f"Критическая ошибка в display_data UsersFrame: {e}")
            messagebox.showerror(
                "Ошибка отображения", "Произошла ошибка при отображении данных пользователей.")

        log.debug(
            f"Отображено {num_display_rows} пользователей на странице {self.current_page}.")

    def search(self, event=None):
        """
        Обработчик события ввода в поле поиска.
        Перезагружает данные с учетом нового поискового запроса и отображает первую страницу.
        """
        search_query = self.search_entry.get().strip()
        log.debug(f"Событие поиска пользователей: '{search_query}'")
        # Сбрасываем на первую страницу при новом поиске
        self.current_page = 1
        # Загружаем данные, отфильтрованные на уровне SQL
        self.load_data(search_term=search_query)
        # Отображаем результат
        self.display_data()

    def get_selected_user_id(self):
        """
        Возвращает ID пользователя, соответствующего выбранной строке в таблице.
        Возвращает None, если ничего не выбрано или произошла ошибка.
        """
        # Получаем индексы выбранных строк в видимой таблице
        selected_rows_indices = self.table.get_selected_rows(
            get_cells_as_rows=False)
        if not selected_rows_indices:
            return None  # Ни одна строка не выбрана

        # Берем индекс первой (и единственной, т.к. single_select) строки
        selected_row_index_in_view = list(selected_rows_indices)[0]

        # Рассчитываем реальный индекс в полном списке данных self.all_data
        actual_data_index = (self.current_page - 1) * \
            self.rows_per_page + selected_row_index_in_view

        # Проверяем валидность рассчитанного индекса
        if 0 <= actual_data_index < len(self.all_data):
            # ID пользователя находится в первом столбце (индекс 0) списка self.all_data
            user_id = self.all_data[actual_data_index][self.ID_COLUMN_INDEX]
            log.debug(
                f"Выбрана строка в таблице: {selected_row_index_in_view}, Индекс в данных: {actual_data_index}, User ID={user_id}")
            return user_id
        else:
            # Логируем ошибку, если индекс оказался некорректным
            log.error(
                f"Ошибка: Неверный индекс данных ({actual_data_index}) для выбранной строки ({selected_row_index_in_view})")
            return None

    def add_user(self):
        """Открывает диалог добавления нового пользователя."""
        log.info("Открытие диалога добавления пользователя")
        # Создаем и отображаем модальный диалог
        dialog = AddUserDialog(self, self.repository)
        dialog.wait_window()  # Ждем закрытия диалога
        # Перезагружаем и отображаем данные после возможного добавления
        self.load_data()
        self.display_data()

    def edit_user(self):
        """Открывает диалог редактирования для выбранного пользователя."""
        log.info("Попытка открытия диалога редактирования пользователя")
        # Получаем ID выбранного пользователя
        user_id = self.get_selected_user_id()
        # Если пользователь не выбран, показываем предупреждение
        if user_id is None:
            messagebox.showwarning(
                "Редактирование", "Выберите пользователя для редактирования.")
            return

        log.info(f"Открытие диалога редактирования для User ID={user_id}")
        # Создаем и отображаем модальный диалог редактирования
        dialog = EditUserDialog(self, self.repository,
                                user_id, self.current_user_id)
        dialog.wait_window()  # Ждем закрытия диалога
        # Перезагружаем и отображаем данные после возможного редактирования
        self.load_data()
        self.display_data()

    def delete_user(self):
        """Удаляет выбранного пользователя с проверками безопасности."""
        log.info("Попытка удаления пользователя")
        # Получаем ID выбранного пользователя
        user_id = self.get_selected_user_id()
        # Если пользователь не выбран, выходим
        if user_id is None:
            messagebox.showwarning(
                "Удаление", "Выберите пользователя для удаления.")
            return

        # --- Проверки безопасности перед удалением ---
        # 1. Нельзя удалить себя
        if user_id == self.current_user_id:
            messagebox.showerror(
                "Ошибка удаления", "Вы не можете удалить свою учетную запись.")
            log.warning(
                f"Попытка само-удаления пользователем ID={self.current_user_id}")
            return
        # 2. Нельзя удалить последнего администратора
        user_role_id = self.repository.get_user_role_id(user_id)
        # Проверяем, является ли пользователь админом и единственным ли админом он является
        if user_role_id == self.admin_role_id:
            admin_count = self.repository.get_admin_count()
            if admin_count <= 1:
                messagebox.showerror(
                    "Ошибка удаления", "Нельзя удалить последнего администратора.")
                log.warning(
                    f"Попытка удаления последнего администратора (User ID={user_id})")
                return
        # --- Конец проверок ---

        # Получаем логин пользователя для окна подтверждения
        selected_login = ""
        selected_rows_indices = self.table.get_selected_rows(
            get_cells_as_rows=False)
        if selected_rows_indices:
            selected_row_index_in_view = list(selected_rows_indices)[0]
            # Получаем данные видимой строки
            # Теперь таблица включает ID, поэтому Login будет с индексом 1
            visible_row_data = self.table.get_row_data(
                selected_row_index_in_view)
            if visible_row_data and len(visible_row_data) > 1:
                # Логин - второй столбец видимой таблицы
                selected_login = visible_row_data[1]

        # Запрашиваем подтверждение у пользователя
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя '{selected_login}' (ID={user_id})?"):
            log.info(
                f"Подтверждено удаление User ID={user_id}, Login='{selected_login}'")
            # Выполняем удаление через репозиторий
            if self.repository.delete_user(user_id):
                messagebox.showinfo("Успех", "Пользователь удален.")
                log.info(f"User ID={user_id} удален.")
                # --- Корректировка пагинации и обновление таблицы ---
                current_total = self.total_rows  # Запоминаем старое общее количество
                # Перезагружаем данные с учетом текущего фильтра поиска
                self.load_data(search_term=self.search_entry.get().strip())
                new_total_pages = self.get_total_pages()  # Вычисляем новое кол-во страниц
                # Корректируем номер текущей страницы, если она стала недействительной
                if self.current_page > new_total_pages > 0:
                    self.current_page = new_total_pages
                elif current_total > 0 and self.total_rows == 0:  # Если удалили последнего
                    self.current_page = 1
                # Если удалили последнюю запись на странице (и это не первая страница)
                elif self.current_page > 1 and (current_total - 1) % self.rows_per_page == 0 and self.total_rows < current_total:
                    self.current_page -= 1
                # Отображаем данные на скорректированной странице
                self.display_data()
                # -------------------------------------------------
            else:
                # Если репозиторий вернул ошибку
                messagebox.showerror(
                    "Ошибка", "Не удалось удалить пользователя.")
                log.error(f"Ошибка удаления User ID={user_id}.")
        else:
            # Если пользователь нажал "Нет" в окне подтверждения
            log.info("Удаление пользователя отменено.")

    def import_users(self):
        """Открывает диалог импорта пользователей."""
        log.info("Открытие диалога импорта пользователей")
        # Создаем и отображаем модальный диалог импорта
        dialog = ImportUsersDialog(self, self.repository)
        dialog.wait_window()  # Ждем закрытия диалога
        # Перезагружаем и отображаем данные после возможного импорта
        self.load_data()
        self.display_data()

    def export_users(self):
        """Экспортирует данные пользователей (БЕЗ ПАРОЛЕЙ) в CSV и XML."""
        log.info("Экспорт данных пользователей")
        # Получаем ВСЕ данные пользователей, игнорируя UI поиск/пагинацию
        all_users_raw, total_count = self.repository.get_users(
            search_term=None)
        # Если данных нет, сообщаем и выходим
        if not all_users_raw:
            messagebox.showinfo("Экспорт", "Нет пользователей для экспорта.")
            log.info("Нет пользователей для экспорта")
            return

        # Готовим данные для экспорта: БЕЗ ID (индекс 0) и БЕЗ ХЕША ПАРОЛЯ (индекс 2)
        # Оставляем: Login(1), EmpInfo(3), Role(4), Email(5)
        all_users_export = [[row[1], row[3], row[4], row[5]]
                            for row in all_users_raw]

        # --- Логика создания файлов и записи (без изменений) ---
        export_dir = "export"
        now = datetime.datetime.now()
        date_dir = os.path.join(export_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(date_dir, exist_ok=True)
        timestamp = now.strftime("%H-%M-%S")
        base_filename = f"users_{timestamp}"
        csv_filename = os.path.join(date_dir, f"{base_filename}.csv")
        xml_filename = os.path.join(date_dir, f"{base_filename}.xml")

        headers_export = ["Login", "EmployeeInfo", "RoleName", "Email"]
        xml_keys_export = ["Login", "EmployeeInfo", "RoleName", "Email"]

        csv_success, xml_success = False, False
        # Экспорт в CSV
        try:
            with codecs.open(csv_filename, "w", "utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers_export)
                writer.writerows(all_users_export)
            log.info(f"Экспорт пользователей в CSV: {csv_filename}")
            csv_success = True
        except Exception as e:
            messagebox.showerror(
                "Ошибка CSV", f"Ошибка экспорта пользователей в CSV:\n{e}")
            log.exception(f"Ошибка экспорта пользователей в CSV")
        # Экспорт в XML
        try:
            root = ET.Element("Users")
            for row_data in all_users_export:
                user_elem = ET.SubElement(root, "User")
                for key, value in zip(xml_keys_export, row_data):
                    ET.SubElement(user_elem, key).text = str(
                        value) if value is not None else ""
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            log.info(f"Экспорт пользователей в XML: {xml_filename}")
            xml_success = True
        except Exception as e:
            messagebox.showerror(
                "Ошибка XML", f"Ошибка экспорта пользователей в XML:\n{e}")
            log.exception(f"Ошибка экспорта пользователей в XML")

        # Финальное сообщение
        if csv_success and xml_success:
            messagebox.showinfo(
                "Экспорт", f"Экспорт пользователей завершен:\n{csv_filename}\n{xml_filename}")
        elif csv_success:
            messagebox.showinfo(
                "Экспорт CSV", f"CSV готов.\n{csv_filename}\n(Ошибка XML)")
        elif xml_success:
            messagebox.showinfo(
                "Экспорт XML", f"XML готов.\n{xml_filename}\n(Ошибка CSV)")

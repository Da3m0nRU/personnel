# gui/main_window.py
"""
Модуль главного окна приложения АИС "Кадры".

Определяет класс `MainWindow`, который является основным контейнером
для пользовательского интерфейса после входа пользователя. Включает:
- Боковую панель навигации с кнопками для доступа к различным разделам.
- Область контента для отображения выбранного раздела (фрейма).
- Информацию о текущем пользователе и его роли.
- Управление доступом к разделам на основе роли пользователя.
- Экспериментальный RGB-режим для подсветки элементов интерфейса.
"""

import logging
import threading
import time
import colorsys
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from config import *  # Константы конфигурации
from db.database import Database
from db.user_repository import UserRepository
from db.role_repository import RoleRepository

# Импорт утилит и фреймов вкладок
from .utils import load_icon, relative_to_assets
from .dashboard_frame import DashboardFrame
from .employees_frame import EmployeesFrame
from .events_frame import EventsFrame
from .absences_frame import AbsencesFrame
from .reports_frame import ReportsFrame
from .users_frame import UsersFrame

log = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения АИС "Кадры".

    Отображает боковую панель навигации и основную область контента,
    где динамически загружаются различные фреймы (вкладки).
    Управляет доступом к вкладкам на основе роли вошедшего пользователя.
    Поддерживает переключение между вкладками и визуальное выделение активной.
    Реализует обработку закрытия окна и управление RGB-режимом.
    """

    def __init__(self, master: ctk.CTk, db: Database, user_data: dict):
        """
        Инициализирует главное окно приложения.

        Выполняет следующие шаги:
        1. Сохраняет данные текущего пользователя (ID, RoleID, Login).
        2. Инициализирует необходимые репозитории (User, Role).
        3. Определяет ID роли администратора и проверяет наличие данных пользователя.
           В случае отсутствия критических данных - прерывает инициализацию и закрывает приложение.
        4. Загружает отображаемую информацию о пользователе (Имя, Роль).
        5. Выполняет базовые настройки окна (размер, заголовок, цвет фона, обработчик закрытия).
        6. Загружает шрифты.
        7. Инициализирует атрибуты, связанные с RGB-режимом.
        8. Инициализирует атрибуты для хранения виджетов (кнопки, фреймы).
        9. Вызывает `create_widgets()` для создания элементов интерфейса.
        10. Отображает начальную вкладку (`DashboardFrame`).

        Args:
            master (ctk.CTk): Родительский виджет (корневое окно CustomTkinter).
            db (Database): Экземпляр для работы с базой данных.
            user_data (dict): Словарь с данными аутентифицированного пользователя.
                              Ожидаемая структура: {'user_id': int, 'role_id': int, 'login': str}.
        """
        super().__init__(master)
        self.master = master
        self.db = db

        # --- 1. Сохранение данных текущего пользователя ---
        self.current_user_id: int | None = user_data.get("user_id")
        self.current_user_role_id: int | None = user_data.get("role_id")
        self.current_user_login: str = user_data.get("login", "Неизвестный")
        log.info(f"Инициализация MainWindow: UserID={self.current_user_id}, "
                 f"RoleID={self.current_user_role_id}, Login='{self.current_user_login}'")

        # --- 2. Инициализация репозиториев ---
        self.user_repository = UserRepository(self.db)
        self.role_repository = RoleRepository(self.db)

        # --- 3. Получение ID администратора и проверка данных пользователя ---
        self.admin_role_id: int | None = self._get_role_id_safe(
            "Администратор")
        if self.current_user_id is None or self.current_user_role_id is None:
            log.critical(
                "Отсутствуют критически важные данные пользователя (ID или RoleID). Работа невозможна.")
            messagebox.showerror(
                "Критическая ошибка", "Ошибка данных пользователя. Приложение будет закрыто.")
            self.master.after(100, self.master.destroy)  # Отложенное закрытие
            return  # Прерываем инициализацию

        # --- 4. Загрузка отображаемой информации о пользователе (Имя, Роль) ---
        self.user_display_name: str = self.current_user_login
        self.user_display_role: str = "Неизвестная роль"
        self.load_user_display_info()

        # --- 5. Базовые настройки окна ---
        self.master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.master.title(
            f"АИС Кадры - {self.user_display_role}: {self.user_display_name}")
        self.configure(fg_color=MAIN_BG_COLOR)
        # Перехват события закрытия окна
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- 6. Шрифты ---
        self.default_font = DEFAULT_FONT
        self.bold_font = BOLD_FONT
        self.title_bold_font = TITLE_BOLD_FONT

        # --- 7. Атрибуты для RGB режима ---
        self.rgb_mode: bool = False
        self.rgb_thread: threading.Thread | None = None
        self.rgb_switch_var = ctk.BooleanVar(value=False)

        # --- 8. Инициализация атрибутов для виджетов ---
        self.buttons: list[ctk.CTkButton] = []  # Список кнопок навигации
        self.active_rectangle_label: ctk.CTkLabel | None = None  # Маркер активной кнопки
        self.content_frame: ctk.CTkFrame | None = None  # Контейнер для вкладок
        self.current_frame: ctk.CTkFrame | None = None  # Текущая отображаемая вкладка

        # --- 9. Создание виджетов интерфейса ---
        self.create_widgets()

        # --- 10. Отображение начальной вкладки (Главная) ---
        if self.content_frame:  # Убедимся, что content_frame создан
            self.button_click(0)
        else:
            log.error(
                "Content frame не был создан, начальная вкладка не отображена.")

    def _get_role_id_safe(self, role_name: str) -> int | None:
        """
        Безопасно получает ID роли по её названию из репозитория.

        Логирует ошибку и показывает сообщение пользователю в случае неудачи.

        Args:
            role_name (str): Название роли.

        Returns:
            int | None: ID роли или None, если роль не найдена или произошла ошибка.
        """
        try:
            role_id = self.role_repository.get_id_by_name(role_name)
            if role_id is None:
                log.error(
                    f"Роль '{role_name}' не найдена в базе данных! Проверьте таблицу Roles.")
            return role_id
        except Exception as e:
            log.critical(
                f"Критическая ошибка при получении ID роли '{role_name}': {e}", exc_info=True)
            messagebox.showerror("Критическая ошибка",
                                 f"Не удалось определить системную роль '{role_name}'.\n"
                                 f"Работа приложения может быть нарушена. Обратитесь к администратору.")
            return None

    def load_user_display_info(self):
        """
        Загружает и устанавливает отображаемое имя пользователя и его роль.

        Пытается получить имя роли по ID. Если пользователь связан с сотрудником,
        пытается сформировать краткое ФИО (Фамилия И.О.) для отображения.
        В случае ошибок использует логин и "Неизвестная роль".
        """
        log.debug("Загрузка отображаемой информации о пользователе (имя, роль)...")
        try:
            # Получаем имя роли
            if self.current_user_role_id is not None:
                role_name = self.role_repository.get_name_by_id(
                    self.current_user_role_id)
                if role_name:
                    self.user_display_role = role_name
                else:
                    log.warning(
                        f"Не найдено название для RoleID={self.current_user_role_id}. Используется 'Неизвестная роль'.")
            else:
                log.error("RoleID текущего пользователя не определен.")

            # Получаем ФИО связанного сотрудника (если есть)
            user_details = self.user_repository.get_user_by_id(
                self.current_user_id)
            if user_details and len(user_details) > 3:
                employee_pn = user_details[3]
                if employee_pn:
                    emp_info = self.db.fetch_one(
                        "SELECT LastName, FirstName, MiddleName FROM Employees WHERE PersonnelNumber = ?", (
                            employee_pn,)
                    )
                    if emp_info:
                        last, first, middle = emp_info
                        initial = f" {first[0]}." if first else ""
                        middle_initial = f"{middle[0]}." if middle else ""
                        # Формируем "Фамилия И.О." или "Фамилия И." или "Фамилия"
                        self.user_display_name = f"{last}{initial}{middle_initial}".strip(
                        )
                    else:
                        log.warning(
                            f"Не найден сотрудник с PN={employee_pn}, связанный с пользователем ID={self.current_user_id}. Используется логин.")
                        self.user_display_name = self.current_user_login  # Возврат к логину
                else:
                    # Пользователь не связан с сотрудником, используем логин
                    self.user_display_name = self.current_user_login
            else:
                # Не удалось получить детали пользователя или они неполные
                log.warning(
                    f"Не удалось получить детали пользователя ID={self.current_user_id} или они неполные. Используется логин.")
                self.user_display_name = self.current_user_login

            log.debug(
                f"Отображаемая информация: Имя='{self.user_display_name}', Роль='{self.user_display_role}'")

            # Обновляем заголовок окна после загрузки информации
            if self.master and self.master.winfo_exists():
                self.master.title(
                    f"АИС Кадры - {self.user_display_role}: {self.user_display_name}")

        except Exception as e:
            log.exception(
                f"Ошибка при загрузке отображаемой информации пользователя: {e}")
            # Оставляем значения по умолчанию (логин, "Неизвестная роль")

    def create_widgets(self):
        """
        Создает все виджеты главного окна:
        - Левую панель навигации.
        - Заголовок и логотип.
        - Кнопки навигации (с учетом роли пользователя).
        - Блок информации о пользователе с переключателем RGB.
        - Футер.
        - Основную область контента.
        """
        log.debug("Создание виджетов MainWindow...")

        # --- 1. Левая панель навигации (контейнер) ---
        left_frame = ctk.CTkFrame(self.master, fg_color=LEFT_PANEL_BG_COLOR,
                                  width=LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        # Запретить изменение размера от содержимого
        left_frame.pack_propagate(False)
        left_frame.pack(side="left", fill="y")

        # --- 2. Заголовок приложения и логотип ---
        title_label = ctk.CTkLabel(left_frame, text="Кадры", font=self.title_bold_font,
                                   text_color=BUTTON_TEXT_COLOR, anchor="nw", padx=62, pady=40)
        title_label.pack()
        self.title_label = title_label  # Сохраняем ссылку для RGB
        try:
            logo_img = Image.open(relative_to_assets("image_2.png"))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ctk.CTkLabel(
                left_frame, image=logo_photo, text="", bg_color="white")
            logo_label.image = logo_photo  # Сохраняем ссылку на изображение
            logo_label.place(x=28, y=40)
        except Exception as e:
            log.error(f"Не удалось загрузить логотип image_2.png: {e}")

        # --- 3. Подпись под заголовком ---
        subtitle_label = ctk.CTkLabel(left_frame, text="Автоматизированная Система\nУправления Кадрами",
                                      font=("Arial", 14), text_color="#B9BABD", anchor="nw", padx=62, pady=0)
        subtitle_label.pack()

        # --- 4. Кнопки меню навигации ---
        self.buttons.clear()  # Очищаем список перед созданием
        is_admin = (self.current_user_role_id == self.admin_role_id)
        log.debug(
            f"Создание кнопок меню. Пользователь администратор: {is_admin}")

        # Конфигурация кнопок: (Текст, Имя_иконки, Класс_фрейма, Нужен_ли_админ)
        button_configs = [
            ("Главная", "home.png", DashboardFrame, False),
            ("Сотрудники", "users.png", EmployeesFrame, False),
            ("Кадровые события", "edit.png", EventsFrame, False),
            ("Отсутствия", "list.png", AbsencesFrame, False),
            ("Отчеты", "chart-histogram.png", ReportsFrame, False),
            ("Пользователи", "user.png", UsersFrame, True),  # Только для админа
        ]

        button_y = BUTTON_Y_START
        for i, (text, icon_name, _, needs_admin) in enumerate(button_configs):
            if needs_admin and not is_admin:
                continue  # Пропускаем кнопку, если нет прав

            button = ctk.CTkButton(
                master=left_frame, text=f"  {text}", corner_radius=15,
                command=lambda index=i: self.button_click(
                    index),  # Используем индекс из конфига
                fg_color=BUTTON_BG_COLOR, bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                font=self.default_font, image=load_icon(icon_name), anchor="w"
            )
            button.place(x=BUTTON_X, y=button_y)
            self.buttons.append(button)  # Добавляем кнопку в список
            button_y += BUTTON_HEIGHT + BUTTON_Y_SPACING  # Сдвигаем Y для следующей кнопки

        # --- 5. Блок информации о пользователе и переключатель RGB ---
        user_info_y_pos = 880  # Примерная позиция Y
        user_info_frame = ctk.CTkFrame(left_frame, fg_color="transparent")

        user_info_frame.grid_columnconfigure(
            0, weight=0)  # Колонка для аватара
        # Колонка для имени/роли (растягиваемая)
        user_info_frame.grid_columnconfigure(1, weight=1)
        user_info_frame.grid_columnconfigure(
            2, weight=0)  # Колонка для переключателя
        user_info_frame.place(x=20, y=user_info_y_pos, anchor="nw")

        # Аватар
        try:
            # TODO: Использовать image_1.png?
            avatar_img = Image.open(relative_to_assets("user.png"))
            avatar_photo = ctk.CTkImage(avatar_img, size=AVATAR_SIZE)
            avatar_label = ctk.CTkLabel(
                user_info_frame, image=avatar_photo, text="")
            avatar_label.image = avatar_photo
            avatar_label.grid(row=0, column=0, rowspan=2,
                              padx=(0, 10), sticky="ns")
        except Exception as e:
            log.error(
                f"Не удалось загрузить аватар пользователя user.png: {e}")

        # Имя пользователя
        user_name_label = ctk.CTkLabel(user_info_frame, text=self.user_display_name, text_color=LABEL_TEXT_COLOR,
                                       font=("Arial", 16), anchor="nw")
        user_name_label.grid(row=0, column=1, sticky="nw", padx=5)

        # Роль пользователя
        user_access_label = ctk.CTkLabel(user_info_frame, text=self.user_display_role, text_color=ACCENT_COLOR,
                                         font=("Arial", 16), anchor="nw")
        user_access_label.grid(row=1, column=1, sticky="nw", padx=5)
        self.user_access_label = user_access_label  # Сохраняем ссылку для RGB

        # Переключатель RGB
        rgb_switch = ctk.CTkSwitch(user_info_frame, text="", command=self.toggle_rgb_mode,
                                   variable=self.rgb_switch_var, onvalue=True, offvalue=False,
                                   width=50)  # Явно задаем ширину
        rgb_switch.grid(row=0, column=2, rowspan=2, padx=(10, 0), sticky="e")

        # --- 6. Футер ---
        footer_text1 = ctk.CTkLabel(
            left_frame, text="Made by Victor", text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT)
        footer_text1.place(x=20, y=984)
        footer_text2 = ctk.CTkLabel(
            left_frame, text='АСУ "Кадры"\n© 2025 Все права защищены', text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT)
        footer_text2.place(x=150, y=984)

        # --- 7. Основная область контента (контейнер) ---
        content_frame = ctk.CTkFrame(self.master, fg_color=MAIN_BG_COLOR,
                                     width=WINDOW_WIDTH - LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        content_frame.pack_propagate(False)
        content_frame.pack(side="right", fill="both", expand=True)
        self.content_frame = content_frame  # Сохраняем ссылку

        log.debug("Виджеты MainWindow успешно созданы.")

    # --- Управление RGB режимом ---

    def start_rgb(self):
        """
        Запускает фоновый поток для анимации RGB-режима, если он еще не запущен.
        """
        log.debug("Запуск потока для RGB-режима...")
        if self.rgb_thread is None or not self.rgb_thread.is_alive():
            self.rgb_thread = threading.Thread(
                target=self.rgb_mode_loop, daemon=True)
            self.rgb_thread.start()
            log.debug("Поток RGB запущен.")
        else:
            log.debug("Поток RGB уже был запущен.")

    def toggle_rgb_mode(self):
        """
        Обрабатывает изменение состояния переключателя RGB.

        Обновляет флаг `self.rgb_mode`, запускает поток анимации при включении
        и восстанавливает стандартные цвета при выключении.
        """
        self.rgb_mode = self.rgb_switch_var.get()
        log.info(f"RGB-режим переключен: {self.rgb_mode}")
        if self.rgb_mode:
            self.start_rgb()
        else:
            # Немедленно восстанавливаем цвета при выключении
            self.restore_default_colors()

    def rgb_mode_loop(self):
        """
        Цикл анимации цветов в RGB-режиме.

        Выполняется в отдельном потоке (`self.rgb_thread`).
        Плавно изменяет цвет (hue) и планирует обновление UI
        в основном потоке с помощью `self.after()`.
        Прекращает работу, если `self.rgb_mode` становится False
        или окно перестает существовать.
        """
        hue = 0
        log.debug("Начало цикла анимации RGB.")
        while self.rgb_mode:
            # Проверяем, существует ли еще окно
            if not self.winfo_exists():
                log.debug("Окно больше не существует, остановка потока RGB.")
                self.rgb_mode = False  # Выходим из цикла
                break

            # Рассчитываем цвет
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(r * 255), int(g * 255), int(b * 255))

            try:
                # Планируем обновление UI в основном потоке
                self.after(0, self.update_rgb_colors, hex_color)
            except Exception as e:
                # Ошибка может возникнуть, если окно закрывается в момент вызова after
                log.error(
                    f"Ошибка планирования обновления цвета в потоке RGB: {e}")
                if not self.winfo_exists():  # Дополнительная проверка
                    self.rgb_mode = False
                    break

            # Обновляем hue и ждем
            hue = (hue + 5) % 360
            time.sleep(0.05)

        log.debug("Цикл RGB завершен.")
        # После завершения цикла (если окно еще существует) восстанавливаем цвета
        if self.winfo_exists():
            self.after(0, self.restore_default_colors)

    def update_rgb_colors(self, hex_color: str):
        """
        Обновляет цвета ключевых виджетов в соответствии с RGB-режимом.

        Вызывается из основного потока через `self.after()` из `rgb_mode_loop`.

        Args:
            hex_color (str): Новый цвет в формате HEX (#RRGGBB).
        """
        if not self.rgb_mode:  # Доп. проверка на случай гонки потоков
            return
        try:
            # Обновляем цвет заголовка
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.configure(text_color=hex_color)
            # Обновляем цвет роли пользователя
            if hasattr(self, 'user_access_label') and self.user_access_label.winfo_exists():
                self.user_access_label.configure(text_color=hex_color)
            # Обновляем цвет активного прямоугольника
            if self.active_rectangle_label and self.active_rectangle_label.winfo_exists():
                self.active_rectangle_label.configure(
                    fg_color=hex_color, bg_color=hex_color)
        except Exception as e:
            # Предотвращаем крах из-за возможного уничтожения виджета
            log.warning(
                f"Ошибка при обновлении RGB цветов (виджет мог быть удален): {e}")

    def restore_default_colors(self):
        """
        Восстанавливает стандартные цвета элементов интерфейса после отключения RGB.

        Вызывается либо при выключении переключателя, либо после завершения цикла `rgb_mode_loop`.
        Проверяет существование виджетов перед изменением их конфигурации.
        """
        if self.rgb_mode:  # Не восстанавливаем, если RGB все еще должен быть активен
            return
        log.debug("Восстановление стандартных цветов UI...")
        try:
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.configure(text_color=BUTTON_TEXT_COLOR)
            if hasattr(self, 'user_access_label') and self.user_access_label.winfo_exists():
                self.user_access_label.configure(text_color=ACCENT_COLOR)
            # Восстанавливаем цвет активного прямоугольника, если он есть
            if self.active_rectangle_label and self.active_rectangle_label.winfo_exists():
                self.active_rectangle_label.configure(
                    fg_color=ACCENT_COLOR, bg_color=ACCENT_COLOR)
            log.debug("Стандартные цвета успешно восстановлены.")
        except Exception as e:
            log.warning(
                f"Ошибка при восстановлении стандартных цветов (виджет мог быть удален): {e}")

    # --- Управление навигацией и отображением вкладок ---

    def button_click(self, button_index: int):
        """
        Обрабатывает нажатие на кнопку навигационного меню.

        1. Обновляет визуальное состояние кнопок (выделение активной).
        2. Создает/перемещает маркер активной кнопки (прямоугольник).
        3. Вызывает соответствующий метод для отображения нужного фрейма.

        Args:
            button_index (int): Индекс нажатой кнопки в исходном списке `button_configs`.
        """
        log.info(f"Нажата кнопка навигации с индексом: {button_index}")

        # --- 1. Обновление вида кнопок --- #
        # button_map определяет, какой реальной кнопке в self.buttons соответствует button_index
        is_admin = (self.current_user_role_id == self.admin_role_id)
        actual_button_index = -1
        current_actual_index = 0
        button_configs = [
            ("Главная", DashboardFrame, False),
            ("Сотрудники", EmployeesFrame, False),
            ("Кадровые события", EventsFrame, False),
            ("Отсутствия", AbsencesFrame, False),
            ("Отчеты", ReportsFrame, False),
            ("Пользователи", UsersFrame, True),  # Только для админа
        ]
        visible_buttons_mapping = {}
        for i, (_, _, needs_admin) in enumerate(button_configs):
            if not needs_admin or is_admin:
                visible_buttons_mapping[i] = current_actual_index
                if i == button_index:
                    actual_button_index = current_actual_index
                current_actual_index += 1

        if actual_button_index == -1:
            log.error(
                f"Не удалось найти соответствующую видимую кнопку для индекса {button_index}")
            return

        # Сброс состояния всех видимых кнопок и выделение активной
        for idx, button in enumerate(self.buttons):
            if idx == actual_button_index:
                button.configure(fg_color=BUTTON_ACTIVE_BG_COLOR,
                                 text_color=BUTTON_ACTIVE_TEXT_COLOR, hover_color=BUTTON_ACTIVE_BG_COLOR)
            else:
                button.configure(fg_color=BUTTON_BG_COLOR,
                                 text_color=BUTTON_TEXT_COLOR, hover_color=BUTTON_HOVER_COLOR)

        # --- 2. Обновление маркера активной кнопки --- #
        if self.active_rectangle_label:
            self.active_rectangle_label.destroy()

        # Рассчитываем Y позицию маркера для текущей активной кнопки
        rect_y = BUTTON_Y_START + actual_button_index * \
            (BUTTON_HEIGHT + BUTTON_Y_SPACING)
        rect_color = ACCENT_COLOR
        # Если RGB режим, берем текущий цвет из заголовка
        if self.rgb_mode and hasattr(self, 'title_label') and self.title_label.winfo_exists():
            try:
                rect_color = self.title_label.cget("text_color")
            except Exception as e:
                log.warning(f"Не удалось получить цвет для RGB маркера: {e}")

        self.active_rectangle_label = ctk.CTkLabel(self.buttons[actual_button_index].master,  # Родитель - left_frame
                                                   text="", fg_color=rect_color, bg_color=rect_color,
                                                   width=8, height=BUTTON_HEIGHT)
        self.active_rectangle_label.place(x=0, y=rect_y)

        # --- 3. Отображение соответствующего фрейма --- #
        frame_class_to_show = None
        args_for_frame = []
        if button_index < len(button_configs):
            _, frame_class, needs_admin = button_configs[button_index]
            if not needs_admin or is_admin:
                frame_class_to_show = frame_class
                # Если это UsersFrame, передаем ID текущего пользователя
                if frame_class is UsersFrame:
                    args_for_frame.append(self.current_user_id)
            else:
                log.warning(
                    f"Доступ к вкладке {button_index} запрещен для текущего пользователя.")
                self.clear_content_frame()
                error_label = ctk.CTkLabel(self.content_frame, text="Доступ запрещен", font=(
                    "Arial", 24), text_color="red")
                error_label.place(relx=0.5, rely=0.5, anchor="center")
                return  # Выход, чтобы не вызывать show_frame
        else:
            log.error(f"Некорректный индекс кнопки: {button_index}")
            return

        if frame_class_to_show:
            self.show_frame(frame_class_to_show, *args_for_frame)
        else:
            log.warning(
                f"Не удалось определить фрейм для отображения по индексу кнопки {button_index}")
            self.clear_content_frame()
            error_label = ctk.CTkLabel(self.content_frame, text="Ошибка загрузки вкладки", font=(
                "Arial", 24), text_color="red")
            error_label.place(relx=0.5, rely=0.5, anchor="center")

    def clear_content_frame(self):
        """
        Удаляет все виджеты из основной области контента (`self.content_frame`).
        """
        log.debug("Очистка области контента (content_frame)...")
        if hasattr(self, 'content_frame') and self.content_frame and self.content_frame.winfo_exists():
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            log.debug("Область контента очищена.")
        else:
            log.warning("Попытка очистить несуществующий content_frame.")
        self.current_frame = None  # Сбрасываем ссылку на текущий фрейм

    def show_frame(self, frame_class: type, *args):
        """
        Отображает экземпляр указанного класса фрейма в области контента.

        Сначала очищает область контента, затем создает и упаковывает
        новый экземпляр фрейма.
        Обрабатывает возможные ошибки при создании фрейма.

        Args:
            frame_class (type): Класс фрейма для отображения (например, `EmployeesFrame`).
            *args: Дополнительные позиционные аргументы, передаваемые в конструктор фрейма.
        """
        frame_name = frame_class.__name__
        log.info(
            f"Запрос на отображение фрейма: {frame_name} с аргументами: {args}")

        # Проверяем, не пытаемся ли мы отобразить тот же фрейм, что уже есть
        if self.current_frame is not None and isinstance(self.current_frame, frame_class):
            log.debug(
                f"Фрейм {frame_name} уже отображен. Обновление не требуется.")
            return

        # Проверяем существование content_frame
        if not hasattr(self, 'content_frame') or not self.content_frame or not self.content_frame.winfo_exists():
            log.error("Невозможно отобразить фрейм: content_frame не существует.")
            return

        self.clear_content_frame()
        try:
            # Создаем экземпляр нужного фрейма
            self.current_frame = frame_class(
                self.content_frame, self.db, *args)
            self.current_frame.pack(fill="both", expand=True)
            log.info(f"Фрейм {frame_name} успешно создан и отображен.")
        except Exception as e:
            log.exception(
                f"КРИТИЧЕСКАЯ ОШИБКА при создании/отображении фрейма {frame_name}: {e}")
            messagebox.showerror("Ошибка интерфейса",
                                 f"Не удалось загрузить вкладку '{frame_name}'.\n"
                                 f"Подробности в файле лога app.log.")
            # Показываем сообщение об ошибке в content_frame
            if self.content_frame.winfo_exists():
                error_label = ctk.CTkLabel(self.content_frame, text=f"Ошибка загрузки\n{frame_name}",
                                           font=("Arial", 18), text_color="red")
                error_label.place(relx=0.5, rely=0.5, anchor="center")

    # --- Метод закрытия окна ---

    def on_closing(self):
        """
        Обработчик события закрытия окна (нажатие на системный крестик).

        Показывает диалог подтверждения. Если пользователь подтверждает выход,
        останавливает поток RGB (если активен) и уничтожает главное окно.
        """
        log.info("Сработало событие закрытия окна (WM_DELETE_WINDOW).")
        if messagebox.askyesno("Выход из АИС Кадры", "Вы уверены, что хотите выйти из программы?"):
            log.info("Пользователь подтвердил выход. Завершение работы...")
            # Сигнализируем RGB потоку об остановке
            self.rgb_mode = False
            # Опционально: можно подождать немного, чтобы поток успел завершиться
            # if self.rgb_thread and self.rgb_thread.is_alive():
            #     time.sleep(0.1)
            # Закрываем соединение с БД, если оно открыто
            if self.db:
                self.db.close()
            # Уничтожаем главное окно Tkinter/CTk
            self.master.destroy()
        else:
            log.debug("Пользователь отменил выход из приложения.")

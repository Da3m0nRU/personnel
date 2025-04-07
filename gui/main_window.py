# gui/main_window.py
from tkinter import messagebox
from db.database import Database  # Для type hinting
import customtkinter as ctk
# Убираем неиспользуемые импорты tkinter
from PIL import Image, ImageTk
from .utils import load_icon, relative_to_assets  # Утилиты для иконок и путей
from config import *  # Константы конфигурации
import threading  # Для потока RGB
import time      # Для задержки в потоке RGB
import colorsys  # Для преобразования цветов HSV -> RGB
import logging   # Для логирования

# Импортируем классы наших вкладок (фреймов)
from .employees_frame import EmployeesFrame
from .absences_frame import AbsencesFrame
from .events_frame import EventsFrame
from .reports_frame import ReportsFrame
from .users_frame import UsersFrame
from .dashboard_frame import DashboardFrame

# Импортируем репозитории для получения данных о пользователе и ролях
from db.user_repository import UserRepository
# Убедимся, что RoleRepository импортирован
log = logging.getLogger(__name__)
try:
    from db.role_repository import RoleRepository
except ImportError:
    log.error("Не найден db.role_repository. Пожалуйста, создайте этот файл.")
    # Заглушка

    class RoleRepository:
        def __init__(self, db): pass

        def get_id_by_name(
            self, name): return 1 if name == "Администратор" else 2
        def get_name_by_id(
            self, id): return "Администратор" if id == 1 else "Неизвестно"


# Импортируем messagebox для сообщений об ошибках


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения АИС "Кадры".
    Отображает боковую панель навигации и область контента для различных вкладок.
    Управляет доступом к вкладкам на основе роли вошедшего пользователя.
    """

    def __init__(self, master: ctk.CTk, db: Database, user_data: dict):
        """
        Инициализирует главное окно приложения.

        Args:
            master (ctk.CTk): Родительский виджет (корневое окно CustomTkinter).
            db (Database): Экземпляр объекта для работы с базой данных.
            user_data (dict): Словарь с данными аутентифицированного пользователя.
                              Ожидаемая структура: {'user_id': int, 'role_id': int, 'login': str}.
        """
        super().__init__(master)
        self.master = master
        self.db = db

        # --- Сохраняем данные текущего пользователя ---
        self.current_user_id = user_data.get("user_id")
        self.current_user_role_id = user_data.get("role_id")
        self.current_user_login = user_data.get("login")
        # ---------------------------------------------
        log.info(
            f"Инициализация MainWindow для пользователя ID={self.current_user_id}, RoleID={self.current_user_role_id}, Login='{self.current_user_login}'")

        # --- Базовые настройки окна ---
        self.master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.master.title(
            f"АИС Кадры - Пользователь: {self.current_user_login}")
        self.configure(fg_color=MAIN_BG_COLOR)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        # -----------------------------

        # --- Инициализация репозиториев ---
        self.user_repository = UserRepository(self.db)
        self.role_repository = RoleRepository(self.db)
        # ---------------------------------

        # --- Получаем ID роли Админа ---
        self.admin_role_id = self._get_role_id_safe("Администратор")
        # ---------------------------------

        # --- Данные для отображения информации о пользователе ---
        self.user_display_name = self.current_user_login
        self.user_display_role = "Неизвестная роль"
        self.load_user_display_info()
        # ------------------------------------------------------

        # --- Шрифты ---
        self.default_font = DEFAULT_FONT
        self.bold_font = BOLD_FONT
        self.title_bold_font = TITLE_BOLD_FONT
        # --------------

        # --- Атрибуты для RGB режима ---
        self.rgb_mode = False
        self.rgb_thread = None
        # -----------------------------

        # --- Создание виджетов интерфейса ---
        self.create_widgets()
        # ---------------------------------

        # --- Управление текущей отображаемой вкладкой ---
        self.current_frame = None
        self.button_click(0)  # Отображаем начальную вкладку
        # ---------------------------------------------

    def _get_role_id_safe(self, role_name: str) -> int | None:
        """Безопасно получает ID роли по имени."""
        try:
            role_id = self.role_repository.get_id_by_name(role_name)
            if role_id is None:
                log.error(f"Роль '{role_name}' не найдена в базе данных!")
            return role_id
        except Exception as e:
            log.critical(
                f"Критическая ошибка при получении ID роли '{role_name}': {e}")
            messagebox.showerror(
                "Критическая ошибка", f"Не удалось определить роль '{role_name}'. Функционал может быть ограничен.")
            return None

    def load_user_display_info(self):
        """Загружает имя роли и ФИО сотрудника (если пользователь связан) для отображения в UI."""
        log.debug("Загрузка отображаемой информации о пользователе...")
        try:
            role_name = self.role_repository.get_name_by_id(
                self.current_user_role_id)
            if role_name:
                self.user_display_role = role_name
            else:
                log.warning(
                    f"Не найдено название для RoleID={self.current_user_role_id}")

            user_details = self.user_repository.get_user_by_id(
                self.current_user_id)
            employee_pn = user_details[3] if user_details and len(
                user_details) > 3 else None

            if employee_pn:
                emp_info = self.db.fetch_one(
                    "SELECT LastName, FirstName, MiddleName FROM Employees WHERE PersonnelNumber = ?", (
                        employee_pn,)
                )
                if emp_info:
                    last, first, middle = emp_info
                    initial = f"{first[0]}." if first else ""
                    middle_initial = f"{middle[0]}." if middle else ""
                    self.user_display_name = f"{last} {initial}{middle_initial}".strip(
                    )
                else:
                    log.warning(
                        f"Не найден сотрудник с PN={employee_pn}, связанный с пользователем ID={self.current_user_id}")
            log.debug(
                f"Информация для отображения: Имя='{self.user_display_name}', Роль='{self.user_display_role}'")

        except Exception as e:
            log.exception(
                f"Ошибка при загрузке отображаемой информации пользователя: {e}")

    def create_widgets(self):
        """Создает все виджеты главного окна."""
        log.debug("Начало создания виджетов MainWindow")

        # --- 1. Левая панель навигации ---
        self.left_frame = ctk.CTkFrame(
            self.master, fg_color=LEFT_PANEL_BG_COLOR, width=LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side="left", fill="y")

        # --- 2. Заголовок приложения и логотип ---
        self.title_label = ctk.CTkLabel(
            self.left_frame, text="Кадры", font=self.title_bold_font,
            text_color=BUTTON_TEXT_COLOR, anchor="nw", padx=62, pady=40
        )
        self.title_label.pack()
        try:
            image_image_2 = Image.open(relative_to_assets("image_2.png"))
            image_photo_2 = ImageTk.PhotoImage(image_image_2)
            self.image_label_2 = ctk.CTkLabel(
                self.left_frame, image=image_photo_2, text="", bg_color="white")
            self.image_label_2.image = image_photo_2
            self.image_label_2.place(x=28, y=40)
        except Exception as e:
            log.error(f"Не удалось загрузить логотип image_2.png: {e}")

        # --- 3. Подпись под заголовком ---
        self.subtitle_label = ctk.CTkLabel(
            self.left_frame, text="Автоматизированная Система\nУправления Кадрами",
            font=("Arial", 14), text_color="#B9BABD", anchor="nw", padx=62, pady=0
        )
        self.subtitle_label.pack()

        # --- 4. Кнопки меню навигации ---
        self.buttons = []
        self.active_rectangle_label = None
        is_admin = (self.current_user_role_id == self.admin_role_id)
        log.debug(f"Создание кнопок меню. Пользователь админ: {is_admin}")

        button_configs = [
            ("Главная", "home.png"),
            ("Сотрудники", "users.png"),
            ("Кадровые события", "edit.png"),
            ("Отсутствия", "list.png"),
            ("Отчеты", "chart-histogram.png"),
        ]
        if is_admin:
            button_configs.append(("Пользователи", "user.png"))

        for i, (text, icon_name) in enumerate(button_configs):
            button = ctk.CTkButton(
                master=self.left_frame, text=f"  {text}", corner_radius=15,
                command=lambda i=i: self.button_click(i),
                fg_color=BUTTON_BG_COLOR, bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                font=self.default_font, image=load_icon(icon_name), anchor="w"
            )
            button.place(x=BUTTON_X, y=BUTTON_Y_START + i *
                         (BUTTON_HEIGHT + BUTTON_Y_SPACING))
            self.buttons.append(button)

        # --- 5. Блок информации о пользователе и ПЕРЕКЛЮЧАТЕЛЬ RGB ---
        user_info_y_pos = 880  # Позиция Y для блока
        self.user_info_frame = ctk.CTkFrame(
            self.left_frame, fg_color="transparent")
        # Используем grid для размещения элементов внутри этого фрейма
        self.user_info_frame.grid_columnconfigure(0, weight=0)  # Аватар
        self.user_info_frame.grid_columnconfigure(
            1, weight=1)  # Имя/роль (может растягиваться)
        self.user_info_frame.grid_columnconfigure(2, weight=0)  # Переключатель
        self.user_info_frame.place(
            x=20, y=user_info_y_pos)  # Размещаем фрейм

        # Аватар (в первой колонке, занимает 2 строки)
        try:
            avatar_image = Image.open(relative_to_assets("user.png"))
            self.avatar_photo = ctk.CTkImage(avatar_image, size=AVATAR_SIZE)
            self.avatar_label = ctk.CTkLabel(
                self.user_info_frame, image=self.avatar_photo, text="")
            self.avatar_label.image = self.avatar_photo
            self.avatar_label.grid(
                row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")
        except Exception as e:
            log.error(f"Не удалось загрузить аватар image_1.png: {e}")

        # Имя пользователя (вторая колонка, первая строка)
        self.user_name_label = ctk.CTkLabel(
            self.user_info_frame, text=self.user_display_name, text_color=LABEL_TEXT_COLOR,
            font=("Arial", 16), anchor="nw")
        self.user_name_label.grid(row=0, column=1, sticky="nw", padx=5)

        # Роль пользователя (вторая колонка, вторая строка)
        self.user_access_label = ctk.CTkLabel(
            self.user_info_frame, text=self.user_display_role, text_color=ACCENT_COLOR,
            font=("Arial", 16), anchor="nw")
        self.user_access_label.grid(row=1, column=1, sticky="nw", padx=5)

        # Переключатель RGB (третья колонка, занимает 2 строки)
        # Переменная состояния переключателя
        self.rgb_switch_var = ctk.BooleanVar(value=False)
        self.rgb_switch = ctk.CTkSwitch(
            self.user_info_frame,  # Родитель - фрейм информации
            text="",  # Без текста рядом
            command=self.toggle_rgb_mode,
            variable=self.rgb_switch_var,
            onvalue=True,
            offvalue=False,
            width=50  # Явно задаем ширину
        )
        # Размещаем справа, выравниваем по правому краю
        self.rgb_switch.grid(row=0, column=2, rowspan=2,
                             padx=(10, 0), sticky="e")
        # ---------------------------------------------------------

        # --- 6. Футер ---
        footer_text1 = ctk.CTkLabel(
            self.left_frame, text="Made by Victor", text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT)
        footer_text1.place(x=20, y=984)
        footer_text2 = ctk.CTkLabel(
            self.left_frame, text="АСУ “Кадры”\n© 2025 Все права защищены", text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT)
        footer_text2.place(x=150, y=984)
        # ----------------

        # --- 7. Основная область контента ---
        self.content_frame = ctk.CTkFrame(
            self.master, fg_color=MAIN_BG_COLOR, width=WINDOW_WIDTH - LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        self.content_frame.pack_propagate(False)
        self.content_frame.pack(side="right", fill="both", expand=True)
        # -----------------------------------

        log.debug("Виджеты MainWindow созданы (с CTkSwitch для RGB)")

    def start_rgb(self):
        """Запускает отдельный поток для анимации RGB-режима."""
        log.debug("Запуск RGB-режима")
        if self.rgb_thread is None or not self.rgb_thread.is_alive():
            self.rgb_thread = threading.Thread(
                target=self.rgb_mode_loop, daemon=True)
            self.rgb_thread.start()
        else:
            log.debug("Поток RGB уже запущен.")

    def toggle_rgb_mode(self):
        """Обрабатывает переключение CTkSwitch RGB-режима."""
        # Получаем состояние из переменной переключателя
        self.rgb_mode = self.rgb_switch_var.get()
        log.debug(f"RGB-режим переключен через Switch: {self.rgb_mode}")
        if self.rgb_mode:
            self.start_rgb()
        else:
            # Если режим выключен, немедленно восстанавливаем цвета
            self.restore_default_colors()

    def rgb_mode_loop(self):
        """Цикл анимации цветов в RGB-режиме (выполняется в отдельном потоке)."""
        hue = 0
        log.debug("Начало цикла RGB.")
        while self.rgb_mode:
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(r * 255), int(g * 255), int(b * 255))
            try:
                if self.winfo_exists():
                    # Планируем обновление цветов в основном потоке
                    self.after(0, self.update_rgb_colors, hex_color)
            except Exception as e:
                log.error(
                    f"Ошибка планирования обновления цвета в потоке RGB: {e}")
                if not self.winfo_exists():
                    break
            hue = (hue + 5) % 360
            if not self.rgb_mode:
                break
            time.sleep(0.05)
        log.debug("Цикл RGB завершен.")
        # Планируем восстановление цветов после завершения цикла
        if self.winfo_exists():
            self.after(0, self.restore_default_colors)

    def update_rgb_colors(self, hex_color):
        """Обновляет цвета виджетов (вызывается из основного потока через self.after)."""
        try:
            if self.title_label.winfo_exists():
                self.title_label.configure(text_color=hex_color)
            if self.user_access_label.winfo_exists():
                self.user_access_label.configure(text_color=hex_color)
            # Обновляем цвет активного прямоугольника, если он есть
            if self.active_rectangle_label and self.active_rectangle_label.winfo_exists():
                self.active_rectangle_label.configure(
                    fg_color=hex_color, bg_color=hex_color)
        except Exception as e:
            log.warning(
                f"Ошибка при обновлении RGB цветов в основном потоке: {e}")

    def restore_default_colors(self):
        """Восстанавливает стандартные цвета элементов после отключения RGB."""
        # Эта функция вызывается либо при выключении режима, либо после завершения потока
        if not self.rgb_mode:  # Дополнительная проверка
            try:
                if self.title_label.winfo_exists():
                    self.title_label.configure(text_color=BUTTON_TEXT_COLOR)
                if self.user_access_label.winfo_exists():
                    self.user_access_label.configure(text_color=ACCENT_COLOR)
                if self.active_rectangle_label and self.active_rectangle_label.winfo_exists():
                    self.active_rectangle_label.configure(
                        fg_color=ACCENT_COLOR, bg_color=ACCENT_COLOR)
                log.debug("Стандартные цвета восстановлены.")
            except Exception as e:
                log.warning(
                    f"Ошибка при окончательном восстановлении цветов: {e}")

    def button_click(self, button_number):
        """Обрабатывает нажатие на кнопку навигационного меню."""
        log.debug(f"Нажата кнопка меню #{button_number}")
        # Обновление вида кнопок
        if self.active_rectangle_label:
            self.active_rectangle_label.destroy()
            self.active_rectangle_label = None
        active_button_index = -1
        for i, button in enumerate(self.buttons):
            if i == button_number:
                button.configure(fg_color=BUTTON_ACTIVE_BG_COLOR,
                                 text_color=BUTTON_ACTIVE_TEXT_COLOR, hover_color=BUTTON_ACTIVE_BG_COLOR)
                active_button_index = i
            else:
                button.configure(
                    fg_color=BUTTON_BG_COLOR, text_color=BUTTON_TEXT_COLOR, hover_color=BUTTON_HOVER_COLOR)
        if active_button_index != -1:
            rect_y = BUTTON_Y_START + active_button_index * \
                (BUTTON_HEIGHT + BUTTON_Y_SPACING)
            rect_color = ACCENT_COLOR
            if self.rgb_mode:
                try:
                    rect_color = self.title_label.cget("text_color")
                except:
                    pass
            self.active_rectangle_label = ctk.CTkLabel(
                self.left_frame, text="", fg_color=rect_color, bg_color=rect_color, width=8, height=BUTTON_HEIGHT)
            self.active_rectangle_label.place(x=0, y=rect_y)

        # Отображение нужной вкладки
        is_admin = (self.current_user_role_id == self.admin_role_id)
        users_button_index = 5 if is_admin else -1

        if button_number == 0:
            self.show_dashboard()
        elif button_number == 1:
            self.show_employees()
        elif button_number == 2:
            self.show_events()
        elif button_number == 3:
            self.show_absences()
        elif button_number == 4:
            self.show_reports()
        elif button_number == users_button_index and is_admin:
            self.show_users()
        else:
            log.warning(
                f"Неизвестный индекс кнопки или кнопка недоступна: {button_number}")
            self.clear_content_frame()
            ctk.CTkLabel(self.content_frame, text="Недоступно", font=(
                "Arial", 24)).place(relx=0.5, rely=0.5, anchor="center")

    def clear_content_frame(self):
        """Очищает область контента."""
        log.debug("Очистка области контента")
        if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        self.current_frame = None

    def show_frame(self, frame_class, *args):
        """
        Отображает экземпляр указанного класса фрейма в области контента.
        Args:
            frame_class (type): Класс фрейма для отображения.
            *args: Дополнительные позиционные аргументы для конструктора фрейма.
        """
        log.debug(
            f"Попытка отображения фрейма: {frame_class.__name__} с аргументами: {args}")
        if self.current_frame is not None and isinstance(self.current_frame, frame_class):
            log.debug("Фрейм того же типа уже отображен.")
            return

        self.clear_content_frame()
        try:
            self.current_frame = frame_class(
                self.content_frame, self.db, *args)
            self.current_frame.pack(fill="both", expand=True)
            log.debug(
                f"Фрейм {frame_class.__name__} успешно создан и отображен.")
        except Exception as e:
            log.exception(
                f"Критическая ошибка при создании экземпляра фрейма {frame_class.__name__}: {e}")
            messagebox.showerror(
                "Ошибка интерфейса", f"Не удалось загрузить вкладку '{frame_class.__name__}'.\nСм. лог app.log для деталей.")
            if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
                ctk.CTkLabel(self.content_frame, text=f"Ошибка загрузки\n{frame_class.__name__}", font=(
                    "Arial", 18), text_color="red").place(relx=0.5, rely=0.5, anchor="center")

    # --- Методы отображения вкладок ---

    def show_dashboard(self):
        log.info("Переход на вкладку 'Главная'")
        self.show_frame(DashboardFrame)  # Без доп. аргументов

    def show_employees(self):
        log.info("Переход на вкладку 'Сотрудники'")
        self.show_frame(EmployeesFrame)  # Без доп. аргументов

    def show_events(self):
        log.info("Переход на вкладку 'Кадровые события'")
        self.show_frame(EventsFrame)  # Без доп. аргументов

    def show_absences(self):
        log.info("Переход на вкладку 'Отсутствия'")
        self.show_frame(AbsencesFrame)  # Без доп. аргументов

    def show_reports(self):
        log.info("Переход на вкладку 'Отчеты'")
        self.show_frame(ReportsFrame)  # Без доп. аргументов

    def show_users(self):
        """Отображает вкладку 'Пользователи', если есть права (Администратор)."""
        log.info("Попытка перехода на вкладку 'Пользователи'")
        if self.current_user_role_id == self.admin_role_id:
            log.info("Доступ к Управлению Пользователями разрешен.")
            # Передаем ID админа
            self.show_frame(UsersFrame, self.current_user_id)
        else:
            log.warning(
                f"Доступ к Управлению Пользователями запрещен для пользователя ID={self.current_user_id} (Роль ID={self.current_user_role_id}).")
            self.clear_content_frame()
            error_label = ctk.CTkLabel(self.content_frame, text="Доступ запрещен", font=(
                "Arial", 24), text_color="red")
            error_label.place(relx=0.5, rely=0.5, anchor="center")
    # ---------------------------------

    def on_closing(self):
        """Обработчик события закрытия окна (нажатие на крестик)."""
        log.info("Запрос на закрытие приложения.")
        if messagebox.askyesno("Выход из приложения", "Вы уверены, что хотите закрыть программу?"):
            log.info("Подтверждено закрытие приложения, уничтожение окна.")
            # Перед закрытием можно остановить RGB поток, если он активен
            self.rgb_mode = False  # Сигнал потоку на остановку
            # Даем потоку немного времени завершиться (опционально)
            # if self.rgb_thread and self.rgb_thread.is_alive():
            #     time.sleep(0.1)
            self.master.destroy()  # Закрываем основное окно CTk
        else:
            log.debug("Закрытие приложения отменено пользователем.")

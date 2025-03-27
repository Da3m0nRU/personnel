# gui/main_window.py
import customtkinter as ctk
from tkinter import Label, PhotoImage
from PIL import Image, ImageTk
from .utils import load_icon, relative_to_assets
from config import *
import random
import threading
import time
import colorsys
import logging

# Импортируем классы наших вкладок
from .employees_frame import EmployeesFrame
# from .absences_frame import AbsencesFrame
from .events_frame import EventsFrame
# from .reports_frame import ReportsFrame
# from .users_frame import UsersFrame
# from .dashboard_frame import DashboardFrame

log = logging.getLogger(__name__)  # !!!


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения.

    Содержит левую панель с кнопками навигации и область контента
    для отображения вкладок (фреймов).
    """

    def __init__(self, master, db):
        """
        Инициализирует главное окно.

        Args:
            master (ctk.CTk):  Родительский виджет (обычно корневое окно Tk).
            db (Database): Объект базы данных.
        """
        super().__init__(master)
        self.master = master
        self.db = db
        self.master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.master.title("АИС Кадры")
        # self.master.resizable(False, False)  # Раскомментируйте, если не нужно изменять размер
        self.configure(fg_color=MAIN_BG_COLOR)
        log.debug("Инициализировано главное окно")  # !!!

        # --- Шрифты ---
        #  Используем шрифты из config.py
        self.default_font = DEFAULT_FONT
        self.bold_font = BOLD_FONT
        self.title_bold_font = TITLE_BOLD_FONT

        self.rgb_mode = False  # Флаг RGB-режима
        self.rgb_thread = None  # Поток для RGB-режима

        self.create_widgets()
        self.current_frame = None  # !!! Добавляем атрибут для хранения текущего фрейма

    def create_widgets(self):
        """
        Создает виджеты главного окна.
        """
        log.debug("Начало создания виджетов")  # !!!
        # --- Левая панель (белая) ---
        self.left_frame = ctk.CTkFrame(
            self.master, fg_color=LEFT_PANEL_BG_COLOR, width=LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        self.left_frame.pack_propagate(False)  # Чтобы фрейм не сжимался
        self.left_frame.pack(side="left", fill="y")

        # --- "Кадры" (заголовок) ---
        self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="Кадры",
            font=self.title_bold_font,
            text_color=BUTTON_TEXT_COLOR,  # Используем цвет из конфига
            anchor="nw",
            padx=62,
            pady=40,
        )
        self.title_label.pack()

        # --- Иконка (логотип) ---
        image_image_2 = Image.open(relative_to_assets("image_2.png"))
        image_photo_2 = ImageTk.PhotoImage(image_image_2)
        self.image_label_2 = ctk.CTkLabel(
            self.left_frame, image=image_photo_2, text="", bg_color="white")  # !!!  text=""
        self.image_label_2.image = image_photo_2  # !!!  Сохраняем ссылку
        self.image_label_2.place(x=28, y=40)

        # --- Подпись ---
        self.subtitle_label = ctk.CTkLabel(
            self.left_frame,
            text="Автоматизированная Система\nУправления Кадрами",
            font=("Arial", 14),
            text_color="#B9BABD",
            anchor="nw",
            padx=62,
            pady=0,
        )
        self.subtitle_label.pack()

        # --- Кнопки меню (CustomTkinter) ---
        self.buttons = []  # Список для хранения кнопок
        self.active_rectangle_label = None  # Для отслеживания активной кнопки

        button_configs = [
            ("Главная", "home.png", self.show_dashboard),
            ("Сотрудники", "users.png", self.show_employees),
            ("Кадровые события", "edit.png", self.show_events),
            ("Отсутствия", "list.png", self.show_absences),
            ("Отчеты", "chart-histogram.png", self.show_reports),
            ("Пользователи", "user.png", self.show_users),
        ]

        for i, (text, icon_name, command) in enumerate(button_configs):
            button = ctk.CTkButton(
                master=self.left_frame,
                text=text,
                corner_radius=15,
                command=lambda i=i: self.button_click(i),  # Используем лямбду
                fg_color=BUTTON_BG_COLOR,
                bg_color=BUTTON_BG_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                width=BUTTON_WIDTH,  # Используем константы
                height=BUTTON_HEIGHT,
                font=self.default_font,
                image=load_icon(icon_name),  # Загружаем иконку
                anchor="w"  # Выравнивание текста по левому краю
            )
            button.place(x=BUTTON_X, y=BUTTON_Y_START +
                         i * (BUTTON_HEIGHT + BUTTON_Y_SPACING))
            self.buttons.append(button)  # Добавляем кнопку в список

        # --- Информация о пользователе ---
        self.user_info_frame = ctk.CTkFrame(
            self.left_frame, fg_color="transparent")
        self.user_info_frame.place(x=20, y=900)  # !!!

        avatar_image = Image.open(relative_to_assets("image_1.png"))
        #  Используем CTkImage
        self.avatar_photo = ctk.CTkImage(avatar_image, size=AVATAR_SIZE)
        self.avatar_label = ctk.CTkLabel(  # !!! CTkLabel
            self.user_info_frame,
            image=self.avatar_photo,
            text="",  # !!!
        )
        self.avatar_label.image = self.avatar_photo
        # !!! pack, выравниваем по левому краю
        self.avatar_label.pack(side="left", padx=(0, 10))

        self.name_role_frame = ctk.CTkFrame(
            self.user_info_frame, fg_color="transparent")  # Создаём фрейм
        self.name_role_frame.pack(side="right")  # !!!

        self.user_name_label = ctk.CTkLabel(
            self.name_role_frame,  # !!!
            text=DEFAULT_USERNAME,
            text_color=LABEL_TEXT_COLOR,  # !!!
            font=("Arial", 16),
            anchor="nw",
        )
        self.user_name_label.pack(anchor="nw")  # !!!
        self.user_access_label = ctk.CTkLabel(
            self.name_role_frame,  # !!!
            text=DEFAULT_USER_ROLE,
            text_color=ACCENT_COLOR,
            font=("Arial", 16),
            anchor="nw"
        )
        self.user_access_label.pack(anchor="nw")  # !!!

        # --- Футер ---
        footer_text1 = ctk.CTkLabel(
            self.left_frame, text="Made by Victor", text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT)
        footer_text1.place(x=20, y=984)

        footer_text2 = ctk.CTkLabel(
            self.left_frame, text="АСУ “Кадры”\n© 2025 Все права защищены", text_color=FOOTER_TEXT_COLOR, font=FOOTER_FONT
        )
        footer_text2.place(x=150, y=984)

        # --- Рамка контента ---
        self.content_frame = ctk.CTkFrame(
            self.master, fg_color=MAIN_BG_COLOR, width=WINDOW_WIDTH - LEFT_PANEL_WIDTH, height=WINDOW_HEIGHT)
        self.content_frame.pack_propagate(False)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # --- Чекбокс RGB-режима ---
        self.rgb_checkbox = ctk.CTkCheckBox(
            self.left_frame,
            text_color=BUTTON_TEXT_COLOR,  # !!!
            text="RGB Режим",
            command=self.toggle_rgb_mode,
            onvalue=True,
            offvalue=False,
            checkbox_width=18,  # !!!  Размеры
            checkbox_height=18
        )
        self.rgb_checkbox.place(x=20, y=850)
        log.debug("Виджеты созданы")  # !!!

    def start_rgb(self):
        """
        Запускает поток для RGB-режима.
        """
        log.debug("Запуск RGB-режима")   # !!!
        self.rgb_thread = threading.Thread(target=self.rgb_mode_loop)
        self.rgb_thread.daemon = True  # Чтобы поток завершился при закрытии
        self.rgb_thread.start()

    def button_click(self, button_number):
        """
        Обрабатывает нажатие на кнопку меню.

        Args:
            button_number (int): Индекс нажатой кнопки (начиная с 0).
        """
        log.debug(f"Нажата кнопка меню #{button_number}")  # !!!
        #  Сначала удаляем "прямоугольник", если он есть
        if self.active_rectangle_label:
            self.active_rectangle_label.destroy()
        #  Меняем цвет для всех кнопок
        for i, button in enumerate(self.buttons):
            button.configure(fg_color=BUTTON_BG_COLOR,
                             text_color=BUTTON_TEXT_COLOR, hover_color=BUTTON_HOVER_COLOR)

        #  Меняем цвет и ставим "прямоугольник" для нажатой
        self.buttons[button_number].configure(
            fg_color=BUTTON_ACTIVE_BG_COLOR, text_color=BUTTON_ACTIVE_TEXT_COLOR, hover_color=BUTTON_ACTIVE_BG_COLOR
        )

        self.active_rectangle_label = ctk.CTkLabel(
            self.left_frame,
            text="",
            fg_color=ACCENT_COLOR,  # !!!
            bg_color=ACCENT_COLOR,
            width=8,
            height=54
        )

        self.active_rectangle_label.place(
            x=0,  # !!!
            y=180.0 + button_number * (54 + 15)
        )

        # Вызываем метод для отображения нужной вкладки
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
        elif button_number == 5:
            self.show_users()

    def toggle_rgb_mode(self):
        """
        Включает/выключает RGB-режим.
        """
        self.rgb_mode = not self.rgb_mode
        log.debug(f"RGB-режим: {self.rgb_mode}")  # !!!
        if self.rgb_mode:
            self.start_rgb()  # запускаем, если врубили
        else:
            # Возвращаем обычные цвета
            self.title_label.configure(text_color=BUTTON_TEXT_COLOR)  # !!!
            self.user_access_label.configure(text_color=ACCENT_COLOR)

    def rgb_mode_loop(self):
        """
        Цикл для изменения цветов в RGB-режиме.
        """
        hue = 0  # Начинаем с красного (hue = 0)
        while self.rgb_mode:
            #  Конвертируем HSV в RGB (значения от 0.0 до 1.0)
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
            #  Переводим RGB в шестнадцатеричный формат (#RRGGBB)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(r * 255), int(g * 255), int(b * 255))

            self.title_label.configure(text_color=hex_color)
            self.user_access_label.configure(text_color=hex_color)

            hue += 5  # Увеличиваем тон (скорость изменения цвета)
            if hue > 360:
                hue = 0  # Сбрасываем, чтобы начать сначала

            time.sleep(0.05)  # Задержка (скорость переливания)

    def clear_content_frame(self):
        """
        Очищает область контента (удаляет все виджеты).
        """
        log.debug("Очистка области контента")  # !!!
        # Удаляем все виджеты из content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_frame(self, frame_class):
        """
        Отображает указанный фрейм в области контента.

        Args:
            frame_class (class): Класс фрейма, который нужно отобразить.
        """
        log.debug(f"Отображение фрейма: {frame_class.__name__}")  # !!!
        # Сначала удаляем текущий фрейм, если он есть
        if self.current_frame is not None and isinstance(self.current_frame, frame_class):
            return  # Уже на этой вкладке

        if self.current_frame is not None:
            self.current_frame.destroy()
        # Создаем новый фрейм
        self.current_frame = frame_class(self.content_frame, self.db)
        self.current_frame.pack(fill="both", expand=True)

    # --- Методы для отображения вкладок ---
    def show_dashboard(self):
        """Отображает вкладку 'Главная'."""
        log.info("Переход на вкладку 'Главная'")  # !!!
        # self.show_frame(DashboardFrame)  # раскомментировал

    def show_employees(self):
        """Отображает вкладку 'Сотрудники'."""
        log.info("Переход на вкладку 'Сотрудники'")   # !!!
        self.show_frame(EmployeesFrame)

    def show_events(self):
        """Отображает вкладку 'Кадровые события'."""
        log.info("Переход на вкладку 'Кадровые события'")
        self.show_frame(EventsFrame)

    def show_absences(self):
        """Отображает вкладку 'Отсутствия'."""
        log.info("Переход на вкладку 'Отсутствия'")    # !!!
        # self.show_frame(AbsencesFrame)  # раскомментировал

    def show_reports(self):
        """Отображает вкладку 'Отчеты'."""
        log.info("Переход на вкладку 'Отчеты'")   # !!!
        # self.show_frame(ReportsFrame)  # раскомментировал

    def show_users(self):
        """Отображает вкладку 'Пользователи'."""
        log.info("Переход на вкладку 'Пользователи'")  # !!!
        # self.show_frame(UsersFrame)  # раскомментировал

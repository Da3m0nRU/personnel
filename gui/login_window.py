# gui/login_window.py
import customtkinter as ctk
from tkinter import messagebox
import logging
from db.user_repository import UserRepository
# Импортируем цвета, шрифты и утилиты
from config import *  # MAIN_BG_COLOR, LEFT_PANEL_BG_COLOR, LABEL_TEXT_COLOR, BUTTON_TEXT_COLOR, ACCENT_COLOR, DEFAULT_FONT, BOLD_FONT, BUTTON_HOVER_COLOR
from .utils import load_icon, relative_to_assets
from PIL import Image  # Нужен PIL для загрузки логотипа

log = logging.getLogger(__name__)


class LoginWindow(ctk.CTk):
    """Окно входа в систему с улучшенным UI."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.logged_in_user_data = None

        self.title("АИС Кадры - Вход")
        # --- Настройки окна ---
        window_width = 450
        window_height = 550
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.resizable(False, False)
        # Устанавливаем основной цвет фона окна
        self.configure(fg_color=MAIN_BG_COLOR)
        # ----------------------

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты окна входа с улучшенным дизайном."""

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True, padx=30, pady=30)

        # --- Логотип ---
        try:
            logo_image = Image.open(relative_to_assets("image_2.png"))
            logo_ctk = ctk.CTkImage(logo_image, size=(64, 64))
            logo_label = ctk.CTkLabel(center_frame, image=logo_ctk, text="")
            logo_label.pack(pady=(0, 15))
        except Exception as e:
            log.error(f"Не удалось загрузить логотип для окна входа: {e}")
        # ---------------

        title_label = ctk.CTkLabel(center_frame, text="Вход в АИС Кадры",
                                   font=("Arial", 26, "bold"),
                                   text_color=LABEL_TEXT_COLOR)  # Цвет заголовка
        title_label.pack(pady=(0, 25))

        # --- Фрейм для полей ввода и кнопки ---
        form_frame = ctk.CTkFrame(center_frame, fg_color=LEFT_PANEL_BG_COLOR,  # Белый фон
                                  corner_radius=15)
        form_frame.pack(fill="x", padx=10, pady=10)
        # ---------------------------------------

        # --- Поле Логин ---
        login_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        login_frame.pack(fill="x", padx=25, pady=(25, 10))

        login_icon = load_icon("user.png", size=(20, 20))
        ctk.CTkLabel(login_frame, image=login_icon,
                     text="").pack(side="left", padx=(0, 8))
        # Устанавливаем цвет метки Логин
        ctk.CTkLabel(login_frame, text="Логин:", font=DEFAULT_FONT,
                     text_color=BUTTON_TEXT_COLOR).pack(side="left")

        # Настраиваем цвета поля ввода Логин
        self.login_entry = ctk.CTkEntry(form_frame, font=DEFAULT_FONT, width=300, height=35,
                                        placeholder_text="Введите ваш логин",
                                        fg_color="white",  # Фон поля ввода
                                        text_color=BUTTON_TEXT_COLOR,  # Цвет текста в поле
                                        border_color="#D0D0D0",  # Цвет рамки
                                        placeholder_text_color="gray")  # Цвет placeholder'а
        self.login_entry.pack(fill="x", padx=25, pady=(0, 15))
        self.login_entry.focus()
        # --------------------

        # --- Поле Пароль ---
        password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=25, pady=(10, 10))

        pw_icon = load_icon("lock.png", size=(20, 20))
        ctk.CTkLabel(password_frame, image=pw_icon,
                     text="").pack(side="left", padx=(0, 8))
        # Устанавливаем цвет метки Пароль
        ctk.CTkLabel(password_frame, text="Пароль:", font=DEFAULT_FONT,
                     text_color=BUTTON_TEXT_COLOR).pack(side="left")

        # Настраиваем цвета поля ввода Пароль
        self.password_entry = ctk.CTkEntry(form_frame, font=DEFAULT_FONT, show="*", width=300, height=35,
                                           placeholder_text="Введите ваш пароль",
                                           fg_color="white",  # Фон поля ввода
                                           text_color=BUTTON_TEXT_COLOR,  # Цвет текста в поле
                                           border_color="#D0D0D0",  # Цвет рамки
                                           placeholder_text_color="gray")  # Цвет placeholder'а
        self.password_entry.pack(fill="x", padx=25, pady=(0, 15))
        self.password_entry.bind("<Return>", self.attempt_login)
        # -------------------

        # --- Метка для вывода ошибок ---
        self.error_label = ctk.CTkLabel(form_frame, text="", text_color="#FF4136",  # Ярко-красный для ошибок
                                        # Сделаем жирным
                                        font=("Arial", 13, "bold"),
                                        wraplength=300)
        self.error_label.pack(pady=(0, 10), padx=25)
        # ----------------------------

        # --- Кнопка "Войти" ---
        login_button = ctk.CTkButton(
            form_frame, text="Войти", font=BOLD_FONT, command=self.attempt_login,
            width=200, height=45,
            fg_color=ACCENT_COLOR,
            hover_color="#008a5a",
            text_color="white",  # Белый текст на кнопке
            corner_radius=10
        )
        login_button.pack(pady=(10, 20))
        # ---------------------

        # --- Кнопка "Выход" ---
        exit_button = ctk.CTkButton(
            center_frame,
            text="Выход из приложения",
            font=DEFAULT_FONT, command=self.on_closing,
            width=200, height=35,
            fg_color="transparent",
            text_color="gray",
            hover_color=MAIN_BG_COLOR  # Фон окна при наведении
        )
        exit_button.pack(pady=(15, 0))
        # ----------------------

    def attempt_login(self, event=None):
        """Пытается аутентифицировать пользователя."""
        login = self.login_entry.get().strip()
        password = self.password_entry.get()
        self.error_label.configure(text="")

        if not login or not password:
            self.error_label.configure(
                text="Пожалуйста, введите логин и пароль.")
            log.warning("Попытка входа с пустыми полями.")
            return

        log.info(f"Попытка входа пользователя: '{login}'")
        user_data = self.user_repository.get_user_by_login(login)

        if user_data:
            user_id, stored_hash, role_id = user_data
            if self.user_repository.verify_password(password, stored_hash):
                log.info(
                    f"Успешный вход пользователя: '{login}' (ID: {user_id}, RoleID: {role_id})")
                self.logged_in_user_data = {
                    "user_id": user_id, "role_id": role_id, "login": login}
                self.destroy()
            else:
                log.warning(f"Неверный пароль для пользователя: '{login}'")
                self.error_label.configure(text="Неверный логин или пароль.")
                self.password_entry.delete(0, "end")
        else:
            log.warning(f"Пользователь не найден: '{login}'")
            self.error_label.configure(text="Неверный логин или пароль.")
            self.password_entry.delete(0, "end")

    def on_closing(self):
        """Обработчик закрытия окна."""
        log.info("Окно входа закрывается.")
        self.destroy()

# gui/login_window.py
import customtkinter as ctk
from tkinter import messagebox
import logging
from db.user_repository import UserRepository  # Нужен для проверки пароля
# Импорт констант
from config import DEFAULT_FONT, BOLD_FONT, ACCENT_COLOR, BUTTON_HOVER_COLOR

log = logging.getLogger(__name__)


class LoginWindow(ctk.CTk):
    """Окно входа в систему."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.logged_in_user_data = None  # Для хранения данных после успешного входа

        self.title("АИС Кадры - Вход")
        # Определим размер окна входа
        window_width = 400
        window_height = 450
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.resizable(False, False)

        # Обработчик закрытия окна крестиком
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты окна входа."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, padx=40, pady=40)

        title_label = ctk.CTkLabel(main_frame, text="Вход в систему", font=(
            "Arial", 28, "bold"), text_color=ACCENT_COLOR)
        title_label.pack(pady=(0, 30))

        # Логин
        ctk.CTkLabel(main_frame, text="Логин:",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.login_entry = ctk.CTkEntry(
            main_frame, font=DEFAULT_FONT, width=300)
        self.login_entry.pack(fill="x", pady=(5, 15))
        self.login_entry.focus()  # Установить фокус на поле логина

        # Пароль
        ctk.CTkLabel(main_frame, text="Пароль:",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.password_entry = ctk.CTkEntry(
            main_frame, font=DEFAULT_FONT, show="*", width=300)
        self.password_entry.pack(fill="x", pady=(5, 25))
        # Привязка Enter к попытке входа
        self.password_entry.bind("<Return>", self.attempt_login)

        # Метка для ошибок
        self.error_label = ctk.CTkLabel(
            main_frame, text="", text_color="red", font=("Arial", 12))
        self.error_label.pack(pady=(0, 10))

        # Кнопка "Войти"
        login_button = ctk.CTkButton(
            main_frame, text="Войти", font=BOLD_FONT, command=self.attempt_login,
            width=120, height=40, fg_color=ACCENT_COLOR, hover_color=BUTTON_HOVER_COLOR
        )
        login_button.pack(pady=(10, 15))

        # Кнопка "Выход"
        exit_button = ctk.CTkButton(
            main_frame, text="Выход", font=BOLD_FONT, command=self.on_closing,
            width=120, height=40, fg_color="gray", hover_color="dim gray"
        )
        exit_button.pack()

    def attempt_login(self, event=None):  # Добавлен event для обработки Enter
        """Пытается аутентифицировать пользователя."""
        login = self.login_entry.get().strip()
        password = self.password_entry.get()

        # Сбрасываем сообщение об ошибке
        self.error_label.configure(text="")

        if not login or not password:
            self.error_label.configure(text="Введите логин и пароль.")
            log.warning("Попытка входа с пустыми полями.")
            return

        log.info(f"Попытка входа пользователя: '{login}'")
        # Получаем данные пользователя по логину (ID, Hash, RoleID)
        user_data = self.user_repository.get_user_by_login(login)

        if user_data:
            user_id, stored_hash, role_id = user_data
            # Проверяем пароль
            if self.user_repository.verify_password(password, stored_hash):
                log.info(
                    f"Успешный вход пользователя: '{login}' (ID: {user_id}, RoleID: {role_id})")
                # Сохраняем данные вошедшего пользователя
                self.logged_in_user_data = {
                    "user_id": user_id,
                    "role_id": role_id,
                    "login": login  # Сохраним и логин на всякий случай
                }
                self.destroy()  # Закрываем окно входа
            else:
                log.warning(f"Неверный пароль для пользователя: '{login}'")
                self.error_label.configure(text="Неверный логин или пароль.")
                self.password_entry.delete(0, "end")  # Очищаем поле пароля
        else:
            log.warning(f"Пользователь не найден: '{login}'")
            self.error_label.configure(text="Неверный логин или пароль.")
            self.password_entry.delete(0, "end")  # Очищаем поле пароля

    def on_closing(self):
        """Обработчик закрытия окна."""
        log.info("Окно входа закрывается.")
        self.destroy()
        # Если пользователь не вошел, self.logged_in_user_data будет None
        # и основное приложение не запустится (см. main.py)

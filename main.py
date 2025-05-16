"""
Точка входа приложения АИС "Кадры".

Отвечает за инициализацию логгера, подключение к базе данных,
запуск окна входа и, в случае успешной аутентификации, запуск
главного окна приложения.
"""
import customtkinter as ctk
from gui.main_window import MainWindow
from gui.login_window import LoginWindow
from db.database import Database
from config import DATABASE_PATH, LOG_LEVEL, LOG_FORMAT, LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT
import logging
from gui.utils import configure_logging
import tkinter as tk
from tkinter import messagebox

log = logging.getLogger(__name__)


def main():
    """Основная функция запуска приложения."""
    # --- Настройка логирования ---
    configure_logging(LOG_LEVEL, LOG_FORMAT, LOG_FILE,
                      MAX_LOG_SIZE, BACKUP_COUNT)
    log.info("Запуск приложения")

    # --- Инициализация базы данных ---
    db = Database()
    if db.conn is None:
        log.critical(
            "Не удалось подключиться к базе данных. Завершение работы.")
        # Попытка показать сообщение об ошибке, если GUI доступен
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Критическая ошибка",
                                 "Не удалось подключиться к базе данных!")
            root.destroy()
        except Exception as e:
            print(f"Не удалось показать сообщение об ошибке БД: {e}")
        return

    # --- Запуск окна входа ---
    login_root = LoginWindow(db)
    login_root.mainloop()

    # --- Проверка результата входа и запуск основного окна ---
    logged_in_user = login_root.logged_in_user_data
    if logged_in_user:
        log.info("Вход успешен, запуск основного окна.")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        main_app_root = ctk.CTk()
        app = MainWindow(main_app_root, db, logged_in_user)
        main_app_root.mainloop()
    else:
        log.info("Вход не выполнен или окно входа закрыто. Завершение работы.")

    # --- Завершение работы ---
    db.close()
    log.info("Приложение завершило работу.")


if __name__ == "__main__":
    main()

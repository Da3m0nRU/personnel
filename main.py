# main.py
import customtkinter as ctk
from gui.main_window import MainWindow
from gui.login_window import LoginWindow  # Импортируем окно входа
from db.database import Database
from config import DATABASE_PATH
import logging
from gui.utils import configure_logging
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT

log = logging.getLogger(__name__)


def main():
    configure_logging(LOG_LEVEL, LOG_FORMAT, LOG_FILE,
                      MAX_LOG_SIZE, BACKUP_COUNT)
    log.info("Запуск приложения")

    # 1. Инициализируем базу данных
    db = Database()
    if db.conn is None:
        log.critical(
            "Не удалось подключиться к базе данных. Завершение работы.")
        # Можно показать messagebox здесь, если tkinter уже импортирован
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # Скрыть основное пустое окно tk
            messagebox.showerror("Критическая ошибка",
                                 "Не удалось подключиться к базе данных!")
            root.destroy()
        except Exception as e:
            # Вывод в консоль как fallback
            print(f"Не удалось показать сообщение об ошибке БД: {e}")
        return

    # 2. Создаем и запускаем окно входа
    login_root = LoginWindow(db)  # Передаем объект базы данных
    login_root.mainloop()

    # 3. Получаем результат входа
    logged_in_user = login_root.logged_in_user_data

    # 4. Если вход УСПЕШЕН, запускаем основное окно
    if logged_in_user:
        log.info("Вход успешен, запуск основного окна.")
        # Устанавливаем внешний вид ПЕРЕД созданием основного окна
        ctk.set_appearance_mode("System")  # Или "Light", "Dark"
        ctk.set_default_color_theme("blue")  # Или "green", "dark-blue"

        # Создаем основное окно приложения
        main_app_root = ctk.CTk()
        # Передаем данные пользователя
        app = MainWindow(main_app_root, db, logged_in_user)
        main_app_root.mainloop()
    else:
        log.info("Вход не выполнен или окно входа закрыто. Завершение работы.")

    # 5. Закрываем соединение с БД после завершения работы приложения
    db.close()
    log.info("Приложение завершило работу.")


if __name__ == "__main__":
    main()

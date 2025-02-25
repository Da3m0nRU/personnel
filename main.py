# main.py
import tkinter as tk
import customtkinter as ctk  # Оставляем CustomTkinter
from gui.main_window import MainWindow
from db.database import Database
from config import DATABASE_PATH
import logging
from gui.utils import configure_logging
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT
# from tkinterdnd2 import TkinterDnD  # НЕ НУЖЕН здесь!

log = logging.getLogger(__name__)


def main():
    configure_logging(LOG_LEVEL, LOG_FORMAT, LOG_FILE,
                      MAX_LOG_SIZE, BACKUP_COUNT)

    log.info("Запуск приложения")

    db = Database()
    if db.conn is None:
        log.critical(
            "Не удалось подключиться к базе данных. Завершение работы.")
        return

    root = ctk.CTk()  # !!! Возвращаем CustomTkinter!
    ctk.set_appearance_mode("system")  # Можно указать тему

    app = MainWindow(root, db)
    root.mainloop()

    db.close()
    log.info("Приложение завершило работу.")


if __name__ == "__main__":
    main()

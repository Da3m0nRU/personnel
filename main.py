# main.py
import tkinter as tk
import customtkinter as ctk
from gui.main_window import MainWindow
from db.database import Database
from config import DATABASE_PATH
import logging
from gui.utils import configure_logging
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT

log = logging.getLogger(__name__)


def main():

    # Сразу настраиваем корневой логгер при импорте config, и передаём константы!!!
    configure_logging(LOG_LEVEL, LOG_FORMAT, LOG_FILE,
                      MAX_LOG_SIZE, BACKUP_COUNT)

    log.info("Запуск приложения")  # Начало

    db = Database()
    if db.conn is None:
        log.critical(
            "Не удалось подключиться к базе данных. Завершение работы.")
        return

    root = ctk.CTk()
    app = MainWindow(root, db)
    root.mainloop()

    db.close()
    log.info("Приложение завершило работу.")  # Конец


if __name__ == "__main__":
    main()

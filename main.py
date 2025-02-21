# main.py
import tkinter as tk
import customtkinter as ctk
from gui.main_window import MainWindow
from db.database import Database


def main():
    # ctk.set_appearance_mode("light")  # Перенес в main_window.py
    # ctk.set_default_color_theme("green")

    db = Database()
    if db.conn is None:  # Если не удалось подключиться к базе данных
        return  # ... завершаем работу

    root = ctk.CTk()
    app = MainWindow(root, db)  # !!! Передаем объект базы данных в MainWindow
    root.mainloop()

    db.close()  # Закрываем соединение с базой данных при закрытии приложения


if __name__ == "__main__":
    main()

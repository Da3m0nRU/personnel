# db/database.py
import sqlite3
# !!!  Используем config
from config import DATABASE_PATH


class Database:
    def __init__(self, db_path=DATABASE_PATH):  # указываем по умолчанию
        self.conn = None  # Инициализируем, чтобы IDE не ругалась
        self.cursor = None
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            # Или messagebox из tkinter
            print(f"Database connection error: {e}")
            # В реальном приложении здесь нужно предпринять действия

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True  # !!!
        except sqlite3.Error as e:
            # Подробный вывод
            print(f"SQL error: {e}, query: {query}, params: {params}")
            self.conn.rollback()
            return False

    def fetch_all(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()  # !!!
        except sqlite3.Error as e:
            print(f"SQL error: {e}, query: {query}, params: {params}")
            return None

    def fetch_one(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()  # !!!
        except sqlite3.Error as e:
            print(f"SQL error: {e}, query: {query}, params: {params}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()

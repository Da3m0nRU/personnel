# db/database.py
import sqlite3
from config import DATABASE_PATH  # !!!


class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.conn = None
        self.cursor = None
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            # В реальном приложении здесь нужно предпринять действия (вывести сообщение об ошибке, закрыть приложение и т.д.)

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"SQL error: {e}, query: {query}, params: {params}")
            self.conn.rollback()
            return False

    def fetch_all(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"SQL error: {e}, query: {query}, params: {params}")
            return None

    def fetch_one(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"SQL error: {e}, query: {query}, params: {params}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()

    def get_employees(self, page=1, per_page=10, search_term=None):
        offset = (page - 1) * per_page
        limit = per_page
        query = """
            SELECT
                E.PersonnelNumber,
                E.LastName,
                E.FirstName,
                E.MiddleName,
                E.BirthDate,
                G.GenderName,
                P.Name AS PositionName,
                D.Name AS DepartmentName,
                S.StateName
            FROM Employees AS E
            JOIN Genders AS G ON E.GenderID = G.ID
            JOIN Positions AS P ON E.PositionID = P.ID
            JOIN Departments AS D ON E.DepartmentID = D.ID
            JOIN States AS S ON E.StateID = S.ID
            JOIN PositionDepartments as PD ON  PD.DepartmentID = D.ID AND PD.PositionID = P.ID
        """
        params = []
        if search_term:
            query += """
                WHERE E.PersonnelNumber LIKE ?
                   OR E.LastName LIKE ?
                   OR E.FirstName LIKE ?
                   OR E.MiddleName LIKE ?
            """
            # !!!  Используем "расширенную" подстановку параметров
            params.extend([f"%{search_term}%"] * 4)

        query += """
            ORDER BY E.PersonnelNumber
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        data = self.fetch_all(query, params)

        if data is None:
            return None, 0
          # Запрос для получения ОБЩЕГО количества строк (без LIMIT/OFFSET)
        count_query = """
            SELECT COUNT(*)
            FROM Employees AS E
             JOIN Genders AS G ON E.GenderID = G.ID
            JOIN Positions AS P ON E.PositionID = P.ID
            JOIN Departments AS D ON E.DepartmentID = D.ID
             JOIN States AS S ON E.StateID = S.ID
            JOIN PositionDepartments as PD ON  PD.DepartmentID = D.ID AND PD.PositionID = P.ID
        """
        count_params = []

        if search_term:
            count_query += """
                WHERE E.PersonnelNumber LIKE ?
                   OR E.LastName LIKE ?
                   OR E.FirstName LIKE ?
                   OR E.MiddleName LIKE ?
            """
            count_params = [f"%{search_term}%"] * 4

        total_rows = self.fetch_one(count_query, count_params)[0]

        return data, total_rows

    def get_departments_for_position(self, position_id):
        query = """
            SELECT D.Name
            FROM Departments AS D
            INNER JOIN PositionDepartments AS PD ON D.ID = PD.DepartmentID
            WHERE PD.PositionID = ?
        """
        return self.fetch_all(query, (position_id,))

    def get_positions(self):
        query = "SELECT Name FROM Positions"
        return self.fetch_all(query)

    def delete_employee(self, personnel_number):
        query = "DELETE FROM Employees WHERE PersonnelNumber = ?"
        return self.execute_query(query, (personnel_number,))

    def get_employee_by_personnel_number(self, personnel_number):
        """Возвращает данные сотрудника по табельному номеру (все поля, включая названия отделов и т.д.)."""
        query = """
            SELECT
                E.PersonnelNumber,
                E.LastName,
                E.FirstName,
                E.MiddleName,
                E.BirthDate,
                G.GenderName,
                P.Name AS PositionName,
                D.Name AS DepartmentName,
                S.StateName
            FROM Employees AS E
            JOIN Genders AS G ON E.GenderID = G.ID
            JOIN Positions AS P ON E.PositionID = P.ID
            JOIN Departments AS D ON E.DepartmentID = D.ID
            JOIN States AS S ON E.StateID = S.ID
            WHERE E.PersonnelNumber = ?
        """
        return self.fetch_one(query, (personnel_number,))

    def update_employee(self, personnel_number, lastname, firstname, middlename, birth_date_str,
                        gender_id, position_id, department_id, state_id):
        """Обновляет данные сотрудника в БД."""
        query = """
            UPDATE Employees
            SET LastName = ?,
                FirstName = ?,
                MiddleName = ?,
                BirthDate = ?,
                GenderID = ?,
                PositionID = ?,
                DepartmentID = ?,
                StateID = ?
            WHERE PersonnelNumber = ?
        """
        params = (lastname, firstname, middlename, birth_date_str,
                  gender_id, position_id, department_id, state_id, personnel_number)
        return self.execute_query(query, params)

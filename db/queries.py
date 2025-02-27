# db/queries.py

# --- Сотрудники ---

# Получение всех сотрудников (без пагинации, но с возможностью поиска)
GET_EMPLOYEES = """
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
    WHERE 1=1  -- Заглушка для WHERE
"""

# Дополнение к запросу GET_EMPLOYEES для поиска
GET_EMPLOYEES_SEARCH = """
   AND (E.PersonnelNumber LIKE :search_term
       OR E.LastName LIKE :search_term
       OR E.FirstName LIKE :search_term
       OR E.MiddleName LIKE :search_term
       OR E.BirthDate LIKE :search_term
       OR G.GenderName LIKE :search_term
       OR P.Name LIKE :search_term
       OR D.Name LIKE :search_term
       OR S.StateName LIKE :search_term)
"""

#  Дополнение для сортировки (ORDER BY)
GET_EMPLOYEES_ORDER_BY = " ORDER BY E.PersonnelNumber"


GET_EMPLOYEES_COUNT = """
    SELECT COUNT(*)
    FROM Employees AS E
    JOIN Genders AS G ON E.GenderID = G.ID
    JOIN Positions AS P ON E.PositionID = P.ID
    JOIN Departments AS D ON E.DepartmentID = D.ID
    JOIN States AS S ON E.StateID = S.ID
    WHERE 1=1 -- Заглушка для WHERE
"""
#!!! такой же search, как и для работников
GET_EMPLOYEES_COUNT_SEARCH = GET_EMPLOYEES_SEARCH

# --- Добавление нового сотрудника ---
INSERT_EMPLOYEE = """
    INSERT INTO Employees (PersonnelNumber, LastName, FirstName, MiddleName, BirthDate,
                          GenderID, PositionID, DepartmentID, StateID)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# --- Обновление данных сотрудника ---
UPDATE_EMPLOYEE = """
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

# --- Удаление сотрудника ---
DELETE_EMPLOYEE = "DELETE FROM Employees WHERE PersonnelNumber = ?"

# --- Получение сотрудника по табельному номеру ---
GET_EMPLOYEE_BY_PERSONNEL_NUMBER = """
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

# --- Справочники ---

GET_GENDERS = "SELECT ID, GenderName FROM Genders"
GET_GENDER_ID = "SELECT ID FROM Genders WHERE GenderName = ?"

GET_ALL_POSITIONS = "SELECT ID, Name FROM Positions"
GET_POSITION_ID = "SELECT ID FROM Positions WHERE Name = ?"
GET_POSITIONS = "SELECT Name FROM Positions"  # !!!

GET_STATES = "SELECT ID, StateName FROM States"
GET_STATE_ID = "SELECT ID FROM States WHERE StateName = ?"

GET_DEPARTMENTS = "SELECT ID, Name FROM Departments"
GET_DEPARTMENT_BY_NAME = "SELECT ID FROM Departments WHERE Name = ?"

GET_DEPARTMENTS_FOR_POSITION = """
    SELECT D.Name
    FROM Departments AS D
    INNER JOIN PositionDepartments AS PD ON D.ID = PD.DepartmentID
    WHERE PD.PositionID = ?
"""
# --- Дополнительные запросы (если понадобятся в будущем) ---

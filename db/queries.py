# db/queries.py

# --- Employees ---

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
    JOIN PositionDepartments as PD ON  PD.DepartmentID = D.ID AND PD.PositionID = P.ID
    WHERE 1=1  -- Заглушка для удобного добавления условий
"""

GET_EMPLOYEES_COUNT = """
    SELECT COUNT(*)
    FROM Employees AS E
     JOIN Genders AS G ON E.GenderID = G.ID
    JOIN Positions AS P ON E.PositionID = P.ID
    JOIN Departments AS D ON E.DepartmentID = D.ID
     JOIN States AS S ON E.StateID = S.ID
    JOIN PositionDepartments as PD ON  PD.DepartmentID = D.ID AND PD.PositionID = P.ID
    WHERE 1=1 -- Заглушка для удобного добавления условий
"""

GET_DEPARTMENTS_FOR_POSITION = """
    SELECT D.Name
    FROM Departments AS D
    INNER JOIN PositionDepartments AS PD ON D.ID = PD.DepartmentID
    WHERE PD.PositionID = ?
"""

GET_POSITIONS = "SELECT Name FROM Positions"

DELETE_EMPLOYEE = "DELETE FROM Employees WHERE PersonnelNumber = ?"

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

# --- Справочники (общие)---
GET_GENDERS = "SELECT ID, GenderName FROM Genders"
GET_ALL_POSITIONS = "SELECT ID, Name FROM Positions"
GET_STATES = "SELECT ID, StateName FROM States"
GET_DEPARTMENTS = "SELECT ID, Name FROM Departments"  # понадобится в будущем

# --- Добавление нового сотрудника ---

INSERT_EMPLOYEE = """
    INSERT INTO Employees (PersonnelNumber, LastName, FirstName, MiddleName, BirthDate,
                          GenderID, PositionID, DepartmentID, StateID)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

GET_GENDER_ID = "SELECT ID FROM Genders WHERE GenderName = ?"
GET_POSITION_ID = "SELECT ID FROM Positions WHERE Name = ?"
GET_STATE_ID = "SELECT ID FROM States WHERE StateName = ?"
GET_DEPARTMENT_BY_NAME = "SELECT ID FROM Departments WHERE Name = ?"

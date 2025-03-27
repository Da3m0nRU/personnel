# db/queries.py

# --- Сотрудники ---
GET_EMPLOYEES = """
    SELECT
        E.PersonnelNumber, E.LastName, E.FirstName, E.MiddleName, E.BirthDate,
        G.GenderName, P.Name AS PositionName, D.Name AS DepartmentName, S.StateName
    FROM Employees AS E
    JOIN Genders AS G ON E.GenderID = G.ID
    JOIN Positions AS P ON E.PositionID = P.ID
    JOIN Departments AS D ON E.DepartmentID = D.ID
    JOIN States AS S ON E.StateID = S.ID
    WHERE 1=1
"""
GET_EMPLOYEES_SEARCH = """
   AND (E.PersonnelNumber LIKE :search_term OR E.LastName LIKE :search_term OR E.FirstName LIKE :search_term OR
        E.MiddleName LIKE :search_term OR E.BirthDate LIKE :search_term OR G.GenderName LIKE :search_term OR
        P.Name LIKE :search_term OR D.Name LIKE :search_term OR S.StateName LIKE :search_term)
"""
GET_EMPLOYEES_ORDER_BY = " ORDER BY E.PersonnelNumber"
GET_EMPLOYEES_COUNT = """
    SELECT COUNT(*) FROM Employees AS E
    JOIN Genders AS G ON E.GenderID = G.ID JOIN Positions AS P ON E.PositionID = P.ID
    JOIN Departments AS D ON E.DepartmentID = D.ID JOIN States AS S ON E.StateID = S.ID
    WHERE 1=1
"""
GET_EMPLOYEES_COUNT_SEARCH = GET_EMPLOYEES_SEARCH
INSERT_EMPLOYEE = """
    INSERT INTO Employees (PersonnelNumber, LastName, FirstName, MiddleName, BirthDate,
                          GenderID, PositionID, DepartmentID, StateID)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_EMPLOYEE = """
    UPDATE Employees SET LastName = ?, FirstName = ?, MiddleName = ?, BirthDate = ?,
                         GenderID = ?, PositionID = ?, DepartmentID = ?, StateID = ?
    WHERE PersonnelNumber = ?
"""
DELETE_EMPLOYEE = "DELETE FROM Employees WHERE PersonnelNumber = ?"
GET_EMPLOYEE_BY_PERSONNEL_NUMBER = """
    SELECT E.PersonnelNumber, E.LastName, E.FirstName, E.MiddleName, E.BirthDate, G.GenderName,
           P.Name AS PositionName, D.Name AS DepartmentName, S.StateName
    FROM Employees AS E
    JOIN Genders AS G ON E.GenderID = G.ID JOIN Positions AS P ON E.PositionID = P.ID
    JOIN Departments AS D ON E.DepartmentID = D.ID JOIN States AS S ON E.StateID = S.ID
    WHERE E.PersonnelNumber = ?
"""
# --- Справочники ---
GET_GENDERS = "SELECT ID, GenderName FROM Genders"
GET_GENDER_ID = "SELECT ID FROM Genders WHERE GenderName = ?"
GET_ALL_POSITIONS = "SELECT ID, Name FROM Positions"
GET_POSITION_ID = "SELECT ID FROM Positions WHERE Name = ?"
GET_POSITIONS = "SELECT Name FROM Positions"
GET_STATES = "SELECT ID, StateName FROM States"
GET_STATE_ID = "SELECT ID FROM States WHERE StateName = ?"
GET_DEPARTMENTS = "SELECT ID, Name FROM Departments"
GET_DEPARTMENT_BY_NAME = "SELECT ID FROM Departments WHERE Name = ?"
GET_DEPARTMENTS_FOR_POSITION = """
    SELECT D.Name FROM Departments AS D
    INNER JOIN PositionDepartments AS PD ON D.ID = PD.DepartmentID
    WHERE PD.PositionID = ?
"""

# --- Кадровые события ---
GET_EMPLOYEE_EVENTS = """
    SELECT EE.EventDate, EV.EventName, E.PersonnelNumber,
           E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName,
           P.Name AS NewPositionName, D.Name AS NewDepartmentName, EE.Reason
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID JOIN Employees AS E ON EE.EmployeePersonnelNumber = E.PersonnelNumber
    LEFT JOIN Positions AS P ON EE.PositionID = P.ID LEFT JOIN Departments AS D ON EE.DepartmentID = D.ID
    WHERE 1=1
"""
GET_EMPLOYEE_EVENTS_SEARCH = """
   AND (EE.EventDate LIKE :search_term OR EV.EventName LIKE :search_term OR E.PersonnelNumber LIKE :search_term OR
        E.LastName LIKE :search_term OR E.FirstName LIKE :search_term OR E.MiddleName LIKE :search_term OR
        P.Name LIKE :search_term OR D.Name LIKE :search_term OR EE.Reason LIKE :search_term)
"""
GET_EMPLOYEE_EVENTS_ORDER_BY = " ORDER BY EE.EventDate DESC, EE.ID DESC"
GET_EMPLOYEE_EVENTS_COUNT = """
    SELECT COUNT(EE.ID) FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID JOIN Employees AS E ON EE.EmployeePersonnelNumber = E.PersonnelNumber
    LEFT JOIN Positions AS P ON EE.PositionID = P.ID LEFT JOIN Departments AS D ON EE.DepartmentID = D.ID
    WHERE 1=1
"""
GET_EMPLOYEE_EVENTS_COUNT_SEARCH = GET_EMPLOYEE_EVENTS_SEARCH
INSERT_EMPLOYEE_EVENT = """
    INSERT INTO EmployeeEvents (EmployeePersonnelNumber, EventID, EventDate, DepartmentID, PositionID, Reason)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# --- Отсутствия ---
GET_ABSENCES = """
    SELECT
        A.ID, -- !!! ID добавлен ПЕРВЫМ СТОЛБЦОМ !!!
        E.PersonnelNumber,
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName,
        A.AbsenceDate,
        CASE A.FullDay WHEN 1 THEN 'Да' ELSE 'Нет' END AS IsFullDay,
        A.StartingTime AS StartTime, -- Убрали COALESCE
        A.EndingTime AS EndTime,     -- Убрали COALESCE
        A.Reason
    FROM Absences AS A
    JOIN Employees AS E ON A.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE 1=1
"""
GET_ABSENCES_SEARCH = """
    AND (E.PersonnelNumber LIKE :search_term OR E.LastName LIKE :search_term OR E.FirstName LIKE :search_term OR
         E.MiddleName LIKE :search_term OR A.AbsenceDate LIKE :search_term OR
         (CASE A.FullDay WHEN 1 THEN 'Да' ELSE 'Нет' END) LIKE :search_term OR
         A.StartingTime LIKE :search_term OR A.EndingTime LIKE :search_term OR A.Reason LIKE :search_term)
"""
GET_ABSENCES_ORDER_BY = " ORDER BY A.AbsenceDate DESC, E.LastName, E.FirstName"
GET_ABSENCES_COUNT = """
    SELECT COUNT(A.ID) FROM Absences AS A
    JOIN Employees AS E ON A.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE 1=1
"""
GET_ABSENCES_COUNT_SEARCH = GET_ABSENCES_SEARCH
INSERT_ABSENCE = """
    INSERT INTO Absences (EmployeePersonnelNumber, AbsenceDate, FullDay, StartingTime, EndingTime, Reason, ScheduleID)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
# --- НОВЫЕ для CRUD отсутствий ---
GET_ABSENCE_BY_ID = """
    SELECT ID, EmployeePersonnelNumber, AbsenceDate, FullDay, StartingTime, EndingTime, Reason, ScheduleID
    FROM Absences WHERE ID = ?
"""
UPDATE_ABSENCE = """
    UPDATE Absences SET AbsenceDate = ?, FullDay = ?, StartingTime = ?, EndingTime = ?,
                        Reason = ?, ScheduleID = ?, EmployeePersonnelNumber = ?
    WHERE ID = ?
"""
DELETE_ABSENCE = "DELETE FROM Absences WHERE ID = ?"
# ------------------------------
GET_EMPLOYEE_LIST_FOR_ABSENCE = """
    SELECT PersonnelNumber, LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '') AS FullName
    FROM Employees WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    ORDER BY LastName, FirstName
"""
GET_WORKING_HOURS_FOR_POSITION_AND_DAY = """
    SELECT S.ID AS ScheduleID, WH.StartingTime, WH.EndingTime
    FROM Schedules AS S
    JOIN WorkingHours AS WH ON S.WorkingHoursID = WH.ID
    WHERE S.PositionID = ? AND S.DayOfWeekID = ? LIMIT 1
"""

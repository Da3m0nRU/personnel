"""
Модуль содержит константы с SQL-запросами для работы с базой данных АИС "Кадры".

Запросы сгруппированы по логическим блокам (сущностям):
- Сотрудники (Employees)
- Справочники (Genders, Positions, Departments, States, Events, Roles)
- Кадровые события (EmployeeEvents)
- Отсутствия (Absences)
- Пользователи (Users)
- Отчеты (Reports)

Имена констант отражают назначение конкретного SQL-запроса.
"""

# ==============================================================================
# Сотрудники (Employees)
# ==============================================================================

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
GET_EMPLOYEE_FIO_BY_PN = """
    SELECT LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '')
    FROM Employees WHERE PersonnelNumber = ?
"""
GET_EMPLOYEE_FIO_MAP_DATA = """
    SELECT PersonnelNumber, LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '')
    FROM Employees
"""
GET_EMPLOYEE_POSITION_ID_BY_PN = """
    SELECT PositionID FROM Employees WHERE PersonnelNumber = ?
"""
CHECK_PERSONNEL_NUMBER_EXISTS = """
    SELECT 1 FROM Employees WHERE PersonnelNumber = ?
"""
GET_ACTIVE_EMPLOYEE_COUNT = """
    SELECT COUNT(PersonnelNumber) FROM Employees
    WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
"""
GET_EMPLOYEES_COUNT_BY_DEPARTMENT = """
    SELECT D.Name, COUNT(E.PersonnelNumber)
    FROM Employees E
    JOIN Departments D ON E.DepartmentID = D.ID
    WHERE E.StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    GROUP BY D.Name
    ORDER BY COUNT(E.PersonnelNumber) DESC;
"""
GET_EMPLOYEES_COUNT_BY_POSITION_TOP_N = """
    SELECT P.Name, COUNT(E.PersonnelNumber) as EmpCount
    FROM Employees E
    JOIN Positions P ON E.PositionID = P.ID
    WHERE E.StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    GROUP BY P.Name
    ORDER BY EmpCount DESC
    LIMIT ?;
"""
GET_ACTIVE_EMPLOYEE_BIRTH_DATES = """
    SELECT BirthDate FROM Employees
    WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    AND BirthDate IS NOT NULL AND BirthDate != '';
"""
GET_GENDER_DISTRIBUTION = """
    SELECT G.GenderName, COUNT(E.PersonnelNumber)
    FROM Employees E
    JOIN Genders G ON E.GenderID = G.ID
    WHERE E.StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    GROUP BY G.GenderName
    ORDER BY COUNT(E.PersonnelNumber) DESC;
"""
GET_EMPLOYEE_LIST_FOR_ABSENCE = """
    SELECT PersonnelNumber, LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '') AS FullName
    FROM Employees WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    ORDER BY LastName, FirstName
"""
GET_ACTIVE_EMPLOYEES_FOR_LINKING = """
    SELECT PersonnelNumber, LastName || ' ' || FirstName || COALESCE(' ' || MiddleName, '') AS FullName
    FROM Employees
    WHERE StateID = (SELECT ID FROM States WHERE StateName = 'Работает')
    ORDER BY LastName, FirstName;
"""

# ==============================================================================
# Справочники (Genders, Positions, Departments, States, Events, Roles)
# ==============================================================================

# --- Справочник: Пол (Genders) ---
GET_GENDERS = "SELECT ID, GenderName FROM Genders"
GET_GENDER_ID = "SELECT ID FROM Genders WHERE GenderName = ?"

# --- Справочник: Должности (Positions) ---
GET_ALL_POSITIONS = "SELECT ID, Name FROM Positions"
GET_POSITION_ID = "SELECT ID FROM Positions WHERE Name = ?"
GET_POSITIONS = "SELECT Name FROM Positions"

# --- Справочник: Состояния (States) ---
GET_STATES = "SELECT ID, StateName FROM States"
GET_STATE_ID = "SELECT ID FROM States WHERE StateName = ?"

# --- Справочник: Отделы (Departments) ---
GET_DEPARTMENTS = "SELECT ID, Name FROM Departments"
GET_DEPARTMENT_ID_BY_NAME = "SELECT ID FROM Departments WHERE Name = ?"
GET_DEPARTMENTS_FOR_POSITION = """
    SELECT D.Name FROM Departments AS D
    INNER JOIN PositionDepartments AS PD ON D.ID = PD.DepartmentID
    WHERE PD.PositionID = ?
"""

# --- Справочник: Кадровые события (Events) ---
GET_ALL_EVENTS = "SELECT ID, EventName FROM Events"
GET_EVENT_ID_BY_NAME = "SELECT ID FROM Events WHERE EventName = ?"

# --- Справочник: Роли пользователей (Roles) ---
GET_ALL_ROLES_ORDERED = "SELECT ID, RoleName FROM Roles ORDER BY RoleName"
GET_ROLE_ID_BY_NAME = "SELECT ID FROM Roles WHERE RoleName = ?"
GET_ROLE_NAME_BY_ID = "SELECT RoleName FROM Roles WHERE ID = ?"
GET_ADMIN_ROLE_ID = "SELECT ID FROM Roles WHERE RoleName = 'Администратор'"

# ==============================================================================
# Кадровые события (EmployeeEvents)
# ==============================================================================

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
GET_EVENT_COUNT_LAST_DAYS = """
    SELECT COUNT(EE.ID)
    FROM EmployeeEvents EE
    JOIN Events EV ON EE.EventID = EV.ID
    WHERE EV.EventName = ?
    AND EE.EventDate BETWEEN ? AND ?;
"""

# ==============================================================================
# Отсутствия (Absences)
# ==============================================================================

GET_ABSENCES = """
    SELECT
        A.ID, -- ID всегда первый столбец для совместимости
        E.PersonnelNumber,
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName,
        A.AbsenceDate,
        CASE A.FullDay WHEN 1 THEN 'Да' ELSE 'Нет' END AS IsFullDay,
        A.StartingTime AS StartTime,
        A.EndingTime AS EndTime,
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

CHECK_ABSENCE_EXISTS_BY_PN_DATE = """
    SELECT 1 FROM Absences WHERE EmployeePersonnelNumber = ? AND AbsenceDate = ?
"""
GET_WORKING_HOURS_FOR_POSITION_AND_DAY = """
    SELECT S.ID AS ScheduleID, WH.StartingTime, WH.EndingTime
    FROM Schedules AS S
    JOIN WorkingHours AS WH ON S.WorkingHoursID = WH.ID
    WHERE S.PositionID = ? AND S.DayOfWeekID = ? LIMIT 1
"""

# ==============================================================================
# Пользователи (Users)
# ==============================================================================

GET_USERS_BASE = """
    SELECT
        U.ID,                   -- 0: ID
        U.Login,                -- 1: Login
        U.Password,             -- 2: Password Hash
        COALESCE(E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, ''), U.EmployeePersonnelNumber, 'Не связан') AS EmployeeInfo, -- 3: Employee Info or PN
        R.RoleName,             -- 4: Role Name
        U.Email                 -- 5: Email
    FROM Users AS U
    JOIN Roles AS R ON U.RoleID = R.ID
    LEFT JOIN Employees AS E ON U.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE 1=1
"""
GET_USERS_SEARCH = """
    AND (U.Login LIKE :search_term OR U.Email LIKE :search_term OR R.RoleName LIKE :search_term
         OR E.LastName LIKE :search_term OR E.FirstName LIKE :search_term OR U.EmployeePersonnelNumber LIKE :search_term)
"""
GET_USERS_ORDER_BY = " ORDER BY U.Login"

GET_USERS_COUNT_BASE = """
    SELECT COUNT(U.ID)
    FROM Users AS U
    JOIN Roles AS R ON U.RoleID = R.ID
    LEFT JOIN Employees AS E ON U.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE 1=1
"""
GET_USERS_COUNT_SEARCH = GET_USERS_SEARCH

GET_USER_BY_ID = "SELECT ID, Login, Password, EmployeePersonnelNumber, RoleID, Email FROM Users WHERE ID = ?"
GET_USER_BY_LOGIN_FOR_AUTH = "SELECT ID, Password, RoleID FROM Users WHERE Login = ?"
GET_USER_ROLE_ID_BY_USER_ID = "SELECT RoleID FROM Users WHERE ID = ?"

INSERT_USER = """
    INSERT INTO Users (Login, Password, EmployeePersonnelNumber, RoleID, Email)
    VALUES (?, ?, ?, ?, ?)
"""
UPDATE_USER_WITH_PASSWORD = """
    UPDATE Users SET RoleID = ?, EmployeePersonnelNumber = ?, Email = ?, Password = ?
    WHERE ID = ?
"""
UPDATE_USER_WITHOUT_PASSWORD = """
    UPDATE Users SET RoleID = ?, EmployeePersonnelNumber = ?, Email = ?
    WHERE ID = ?
"""
DELETE_USER = "DELETE FROM Users WHERE ID = ?"

CHECK_LOGIN_UNIQUE = "SELECT 1 FROM Users WHERE Login = ?"
CHECK_LOGIN_UNIQUE_EXCLUDE_ID = "SELECT 1 FROM Users WHERE Login = ? AND ID != ?"

GET_ADMIN_COUNT = """
    SELECT COUNT(U.ID) FROM Users U
    JOIN Roles R ON U.RoleID = R.ID
    WHERE R.RoleName = 'Администратор'
"""

# ==============================================================================
# Отчеты (Reports)
# ==============================================================================

# --- Отчет по увольнениям ---
GET_DISMISSAL_COUNT_BY_MONTH = """
    SELECT
        substr(EE.EventDate, 1, 7) AS DismissalMonth, -- 'YYYY-MM'
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE.EventDate BETWEEN ? AND ?
    GROUP BY DismissalMonth
    ORDER BY DismissalMonth ASC;
"""
GET_DISMISSAL_COUNT_BY_DAY = """
    SELECT
        EE.EventDate AS DismissalDay, -- 'YYYY-MM-DD'
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE.EventDate BETWEEN ? AND ?
    GROUP BY DismissalDay
    ORDER BY DismissalDay ASC;
"""
GET_DISMISSAL_COUNT_BY_YEAR = """
    SELECT
        substr(EE.EventDate, 1, 4) AS DismissalYear, -- 'YYYY'
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE.EventDate BETWEEN ? AND ?
    GROUP BY DismissalYear
    ORDER BY DismissalYear ASC;
"""
GET_DISMISSED_EMPLOYEES_DETAILS = """
    SELECT
        E.PersonnelNumber,
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName,
        P.Name AS PositionName,
        D.Name AS DepartmentName,
        (SELECT MAX(EventDate)
         FROM EmployeeEvents AS EE_Hire
         JOIN Events AS EV_Hire ON EE_Hire.EventID = EV_Hire.ID
         WHERE EE_Hire.EmployeePersonnelNumber = E.PersonnelNumber
           AND EV_Hire.EventName = 'Прием'
           AND EE_Hire.EventDate <= EE_Dismiss.EventDate
        ) AS HireDate,
        EE_Dismiss.EventDate AS DismissalDate,
        EE_Dismiss.Reason AS DismissalReason
    FROM EmployeeEvents AS EE_Dismiss
    JOIN Employees AS E ON EE_Dismiss.EmployeePersonnelNumber = E.PersonnelNumber
    JOIN Events AS EV ON EE_Dismiss.EventID = EV.ID
    LEFT JOIN Positions AS P ON E.PositionID = P.ID
    LEFT JOIN Departments AS D ON E.DepartmentID = D.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE_Dismiss.EventDate BETWEEN ? AND ?
    ORDER BY EE_Dismiss.EventDate DESC;
"""

# --- Отчет по отсутствиям ---
GET_ABSENCES_DETAILS_FOR_REPORT = """
    SELECT
        EmployeePersonnelNumber,
        AbsenceDate,
        FullDay,
        StartingTime,
        EndingTime,
        ScheduleID
    FROM Absences
    WHERE AbsenceDate BETWEEN ? AND ?
    ORDER BY EmployeePersonnelNumber, AbsenceDate;
"""
GET_RAW_ABSENCE_DATA_FOR_SUMMATION = """
    SELECT
        A.EmployeePersonnelNumber, -- 0
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName, -- 1
        E.PositionID,             -- 2
        A.AbsenceDate,            -- 3
        A.FullDay,                -- 4
        A.StartingTime,           -- 5
        A.EndingTime,             -- 6
        A.ScheduleID              -- 7
    FROM Absences AS A
    JOIN Employees AS E ON A.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE A.AbsenceDate BETWEEN ? AND ?
    ORDER BY A.EmployeePersonnelNumber, A.AbsenceDate;
"""

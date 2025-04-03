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

# --- Отчеты ---

# Отчет по увольнениям: Данные для ГРАФИКА
# Считаем количество увольнений по месяцам в заданном периоде
# Используем substr для извлечения 'ГГГГ-ММ'
GET_DISMISSAL_COUNT_BY_MONTH = """
    SELECT
        substr(EE.EventDate, 1, 7) AS DismissalMonth, -- Получаем 'ГГГГ-ММ'
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение' -- Только события увольнения
      AND EE.EventDate BETWEEN ? AND ?   -- В заданном диапазоне дат (включительно)
    GROUP BY DismissalMonth           -- Группируем по месяцу
    ORDER BY DismissalMonth ASC;      -- Сортируем по месяцу
"""

# Отчет по увольнениям: Данные для ТАБЛИЦЫ
# Получаем детальный список уволенных в заданном периоде
GET_DISMISSED_EMPLOYEES_DETAILS = """
    SELECT
        E.PersonnelNumber,
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName,
        P.Name AS PositionName,
        D.Name AS DepartmentName,
        -- Ищем дату приема (последнее событие 'Прием' ДО даты увольнения)
        (SELECT MAX(EventDate)
         FROM EmployeeEvents AS EE_Hire
         JOIN Events AS EV_Hire ON EE_Hire.EventID = EV_Hire.ID
         WHERE EE_Hire.EmployeePersonnelNumber = E.PersonnelNumber
           AND EV_Hire.EventName = 'Прием'
           AND EE_Hire.EventDate <= EE_Dismiss.EventDate -- Не позже даты увольнения
        ) AS HireDate,
        EE_Dismiss.EventDate AS DismissalDate,
        EE_Dismiss.Reason AS DismissalReason
    FROM EmployeeEvents AS EE_Dismiss
    JOIN Employees AS E ON EE_Dismiss.EmployeePersonnelNumber = E.PersonnelNumber
    JOIN Events AS EV ON EE_Dismiss.EventID = EV.ID
    LEFT JOIN Positions AS P ON E.PositionID = P.ID   -- Должность на момент увольнения (из Employees)
    LEFT JOIN Departments AS D ON E.DepartmentID = D.ID -- Отдел на момент увольнения (из Employees)
    WHERE EV.EventName = 'Увольнение'
      AND EE_Dismiss.EventDate BETWEEN ? AND ? -- В заданном диапазоне
    ORDER BY EE_Dismiss.EventDate DESC; -- Сначала последние уволенные
"""

# НОВЫЙ: Отчет по увольнениям: Данные для ГРАФИКА (по дням)
GET_DISMISSAL_COUNT_BY_DAY = """
    SELECT
        EE.EventDate AS DismissalDay, -- Дата как есть
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE.EventDate BETWEEN ? AND ?
    GROUP BY DismissalDay
    ORDER BY DismissalDay ASC;
"""

# НОВЫЙ: Отчет по увольнениям: Данные для ГРАФИКА (по годам)
GET_DISMISSAL_COUNT_BY_YEAR = """
    SELECT
        substr(EE.EventDate, 1, 4) AS DismissalYear, -- Получаем 'ГГГГ'
        COUNT(EE.ID) AS DismissalCount
    FROM EmployeeEvents AS EE
    JOIN Events AS EV ON EE.EventID = EV.ID
    WHERE EV.EventName = 'Увольнение'
      AND EE.EventDate BETWEEN ? AND ?
    GROUP BY DismissalYear
    ORDER BY DismissalYear ASC;
"""

GET_ABSENCES_DETAILS_FOR_REPORT = """
    SELECT
        EmployeePersonnelNumber,
        AbsenceDate,
        FullDay,
        StartingTime, -- Может быть NULL из старых версий или если не был подставлен
        EndingTime,   -- Может быть NULL
        ScheduleID    -- Может быть NULL
    FROM Absences
    WHERE AbsenceDate BETWEEN ? AND ?
    ORDER BY EmployeePersonnelNumber, AbsenceDate; -- Сортируем для возможной доп. логики
"""

# Запрос для получения ИСХОДНЫХ данных для расчета сумм отсутствий
GET_RAW_ABSENCE_DATA_FOR_SUMMATION = """
    SELECT
        A.EmployeePersonnelNumber, -- 0: Табельный номер
        E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, '') AS FullName, -- 1: ФИО
        E.PositionID,             -- 2: ID Должности сотрудника
        A.AbsenceDate,            -- 3: Дата отсутствия
        A.FullDay,                -- 4: Флаг полного дня (1 или 0)
        A.StartingTime,           -- 5: Время начала (ЧЧ:ММ или NULL/пусто)
        A.EndingTime,             -- 6: Время окончания (ЧЧ:ММ или NULL/пусто)
        A.ScheduleID              -- 7: ID Графика из записи Absence (может быть NULL)
    FROM Absences AS A
    JOIN Employees AS E ON A.EmployeePersonnelNumber = E.PersonnelNumber
    WHERE A.AbsenceDate BETWEEN ? AND ? -- Фильтр по дате
    -- WHERE E.StateID = (SELECT ID FROM States WHERE StateName = 'Работает') -- ? Нужно ли только для работающих? ТЗ не уточняет. Пока оставим для всех.
    ORDER BY A.EmployeePersonnelNumber, A.AbsenceDate; -- Сортировка для удобства обработки
"""

# --- Пользователи ---
GET_USERS_BASE = """
    SELECT
        U.ID,                   -- 0: ID пользователя (для выбора)
        U.Login,                -- 1: Логин
        U.Password,             -- 2: Хеш пароля
        -- Получаем ФИО или Таб.номер сотрудника, если связан
        COALESCE(E.LastName || ' ' || E.FirstName || COALESCE(' ' || E.MiddleName, ''), U.EmployeePersonnelNumber, 'Не связан') AS EmployeeInfo, -- 3: Инфо о сотруднике
        R.RoleName,             -- 4: Название роли
        U.Email                 -- 5: Email
    FROM Users AS U
    JOIN Roles AS R ON U.RoleID = R.ID
    LEFT JOIN Employees AS E ON U.EmployeePersonnelNumber = E.PersonnelNumber -- LEFT JOIN, т.к. сотрудник может быть не связан
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
GET_USERS_COUNT_SEARCH = GET_USERS_SEARCH  # Условия поиска те же

GET_USER_BY_ID = "SELECT ID, Login, Password, EmployeePersonnelNumber, RoleID, Email FROM Users WHERE ID = ?"
GET_USER_BY_LOGIN_FOR_AUTH = "SELECT ID, Password, RoleID FROM Users WHERE Login = ?"  # Для входа

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

-- Таблица "Пол"
CREATE TABLE Genders (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    GenderName TEXT UNIQUE NOT NULL
);

-- Таблица "Подразделения"
CREATE TABLE Departments (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT UNIQUE NOT NULL,
    Description TEXT
);

-- Таблица "Должности"
CREATE TABLE Positions (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT UNIQUE NOT NULL,
    Description TEXT
);

-- Таблица "Состояния сотрудников"
CREATE TABLE States (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    StateName TEXT UNIQUE NOT NULL
);

-- Таблица "Сотрудники"
CREATE TABLE Employees (
    PersonnelNumber TEXT PRIMARY KEY,
    LastName TEXT NOT NULL,
    FirstName TEXT NOT NULL,
    MiddleName TEXT,
    BirthDate TEXT,  -- Формат: ГГГГ-ММ-ДД
    GenderID INTEGER,
    PositionID INTEGER,
    StateID INTEGER,
    DepartmentID INTEGER,
    FOREIGN KEY (GenderID) REFERENCES Genders(ID),
    FOREIGN KEY (PositionID) REFERENCES Positions(ID),
    FOREIGN KEY (StateID) REFERENCES States(ID),
    FOREIGN KEY (DepartmentID) REFERENCES Departments(ID)
);

-- Таблица "События"
CREATE TABLE Events (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    EventName TEXT UNIQUE NOT NULL  -- Прием, Увольнение, Перемещение
);

-- Таблица "Кадровые события сотрудников"
CREATE TABLE EmployeeEvents (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeePersonnelNumber TEXT NOT NULL,
    EventID INTEGER NOT NULL,
    EventDate TEXT,  -- Формат: ГГГГ-ММ-ДД
    DepartmentID INTEGER,
    PositionID INTEGER,
    Reason TEXT,
    FOREIGN KEY (EmployeePersonnelNumber) REFERENCES Employees(PersonnelNumber),
    FOREIGN KEY (EventID) REFERENCES Events(ID),
    FOREIGN KEY (DepartmentID) REFERENCES Departments(ID),
    FOREIGN KEY (PositionID) REFERENCES Positions(ID)
);

-- Таблица "Дни недели"
CREATE TABLE DaysOfTheWeek (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT UNIQUE NOT NULL
);

-- Таблица "Рабочие часы"
CREATE TABLE WorkingHours (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    StartingTime TEXT NOT NULL,  -- Формат: ЧЧ:ММ
    EndingTime TEXT NOT NULL    -- Формат: ЧЧ:ММ
);

-- Таблица "Графики работы"
CREATE TABLE Schedules (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	PositionID INTEGER NOT NULL,
	DayOfWeekID INTEGER NOT NULL,
	WorkingHoursID INTEGER NOT NULL,
	FOREIGN KEY (PositionID) REFERENCES Positions(ID),
	FOREIGN KEY (DayOfWeekID) REFERENCES DaysOfTheWeek(ID),
	FOREIGN KEY (WorkingHoursID) REFERENCES WorkingHours(ID)
);

-- Таблица "Отсутствия"
CREATE TABLE Absences (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeePersonnelNumber TEXT NOT NULL,
    AbsenceDate TEXT,  -- Формат: ГГГГ-ММ-ДД
    StartingTime TEXT,  -- Формат: ЧЧ:ММ (NULL, если FullDay = 1)
    EndingTime TEXT,    -- Формат: ЧЧ:ММ (NULL, если FullDay = 1)
    ScheduleID INTEGER, --NULLABLE
    FullDay INTEGER NOT NULL,  -- 0 - нет, 1 - да
    Reason TEXT,
    FOREIGN KEY (EmployeePersonnelNumber) REFERENCES Employees(PersonnelNumber),
   FOREIGN KEY (ScheduleID) REFERENCES Schedules(ID)
);

-- Таблица "Роли"
CREATE TABLE Roles (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoleName TEXT UNIQUE NOT NULL
);

-- Таблица "Пользователи"
CREATE TABLE Users (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Login TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    EmployeePersonnelNumber TEXT,
    RoleID INTEGER NOT NULL,
    Email TEXT,
    FOREIGN KEY (EmployeePersonnelNumber) REFERENCES Employees(PersonnelNumber),
    FOREIGN KEY (RoleID) REFERENCES Roles(ID)
);
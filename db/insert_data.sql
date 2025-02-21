-- Добавляем данные в таблицу Genders (Пол)
INSERT INTO Genders (GenderName) VALUES
('Мужской'),
('Женский');

-- Добавляем данные в таблицу Departments (Подразделения)
INSERT INTO Departments (Name, Description) VALUES
('Отдел кадров', 'Ведение кадрового учета'),
('Бухгалтерия', 'Финансовый учет и отчетность'),
('IT-отдел', 'Разработка и поддержка информационных систем'),
('Отдел продаж', 'Продажа товаров и услуг'),
('Юридический отдел', NULL);

-- Добавляем данные в таблицу Positions (Должности)
INSERT INTO Positions (Name, Description) VALUES
('Начальник отдела кадров', NULL),
('Специалист отдела кадров', NULL),
('Главный бухгалтер', NULL),
('Бухгалтер', NULL),
('Программист', 'Разработка ПО'),
('Системный администратор', NULL),
('Менеджер по продажам', NULL),
('Юрисконсульт', NULL);

-- Добавляем данные в таблицу States (Состояния сотрудников)
INSERT INTO States (StateName) VALUES
('Работает'),
('Уволен'),
('Недоступен'); -- Например, в отпуске по уходу за ребенком

-- Добавляем данные в таблицу Events (События)
INSERT INTO Events (EventName) VALUES
('Прием'),
('Увольнение'),
('Перемещение');

-- Добавляем данные в таблицу DaysOfTheWeek (Дни недели)
INSERT INTO DaysOfTheWeek (Name) VALUES
('Понедельник'),
('Вторник'),
('Среда'),
('Четверг'),
('Пятница'),
('Суббота'),
('Воскресенье');

-- Добавляем данные в таблицу WorkingHours (Рабочие часы)
INSERT INTO WorkingHours (StartingTime, EndingTime) VALUES
('09:00', '18:00'),  -- Стандартный рабочий день
('10:00', '19:00'),
('08:00', '17:00'),
('00:00', '00:00');


-- Добавляем данные в таблицу Roles (Роли)
INSERT INTO Roles (RoleName) VALUES
('Администратор'),
('Сотрудник отдела кадров'),
('Сотрудник');

-- Добавляем пользователя-администратора
INSERT INTO Users (Login, Password, EmployeePersonnelNumber, RoleID) VALUES
('admin', 'adminpassword', NULL, 1); -- Пароль ОЧЕНЬ плохой, нужен только для учебных целей!!!
-- Добавляем пользователя-сотрудника
INSERT INTO Users (Login, Password, EmployeePersonnelNumber, RoleID) VALUES
('kadrovik', '123', NULL, 2);
-- Добавляем несколько сотрудников (пример)
INSERT INTO Employees (PersonnelNumber, LastName, FirstName, MiddleName, BirthDate, GenderID, PositionID, StateID, DepartmentID) VALUES
('12345', 'Иванов', 'Иван', 'Иванович', '1980-05-10', 1, 5, 1, 3), -- Программист
('54321', 'Петрова', 'Мария', 'Сергеевна', '1992-11-20', 2, 7, 1, 4), -- Менеджер по продажам
('98765', 'Сидоров', 'Петр', 'Алексеевич', '1975-03-15', 1, 3, 1, 2); -- Главный бухгалтер

-- Добавляем несколько графиков работы (примеры)
-- Для должности "Программист" (PositionID = 5), стандартный график 5/2
INSERT INTO Schedules (PositionID, DayOfWeekID, WorkingHoursID) VALUES
(5, 1, 1), -- Пн, 09:00-18:00
(5, 2, 1), -- Вт, 09:00-18:00
(5, 3, 1), -- Ср, 09:00-18:00
(5, 4, 1), -- Чт, 09:00-18:00
(5, 5, 1), -- Пт, 09:00-18:00
(5, 6, 4), -- Сб, нерабочий
(5, 7, 4); -- Вс, нерабочий

-- Для должности "Менеджер по продажам" (PositionID = 7), тоже стандартный график
INSERT INTO Schedules (PositionID, DayOfWeekID, WorkingHoursID) VALUES
(7, 1, 2),
(7, 2, 2),
(7, 3, 2),
(7, 4, 2),
(7, 5, 2),
(7, 6, 4),
(7, 7, 4);

-- Для должности "Главный бухгалтер" (PositionID = 3), тоже стандартный график
INSERT INTO Schedules (PositionID, DayOfWeekID, WorkingHoursID) VALUES
(3, 1, 1),
(3, 2, 1),
(3, 3, 1),
(3, 4, 1),
(3, 5, 1),
(3, 6, 4),
(3, 7, 4);
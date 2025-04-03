# gui/dialogs/import_users_dialog.py
import customtkinter as ctk
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD  # Используем для Drag & Drop
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
import codecs  # Для utf-8-sig
import re
import datetime  # Для валидации пароля (если будет проверка на возраст и т.п.)
from db.user_repository import UserRepository  # Репозиторий пользователей
import os

log = logging.getLogger(__name__)


class ImportUsersDialog(ctk.CTkToplevel):
    """Диалог для импорта пользователей из CSV/XML."""

    def __init__(self, master, repository: UserRepository):
        super().__init__(master)
        self.repository = repository
        # Ссылка на родительский фрейм (UsersFrame) для обновления данных
        self.master_frame = master

        # Проверка и требование TkinterDnD
        try:
            TkinterDnD._require(self)
            self.dnd_enabled = True
        except tk.TclError:
            log.warning(
                "TkinterDnD не доступен. Drag & Drop для импорта пользователей будет отключен.")
            self.dnd_enabled = False

        self.title("Импорт пользователей")
        self.geometry("500x400")  # Размер как у других импортов
        self.resizable(False, False)
        self.grab_set()

        # Устанавливаем фон (можно убрать, если системный устраивает)
        # self.configure(bg="#000000")

        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты: область Drag&Drop и кнопку Отмена."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        # --- Область Drag & Drop ---
        drop_frame_border_color = "#4CAF50"  # Цвет как у кнопки импорта

        self.drop_frame = ctk.CTkFrame(
            frame, fg_color="#333333",  # Темный фон
            border_width=2, border_color=drop_frame_border_color
        )
        self.drop_frame.pack(fill="both", expand=True, pady=(0, 20))

        drop_text = "Перетащите файлы сюда (CSV или XML)"
        if not self.dnd_enabled:
            drop_text += "\n(Drag & Drop не доступен)"

        self.drop_label = ctk.CTkLabel(
            self.drop_frame, text=drop_text, font=("Arial", 16), text_color="white",
        )
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        # Привязка Drop, если DND доступен
        if self.dnd_enabled:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Кнопка Отмена ---
        self.cancel_button = ctk.CTkButton(
            frame, text="Отмена", command=self.destroy, width=100,
            fg_color=drop_frame_border_color,  # Тот же цвет, что и рамка
            hover_color="#66BB6A",  # Светлее при наведении
            text_color="white"
        )
        self.cancel_button.pack(side="bottom", pady=(0, 10))

    def handle_drop(self, event):
        """Обрабатывает событие перетаскивания файлов."""
        try:
            file_paths = self.tk.splitlist(event.data)
            if not file_paths:
                raise ValueError("Не удалось разобрать список файлов.")
        except Exception as e:
            log.error(f"Ошибка разбора файлов из event.data: {e}")
            messagebox.showerror("Ошибка Drag&Drop",
                                 "Не удалось определить перетащенные файлы.")
            return

        log.info(f"Перетащены файлы для импорта пользователей: {file_paths}")
        total_added = 0
        total_skipped = 0
        total_errors = 0
        processed_files = 0

        for path in file_paths:
            lower_path = path.lower()
            added, skipped, errors = 0, 0, 0  # Счетчики для файла
            try:
                if lower_path.endswith(".csv"):
                    added, skipped, errors = self.process_csv(path)
                elif lower_path.endswith(".xml"):
                    added, skipped, errors = self.process_xml(path)
                else:
                    messagebox.showwarning(
                        "Неверный формат", f"Файл '{os.path.basename(path)}' имеет неподдерживаемый формат (нужен CSV или XML).")
                    errors = 1
            except Exception as e:
                messagebox.showerror(
                    "Критическая ошибка", f"Ошибка при обработке файла '{os.path.basename(path)}':\n{e}")
                errors = 1
                log.exception(
                    f"Критическая ошибка при обработке файла импорта пользователей {path}")

            total_added += added
            total_skipped += skipped
            total_errors += errors
            processed_files += 1

        # Финальное сообщение
        messagebox.showinfo("Импорт пользователей завершен",
                            f"Обработано файлов: {processed_files}\n"
                            f"Добавлено пользователей: {total_added}\n"
                            f"Пропущено (дубликаты/ошибки данных): {total_skipped}\n"
                            f"Ошибки обработки файлов: {total_errors}")

        # Обновляем данные в родительском фрейме UsersFrame
        if self.master_frame and hasattr(self.master_frame, "load_data"):
            self.master_frame.load_data()
        if self.master_frame and hasattr(self.master_frame, "display_data"):
            self.master_frame.display_data()

    def process_csv(self, file_path):
        """Обрабатывает CSV файл с пользователями. Возвращает (added, skipped, errors)."""
        log.info(f"Обработка CSV пользователей: {file_path}")
        added, skipped = 0, 0
        # Обязательные поля (в нижнем регистре)
        required_headers = {"login", "password", "rolename"}
        # Опциональные поля
        optional_headers = {"employeepersonnelnumber", "email"}

        try:
            # Используем codecs для правильной работы с BOM
            with codecs.open(file_path, 'r', encoding='utf-8-sig') as file:
                # delimiter=';' - если разделитель точка с запятой
                # По умолчанию разделитель запятая
                reader = csv.DictReader(file)
                headers = {h.lower().strip()
                           for h in reader.fieldnames} if reader.fieldnames else set()

                # Проверка наличия обязательных заголовков
                if not required_headers.issubset(headers):
                    missing = required_headers - headers
                    messagebox.showerror(
                        "Ошибка CSV", f"Отсутствуют обязательные колонки в файле '{os.path.basename(file_path)}': {', '.join(missing)}")
                    return 0, 0, 1  # 1 ошибка файла

                line_num = 1  # Для логирования номера строки
                for row in reader:
                    line_num += 1
                    # Приводим ключи к нижнему регистру и удаляем пробелы
                    row_data_clean = {
                        k.lower().strip(): v for k, v in row.items() if k}
                    # Передаем очищенные данные на валидацию и вставку
                    if self.validate_and_insert_user_row(row_data_clean, f"CSV строка {line_num}"):
                        added += 1
                    else:
                        skipped += 1  # Ошибка валидации или дубликат = пропуск
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл не найден: {file_path}")
            return 0, 0, 1
        except Exception as e:
            messagebox.showerror(
                "Ошибка CSV", f"Ошибка чтения CSV файла пользователей '{os.path.basename(file_path)}':\n{e}")
            log.exception(f"Ошибка обработки CSV пользователей: {file_path}")
            return added, skipped, 1  # Считаем ошибкой файла
        return added, skipped, 0  # Нет ошибки файла

    def process_xml(self, file_path):
        """Обрабатывает XML файл с пользователями. Возвращает (added, skipped, errors)."""
        log.info(f"Обработка XML пользователей: {file_path}")
        added, skipped = 0, 0
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Ожидаем корневой тег <Users>
            if root.tag.lower() != "users":
                messagebox.showerror(
                    "Ошибка XML", f"Неверный корневой тег в файле '{os.path.basename(file_path)}' (ожидается <Users>).")
                return 0, 0, 1

            # Находим все записи <User>
            for index, user_node in enumerate(root.findall('User')):
                row_data = {}
                # Собираем данные из дочерних тегов, приводя теги к нижнему регистру
                for child in user_node:
                    tag_lower = child.tag.lower().strip()
                    value = child.text.strip() if child.text else ""
                    row_data[tag_lower] = value

                # Валидация и вставка
                if self.validate_and_insert_user_row(row_data, f"XML запись #{index + 1}"):
                    added += 1
                else:
                    skipped += 1
        except ET.ParseError as e:
            messagebox.showerror(
                "Ошибка XML", f"Ошибка разбора XML файла пользователей '{os.path.basename(file_path)}':\n{e}")
            return 0, 0, 1
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл не найден: {file_path}")
            return 0, 0, 1
        except Exception as e:
            messagebox.showerror(
                "Ошибка XML", f"Непредвиденная ошибка при обработке XML пользователей '{os.path.basename(file_path)}':\n{e}")
            log.exception(f"Ошибка обработки XML пользователей: {file_path}")
            return added, skipped, 1
        return added, skipped, 0

    def validate_and_insert_user_row(self, row_data, source_info=""):
        """
        Валидирует данные пользователя из строки (словаря) и вставляет в БД.
        Возвращает True при успехе, False при ошибке/пропуске.
        """
        # 1. Извлечение обязательных полей
        login = row_data.get('login', '').strip()
        # Пароль берем как есть, не удаляем пробелы
        password = row_data.get('password', '')
        role_name = row_data.get('rolename', '').strip()

        # 2. Извлечение опциональных полей
        employee_pn = row_data.get(
            'employeepersonnelnumber', '').strip() or None  # Если пусто, то None
        # Если пусто, то None
        email = row_data.get('email', '').strip() or None

        # 3. Проверка наличия обязательных полей
        if not (login and password and role_name):
            log.warning(
                f"Импорт пользователя пропущен ({source_info}): Не заполнены обязательные поля (login, password, rolename). Данные: {row_data}")
            return False

        # 4. Валидация логина
        if not re.match(r"^[a-zA-Z0-9_.-]+$", login):
            log.warning(
                f"Импорт пользователя пропущен ({source_info}): Некорректный формат логина '{login}'.")
            return False
        if not self.repository.is_login_unique(login):
            log.warning(
                f"Импорт пользователя пропущен ({source_info}): Логин '{login}' уже существует.")
            return False

        # 5. Валидация пароля (только на минимальную длину, т.к. требования из ТЗ могут быть строже)
        if len(password) < 8:  # Минимальная проверка для импорта
            log.warning(
                f"Импорт пользователя пропущен ({source_info}): Пароль для логина '{login}' слишком короткий (< 8 символов).")
            # Рекомендуется сообщить пользователю, что пароль нужно будет сменить
            # Можно либо пропустить, либо создать пользователя с временным/слабым паролем
            # Пропускаем для безопасности
            return False
        # Строгую проверку на цифры/регистр здесь не делаем, чтобы не усложнять импорт

        # 6. Поиск ID роли
        # Нужен метод в репозитории или загрузка карты ролей при инициализации диалога
        # Пока сделаем через прямой запрос (менее эффективно)
        role_result = self.repository.db.fetch_one(
            "SELECT ID FROM Roles WHERE RoleName = ?", (role_name,))
        if not role_result:
            log.warning(
                f"Импорт пользователя пропущен ({source_info}): Роль '{role_name}' не найдена в базе данных.")
            return False
        role_id = role_result[0]

        # 7. Проверка существования сотрудника (если указан)
        if employee_pn:
            # Нужен метод в EmployeeRepository или прямой запрос
            emp_exists = self.repository.db.fetch_one(
                "SELECT 1 FROM Employees WHERE PersonnelNumber = ?", (employee_pn,))
            if not emp_exists:
                log.warning(
                    f"Импорт пользователя '{login}' ({source_info}): Сотрудник с таб. номером '{employee_pn}' не найден. Пользователь будет создан без связи.")
                employee_pn = None  # Сбрасываем связь, если сотрудник не найден

        # 8. Валидация Email (если указан)
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            log.warning(
                f"Импорт пользователя '{login}' ({source_info}): Некорректный формат Email '{email}'. Email не будет сохранен.")
            email = None  # Не сохраняем невалидный email

        # 9. Вставка пользователя (пароль будет хеширован внутри add_user)
        try:
            success = self.repository.add_user(
                login=login,
                password=password,  # Передаем пароль в открытом виде
                role_id=role_id,
                employee_pn=employee_pn,
                email=email
            )
            if success:
                log.info(
                    f"Импорт ({source_info}): Успешно добавлен пользователь '{login}'.")
                return True
            else:
                # Ошибка могла произойти на уровне БД (например, constraint)
                log.error(
                    f"Импорт ({source_info}): Не удалось добавить пользователя '{login}' (ошибка репозитория/БД).")
                return False
        except Exception as e:
            log.exception(
                f"Импорт ({source_info}): Критическая ошибка при вставке пользователя '{login}'.")
            return False

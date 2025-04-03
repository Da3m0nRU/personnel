# gui/dialogs/add_user_dialog.py
import customtkinter as ctk
from config import *
import logging
from tkinter import messagebox
import re  # Для валидации
from db.user_repository import UserRepository  # Используем UserRepository

log = logging.getLogger(__name__)


class AddUserDialog(ctk.CTkToplevel):
    """Диалог для добавления нового пользователя."""

    def __init__(self, master, repository: UserRepository):
        super().__init__(master)
        self.repository = repository
        self.roles_map = {}  # Словарь для ID ролей
        self.employees_map = {}  # Словарь для Таб.№ сотрудников

        self.title("Добавить пользователя")
        self.geometry("450x600")  # Подберем размер
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.create_widgets()
        self.load_combobox_data()
        self.check_fields()  # Проверить состояние кнопки Save

    def create_widgets(self):
        """Создает виджеты диалога."""
        log.debug("Создание виджетов AddUserDialog")
        dialog_frame = ctk.CTkFrame(self, fg_color="transparent")
        dialog_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Логин
        ctk.CTkLabel(dialog_frame, text="Логин*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.login_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, width=380)
        self.login_entry.pack(anchor="w", pady=(2, 10))
        self.login_entry.bind("<KeyRelease>", self.check_fields)

        # Пароль
        ctk.CTkLabel(dialog_frame, text="Пароль*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.password_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, show="*", width=380)
        self.password_entry.pack(anchor="w", pady=(2, 10))
        self.password_entry.bind("<KeyRelease>", self.check_fields)

        # Подтверждение пароля
        ctk.CTkLabel(dialog_frame, text="Подтверждение пароля*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.confirm_password_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, show="*", width=380)
        self.confirm_password_entry.pack(anchor="w", pady=(2, 10))
        self.confirm_password_entry.bind("<KeyRelease>", self.check_fields)

        # Роль
        ctk.CTkLabel(dialog_frame, text="Роль*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.role_combo = ctk.CTkComboBox(
            dialog_frame, values=[], font=DEFAULT_FONT, width=380, state="readonly",
            command=self.check_fields
        )
        self.role_combo.pack(anchor="w", pady=(2, 10))

        # Связать с сотрудником
        ctk.CTkLabel(dialog_frame, text="Связать с сотрудником (опционально)",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.employee_combo = ctk.CTkComboBox(
            dialog_frame, values=[], font=DEFAULT_FONT, width=380, state="readonly"
            # command не нужен, т.к. поле опционально
        )
        self.employee_combo.pack(anchor="w", pady=(2, 10))

        # Email
        ctk.CTkLabel(dialog_frame, text="Email (опционально)",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.email_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, width=380)
        self.email_entry.pack(anchor="w", pady=(2, 20))
        # Email не влияет на активность кнопки Save

        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", side="bottom", pady=(10, 0))

        self.save_button = ctk.CTkButton(
            # Начинаем с disabled
            buttons_frame, text="Сохранить", command=self.save_user, font=DEFAULT_FONT, state="disabled"
        )
        self.save_button.pack(side="left", padx=(0, 10))

        cancel_button = ctk.CTkButton(
            buttons_frame, text="Отмена", command=self.cancel, font=DEFAULT_FONT, fg_color="gray"
        )
        cancel_button.pack(side="left")

        log.debug("Виджеты AddUserDialog созданы")

    def load_combobox_data(self):
        """Загружает роли и сотрудников в ComboBox'ы."""
        log.debug("Загрузка данных в комбобоксы AddUserDialog")
        try:
            # Роли
            # [(1, 'Админ'), (2, 'Кадровик'), ...]
            roles = self.repository.get_roles()
            # {'Админ': 1, 'Кадровик': 2}
            self.roles_map = {name: id for id, name in roles}
            role_names = list(self.roles_map.keys())
            self.role_combo.configure(values=role_names)
            if role_names:
                # Выбрать первую роль по умолчанию
                self.role_combo.set(role_names[0])
            log.debug(f"Загружено ролей: {len(role_names)}")

            # Сотрудники
            # ["Иванов И. (123)", ...]
            employees_raw = self.repository.get_active_employees_for_linking()
            # Формируем словарь для получения Таб.№ и добавляем опцию "Не связан"
            self.employees_map = {"Не связан": None}
            employee_display_list = ["Не связан"]
            for emp_str in employees_raw:
                match = re.search(r'\((\d+)\)$', emp_str)
                if match:
                    pn = match.group(1)
                    self.employees_map[emp_str] = pn
                    employee_display_list.append(emp_str)
                else:
                    log.warning(
                        f"Не удалось извлечь Таб.№ из строки сотрудника: {emp_str}")

            self.employee_combo.configure(values=employee_display_list)
            self.employee_combo.set("Не связан")  # По умолчанию не связан
            log.debug(
                f"Загружено сотрудников для связи: {len(employee_display_list)-1}")

        except Exception as e:
            log.exception(
                "Ошибка загрузки данных для комбобоксов AddUserDialog")
            messagebox.showerror(
                "Ошибка данных", "Не удалось загрузить справочники для формы.")

    def validate_input(self):
        """Валидирует введенные данные."""
        login = self.login_entry.get().strip()
        password = self.password_entry.get()  # Пароль берем как есть
        confirm_password = self.confirm_password_entry.get()
        role_name = self.role_combo.get()
        employee_display = self.employee_combo.get()
        email = self.email_entry.get().strip()

        # 1. Логин
        if not login:
            messagebox.showerror("Ошибка валидации",
                                 "Логин не может быть пустым.")
            return None
        if not re.match(r"^[a-zA-Z0-9_.-]+$", login):
            messagebox.showerror(
                "Ошибка валидации", "Логин может содержать только латинские буквы, цифры, точки, дефисы и подчеркивания.")
            return None
        if not self.repository.is_login_unique(login):
            messagebox.showerror("Ошибка валидации",
                                 f"Логин '{login}' уже занят.")
            return None

        # 2. Пароль
        if not password:
            messagebox.showerror("Ошибка валидации",
                                 "Пароль не может быть пустым.")
            return None
        if len(password) < 8:
            messagebox.showerror("Ошибка валидации",
                                 "Пароль должен быть не менее 8 символов.")
            return None
        if not re.search(r"\d", password):
            messagebox.showerror("Ошибка валидации",
                                 "Пароль должен содержать хотя бы одну цифру.")
            return None
        if not re.search(r"[a-z]", password):
            messagebox.showerror(
                "Ошибка валидации", "Пароль должен содержать хотя бы одну строчную латинскую букву.")
            return None
        if not re.search(r"[A-Z]", password):
            messagebox.showerror(
                "Ошибка валидации", "Пароль должен содержать хотя бы одну заглавную латинскую букву.")
            return None
        if password != confirm_password:
            messagebox.showerror("Ошибка валидации", "Пароли не совпадают.")
            return None

        # 3. Роль
        role_id = self.roles_map.get(role_name)
        if not role_id:
            messagebox.showerror("Ошибка валидации",
                                 "Не выбрана или не найдена роль.")
            return None

        # 4. Сотрудник (получаем Таб.№ или None)
        employee_pn = self.employees_map.get(employee_display)

        # 5. Email (опционально, но если есть - проверяем формат)
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Ошибка валидации",
                                 "Некорректный формат Email.")
            return None

        # Валидация пройдена
        validated_data = {
            "login": login,
            "password": password,  # Передаем пароль для хеширования в репозиторий
            "role_id": role_id,
            "employee_pn": employee_pn,
            "email": email if email else None
        }
        log.debug(
            f"Данные добавления пользователя прошли валидацию: { {k:v for k,v in validated_data.items() if k!='password'} }")
        return validated_data

    def save_user(self):
        """Сохраняет нового пользователя."""
        log.info("Попытка сохранения нового пользователя")
        validated_data = self.validate_input()
        if validated_data is None:
            log.warning("Валидация данных нового пользователя не пройдена.")
            return

        success = self.repository.add_user(**validated_data)

        if success:
            messagebox.showinfo(
                "Успех", f"Пользователь '{validated_data['login']}' успешно добавлен.")
            log.info(f"Пользователь '{validated_data['login']}' добавлен.")
            # Обновляем данные в родительском фрейме (UsersFrame)
            if self.master and hasattr(self.master, 'load_data'):
                self.master.load_data()
            if self.master and hasattr(self.master, 'display_data'):
                self.master.display_data()
            self.destroy()  # Закрываем диалог
        else:
            messagebox.showerror(
                "Ошибка", "Не удалось добавить пользователя в базу данных.")
            log.error(
                f"Ошибка при вызове add_user для логина '{validated_data['login']}'.")

    def check_fields(self, event=None):
        """Проверяет заполненность обязательных полей для активации кнопки 'Сохранить'."""
        login_ok = bool(self.login_entry.get().strip())
        # Пароль не должен быть пустым
        password_ok = bool(self.password_entry.get())
        confirm_ok = bool(self.confirm_password_entry.get())
        role_ok = bool(self.role_combo.get())

        can_save = login_ok and password_ok and confirm_ok and role_ok
        current_state = self.save_button.cget("state")

        if can_save and current_state == "disabled":
            self.save_button.configure(state="normal", fg_color="#0057FC")
        elif not can_save and current_state == "normal":
            self.save_button.configure(state="disabled", fg_color="gray")

    def cancel(self):
        """Закрывает диалог без сохранения."""
        log.debug("Закрытие диалога AddUserDialog без сохранения")
        self.destroy()

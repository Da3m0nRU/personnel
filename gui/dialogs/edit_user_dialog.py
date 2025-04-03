# gui/dialogs/edit_user_dialog.py
import customtkinter as ctk
from config import *
import logging
from tkinter import messagebox
import re
from db.user_repository import UserRepository

log = logging.getLogger(__name__)


class EditUserDialog(ctk.CTkToplevel):
    """Диалог для редактирования пользователя."""

    def __init__(self, master, repository: UserRepository, user_id, current_admin_id):
        super().__init__(master)
        self.repository = repository
        self.user_id = user_id
        self.current_admin_id = current_admin_id  # ID текущего админа для проверок
        self.original_data = None  # Для хранения исходных данных
        self.roles_map = {}
        self.employees_map = {}
        self.admin_role_id = self.repository.get_admin_role_id()  # ID роли админа

        self.title("Редактировать пользователя")
        self.geometry("450x650")  # Чуть выше из-за полей пароля
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.create_widgets()
        self.load_combobox_data()  # Сначала справочники
        if not self.load_user_data():  # Потом данные пользователя
            return  # Если не удалось загрузить, закрываемся

        self.check_fields()  # Проверить состояние кнопки Save

    def create_widgets(self):
        """Создает виджеты диалога."""
        log.debug(
            f"Создание виджетов EditUserDialog для User ID={self.user_id}")
        dialog_frame = ctk.CTkFrame(self, fg_color="transparent")
        dialog_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Логин (нередактируемый)
        ctk.CTkLabel(dialog_frame, text="Логин",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.login_label = ctk.CTkLabel(
            dialog_frame, text="...", font=DEFAULT_FONT, anchor="w")
        self.login_label.pack(anchor="w", pady=(2, 10), fill="x")

        # Роль
        ctk.CTkLabel(dialog_frame, text="Роль*",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.role_combo = ctk.CTkComboBox(
            dialog_frame, values=[], font=DEFAULT_FONT, width=380, state="readonly",
            command=self.check_fields
        )
        self.role_combo.pack(anchor="w", pady=(2, 10))

        # Связать с сотрудником
        ctk.CTkLabel(dialog_frame, text="Связать с сотрудником",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.employee_combo = ctk.CTkComboBox(
            dialog_frame, values=[], font=DEFAULT_FONT, width=380, state="readonly"
        )
        self.employee_combo.pack(anchor="w", pady=(2, 10))

        # Email
        ctk.CTkLabel(dialog_frame, text="Email",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.email_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, width=380)
        self.email_entry.pack(anchor="w", pady=(2, 20))

        # --- Поля для смены пароля ---
        ctk.CTkLabel(dialog_frame, text="Новый пароль (оставьте пустым, если не меняете)",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.new_password_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, show="*", width=380)
        self.new_password_entry.pack(anchor="w", pady=(2, 10))
        # Проверка нужна, если пароль меняется
        self.new_password_entry.bind("<KeyRelease>", self.check_fields)

        ctk.CTkLabel(dialog_frame, text="Подтверждение нового пароля",
                     font=DEFAULT_FONT).pack(anchor="w")
        self.confirm_new_password_entry = ctk.CTkEntry(
            dialog_frame, font=DEFAULT_FONT, show="*", width=380)
        self.confirm_new_password_entry.pack(anchor="w", pady=(2, 20))
        self.confirm_new_password_entry.bind(
            "<KeyRelease>", self.check_fields)  # Проверка нужна

        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", side="bottom", pady=(10, 0))

        self.save_button = ctk.CTkButton(
            buttons_frame, text="Сохранить", command=self.save_user, font=DEFAULT_FONT
        )
        self.save_button.pack(side="left", padx=(0, 10))

        cancel_button = ctk.CTkButton(
            buttons_frame, text="Отмена", command=self.cancel, font=DEFAULT_FONT, fg_color="gray"
        )
        cancel_button.pack(side="left")

        log.debug("Виджеты EditUserDialog созданы")

    def load_combobox_data(self):
        """Загружает роли и сотрудников в ComboBox'ы."""
        log.debug("Загрузка данных в комбобоксы EditUserDialog")
        try:
            # Роли
            roles = self.repository.get_roles()
            self.roles_map = {name: id for id, name in roles}
            role_names = list(self.roles_map.keys())
            self.role_combo.configure(values=role_names)
            log.debug(f"Загружено ролей: {len(role_names)}")

            # Сотрудники
            employees_raw = self.repository.get_active_employees_for_linking()
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
            log.debug(
                f"Загружено сотрудников для связи: {len(employee_display_list)-1}")

        except Exception as e:
            log.exception(
                "Ошибка загрузки данных для комбобоксов EditUserDialog")
            messagebox.showerror(
                "Ошибка данных", "Не удалось загрузить справочники для формы.")

    def load_user_data(self):
        """Загружает данные редактируемого пользователя в поля формы."""
        log.debug(
            f"Загрузка данных для User ID={self.user_id} в EditUserDialog")
        self.original_data = self.repository.get_user_by_id(self.user_id)
        if not self.original_data:
            messagebox.showerror(
                "Ошибка", f"Не удалось загрузить данные пользователя с ID={self.user_id}")
            log.error(
                f"Не найден пользователь с ID={self.user_id} для редактирования.")
            self.after(10, self.destroy)  # Закрыть диалог
            return False

        # original_data: (ID, Login, PasswordHash, EmployeePN, RoleID, Email)
        login, _, employee_pn, role_id, email = self.original_data[1], self.original_data[
            2], self.original_data[3], self.original_data[4], self.original_data[5]

        self.login_label.configure(text=login)
        self.email_entry.insert(0, email if email else "")

        # Установка роли
        role_name = next(
            (name for name, id_ in self.roles_map.items() if id_ == role_id), None)
        if role_name:
            self.role_combo.set(role_name)
        else:
            log.warning(f"Не найдено название для RoleID={role_id}")
            # Оставляем пустым или ставим первое значение? Лучше первое, если есть.
            if self.role_combo.cget("values"):
                self.role_combo.set(self.role_combo.cget("values")[0])

        # Установка связанного сотрудника
        employee_display = "Не связан"
        if employee_pn:
            employee_display = next(
                (disp for disp, pn in self.employees_map.items() if pn == employee_pn), "Не связан")
        self.employee_combo.set(employee_display)

        log.debug("Данные пользователя загружены в EditUserDialog.")
        return True

    def validate_input(self):
        """Валидирует введенные данные."""
        role_name = self.role_combo.get()
        employee_display = self.employee_combo.get()
        email = self.email_entry.get().strip()
        new_password = self.new_password_entry.get()
        confirm_new_password = self.confirm_new_password_entry.get()

        # 1. Роль
        role_id = self.roles_map.get(role_name)
        if not role_id:
            messagebox.showerror("Ошибка валидации",
                                 "Не выбрана или не найдена роль.")
            return None

        # --- Проверка на понижение роли последнего админа ---
        original_role_id = self.original_data[4]
        # Если роль изменилась И исходная роль была Админ И новая роль НЕ Админ
        if role_id != original_role_id and original_role_id == self.admin_role_id and role_id != self.admin_role_id:
            admin_count = self.repository.get_admin_count()
            if admin_count <= 1:
                messagebox.showerror(
                    "Ошибка валидации", "Нельзя понизить роль последнего администратора.")
                log.warning(
                    f"Попытка понизить роль последнего администратора (User ID={self.user_id})")
                return None
        # ----------------------------------------------------

        # 2. Сотрудник
        employee_pn = self.employees_map.get(employee_display)

        # 3. Email
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Ошибка валидации",
                                 "Некорректный формат Email.")
            return None

        # 4. Новый пароль (если введен)
        password_to_save = None
        if new_password or confirm_new_password:  # Если хотя бы одно поле заполнено
            if not new_password:
                messagebox.showerror("Ошибка валидации",
                                     "Введите новый пароль.")
                return None
            if len(new_password) < 8:
                messagebox.showerror(
                    "Ошибка валидации", "Новый пароль должен быть не менее 8 символов.")
                return None
            if not re.search(r"\d", new_password):
                messagebox.showerror(
                    "Ошибка валидации", "Новый пароль должен содержать хотя бы одну цифру.")
                return None
            if not re.search(r"[a-z]", new_password):
                messagebox.showerror(
                    "Ошибка валидации", "Новый пароль должен содержать хотя бы одну строчную латинскую букву.")
                return None
            if not re.search(r"[A-Z]", new_password):
                messagebox.showerror(
                    "Ошибка валидации", "Новый пароль должен содержать хотя бы одну заглавную латинскую букву.")
                return None
            if new_password != confirm_new_password:
                messagebox.showerror("Ошибка валидации",
                                     "Новые пароли не совпадают.")
                return None
            password_to_save = new_password  # Пароль валиден для сохранения
        # Если оба поля пароля пустые, password_to_save останется None

        validated_data = {
            "user_id": self.user_id,
            "role_id": role_id,
            "employee_pn": employee_pn,
            "email": email if email else None,
            "new_password": password_to_save  # Передаем пароль или None
        }
        log.debug(
            f"Данные редактирования пользователя прошли валидацию: { {k:v for k,v in validated_data.items() if k!='new_password'} }")
        return validated_data

    def save_user(self):
        """Сохраняет изменения пользователя."""
        log.info(f"Попытка сохранения изменений для User ID={self.user_id}")
        validated_data = self.validate_input()
        if validated_data is None:
            log.warning(
                "Валидация данных редактирования пользователя не пройдена.")
            return

        success = self.repository.update_user(**validated_data)

        if success:
            messagebox.showinfo(
                "Успех", f"Данные пользователя успешно обновлены.")
            log.info(f"Данные пользователя ID={self.user_id} обновлены.")
            if self.master and hasattr(self.master, 'load_data'):
                self.master.load_data()
            if self.master and hasattr(self.master, 'display_data'):
                self.master.display_data()
            self.destroy()
        else:
            messagebox.showerror(
                "Ошибка", "Не удалось обновить данные пользователя.")
            log.error(f"Ошибка при вызове update_user для ID={self.user_id}.")

    def check_fields(self, event=None):
        """Проверяет поля для активации кнопки 'Сохранить'."""
        role_ok = bool(self.role_combo.get())
        # Проверка пароля нужна только если он вводится
        password_fields_ok = True
        new_pass = self.new_password_entry.get()
        confirm_pass = self.confirm_new_password_entry.get()
        if new_pass or confirm_pass:  # Если начали менять пароль
            # Оба должны быть заполнены
            password_fields_ok = bool(new_pass and confirm_pass)

        can_save = role_ok and password_fields_ok
        current_state = self.save_button.cget("state")

        if can_save and current_state == "disabled":
            self.save_button.configure(state="normal", fg_color="#0057FC")
        elif not can_save and current_state == "normal":
            self.save_button.configure(state="disabled", fg_color="gray")

    def cancel(self):
        """Закрывает диалог без сохранения."""
        log.debug(
            f"Закрытие диалога EditUserDialog ID={self.user_id} без сохранения")
        self.destroy()

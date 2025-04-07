# gui/dialogs/confirm_event_dialog.py
import customtkinter as ctk
from config import *
import datetime
from tkinter import messagebox
import logging
import db.queries as q

log = logging.getLogger(__name__)


class ConfirmEventDialog(ctk.CTkToplevel):
    def __init__(self, master, event_type, employee_name, employee_event_repository, personnel_number,
                 department_id=None, position_id=None):
        super().__init__(master)
        self.event_type = event_type
        self.employee_name = employee_name
        self.employee_event_repository = employee_event_repository
        self.personnel_number = personnel_number
        self.department_id = department_id  # Может быть None
        self.position_id = position_id      # Может быть None
        self.master_window = master  # Ссылка на EditEmployeeDialog
        self.confirmed = False  # Добавляем атрибут-флаг

        self.title(event_type)
        self.geometry("500x300")  # Или другой подходящий размер
        self.resizable(False, False)
        self.create_widgets()
        self.grab_set()

    def create_widgets(self):

        log.debug("Создание виджетов ConfirmEventDialog")  # !!!

        title_label = ctk.CTkLabel(
            self, text=self.event_type, font=("Arial", 24, "bold"))
        title_label.pack(pady=(20, 10))

        if self.event_type == "Увольнение":
            text = f"Вы собираетесь уволить сотрудника {self.employee_name}.\nУкажите причину увольнения:"
        elif self.event_type == "Перемещение":
            text = (f"Вы собираетесь перевести сотрудника {self.employee_name} "
                    f"на новую должность/в новое подразделение.\nПри необходимости, укажите причину/комментарий:")
        elif self.event_type == "Недоступен":
            text = f"Вы собираетесь изменить статус сотрудника {self.employee_name} на \"Недоступен\".\nУкажите причину:"
        elif self.event_type == "Возвращение к работе":
            text = f"Вы собираетесь изменить статус сотрудника {self.employee_name} на \"Работает\".\nПри необходимости, укажите причину/комментарий:"
        else:  # "Прием"
            text = f"Вы собираетесь принять на работу сотрудника {self.employee_name}."

        text_label = ctk.CTkLabel(
            self, text=text, font=DEFAULT_FONT, wraplength=450, justify="left")
        text_label.pack(pady=(10, 5))

        #  Поле для ввода причины (многострочное).  Появляется, если НЕ "Прием".
        if self.event_type != "Прием":
            self.reason_textbox = ctk.CTkTextbox(
                self, height=80, font=DEFAULT_FONT)
            self.reason_textbox.pack(padx=20, pady=(5, 20), fill="x")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        confirm_button = ctk.CTkButton(button_frame, text="Подтвердить", command=self.confirm,
                                       fg_color="#0057FC", text_color="white",
                                       hover_color="#003580", width=120)  # !!! hover
        confirm_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Отмена", command=self.destroy,
                                      fg_color="gray", text_color="white",
                                      hover_color="dim gray", width=120)  # !!! hover

        cancel_button.pack(side="left", padx=10)

        log.debug("Виджеты ConfirmEventDialog созданы")  # !!!

    def confirm(self):
        log.info(f"Подтверждение кадрового события: {self.event_type}")

        reason = self.reason_textbox.get(
            "1.0", "end-1c").strip() if self.event_type != "Прием" else ""

        if self.event_type == "Увольнение" and not reason:
            messagebox.showerror("Ошибка", "Укажите причину увольнения.")
            log.warning("Не указана причина увольнения")
            return

        event_id = self.get_event_id(self.event_type)
        if event_id is None:
            messagebox.showerror(
                "Ошибка", f"Не удалось определить ID для события '{self.event_type}'")
            log.error(f"Не удалось определить ID события: {self.event_type}")
            return

        event_date = datetime.date.today().strftime("%Y-%m-%d")

        success = self.employee_event_repository.insert_event(
            self.personnel_number,
            event_id,
            event_date,
            self.department_id,
            self.position_id,
            reason
        )

        if success:
            messagebox.showinfo(
                "Успех", f"Событие '{self.event_type}' успешно зарегистрировано.")
            log.info(
                f"Кадровое событие {self.event_type} успешно зарегистрировано, таб.номер {self.personnel_number}")
            self.confirmed = True  # Устанавливаем флаг
            self.destroy()
            if self.master_window and hasattr(self.master_window, "display_data"):
                self.master_window.display_data()
        else:
            messagebox.showerror(
                "Ошибка", f"Не удалось зарегистрировать событие '{self.event_type}'.")
            log.error(
                f"Ошибка регистрации кадрового события {self.event_type} таб.номер {self.personnel_number}")

    def was_confirmed(self):
        """Возвращает True, если пользователь нажал 'Подтвердить', иначе False."""
        return self.confirmed

    def cancel(self):
        """Закрываем диалог без подтверждения."""
        self.destroy()

    def get_event_id(self, event_name):
        """Вспомогательный метод для получения ID события по названию."""
        print(
            f"Type of self.employee_event_repository: {type(self.employee_event_repository)}")
        print(
            f"Type of self.employee_event_repository.db: {type(self.employee_event_repository.db)}")
        event = self.employee_event_repository.db.fetch_one(
            q.GET_EVENT_ID_BY_NAME, (event_name,))
        return event[0] if event else None

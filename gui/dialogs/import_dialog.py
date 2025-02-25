# gui/dialogs/import_dialog.py

import customtkinter as ctk
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD  # Импортируем
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
from config import *
import re
import datetime

log = logging.getLogger(__name__)


class ImportDialog(ctk.CTkToplevel):  # !!! CTkToplevel
    def __init__(self, master, db):
        super().__init__(master)  # !!! CTkToplevel

        self.db = db
        self.title("Импорт данных")
        self.geometry("500x400")
        self.resizable(False, False)

        self.configure(bg="#000000")

        # !!! Важно: Инициализируем TkinterDnD для CustomTkinter !!!
        TkinterDnD._require(self)

        self.create_widgets()
        self.grab_set()

    def create_widgets(self):
        # --- Область для Drag & Drop ---
        self.drop_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            border_width=2,
            border_color="#f233f5"
        )
        self.drop_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.drop_label = ctk.CTkLabel(
            self.drop_frame,
            text="Перетащите файлы сюда (CSV или XML)",
            font=("Arial", 16),
            fg_color="transparent",
            text_color="white",
        )
        self.drop_label.pack(expand=True)

        # --- Привязываем события Drag and Drop ---
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind("<<Drop>>", self.handle_drop)

        # --- Кнопка "Отмена" ---
        self.cancel_button = ctk.CTkButton(
            self,
            text="Отмена",
            command=self.destroy,
            width=100,
            fg_color="#f233f5",
            hover_color="#DA70D6",
            text_color="white",
            border_width=0
        )
        self.cancel_button.pack(pady=(0, 20))

    def handle_drop(self, event):
        """Обрабатывает событие Drop (перетаскивание файлов)."""
        file_paths = self.parse_drop_files(event.data)
        log.info(f"Перетащены файлы: {file_paths}")

        for path in file_paths:
            if path.lower().endswith(".csv"):
                self.process_csv(path)
            elif path.lower().endswith(".xml"):
                self.process_xml(path)
            else:
                messagebox.showwarning(
                    "Предупреждение", f"Неподдерживаемый формат файла: {path}")
                log.warning(
                    f"Неподдерживаемый формат файла при импорте: {path}")

    def parse_drop_files(self, data_string):
        """
        Разбирает строку с путями к файлам, полученную от TkinterDnD.
        """
        paths = []
        current_path = ""
        in_braces = False

        for char in data_string:
            if char == "{" and not in_braces:
                in_braces = True
            elif char == "}" and in_braces:
                in_braces = False
                paths.append(current_path.strip())
                current_path = ""
            elif not in_braces and char == " ":
                if current_path:
                    paths.append(current_path.strip())
                current_path = ""
            else:
                current_path += char
        if current_path:
            paths.append(current_path.strip())
        return paths

    def process_csv(self, file_path):
        """Обрабатывает CSV-файл."""
        log.info(f"Обработка CSV файла: {file_path}")
        added_count = 0
        skipped_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if self.validate_and_insert_row(row):
                        added_count += 1
                    else:
                        skipped_count += 1

        except Exception as e:
            messagebox.showerror("Ошибка импорта CSV",
                                 f"Ошибка при обработке CSV: {e}")
            log.exception(f"Ошибка импорта из CSV {file_path}: {e}")
            return

        messagebox.showinfo("Импорт CSV",
                            f"Импорт завершен.\nДобавлено записей: {added_count}\nПропущено записей: {skipped_count}")

    def process_xml(self, file_path):
        """Обрабатывает XML-файл."""
        log.info(f"Обработка XML файла: {file_path}")
        added_count = 0
        skipped_count = 0
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for employee in root.findall('Employee'):
                row = {
                    'PersonnelNumber': employee.findtext('PersonnelNumber'),
                    'LastName': employee.findtext('LastName'),
                    'FirstName': employee.findtext('FirstName'),
                    'MiddleName': employee.findtext('MiddleName'),
                    'BirthDate': employee.findtext('BirthDate'),
                    'GenderName': employee.findtext('GenderName'),
                    'PositionName': employee.findtext('PositionName'),
                    'DepartmentName': employee.findtext('DepartmentName'),
                    'StateName': employee.findtext('StateName')
                }
                if self.validate_and_insert_row(row):
                    added_count += 1
                else:
                    skipped_count += 1

        except Exception as e:
            messagebox.showerror("Ошибка импорта XML",
                                 f"Ошибка при обработке XML: {e}")
            log.exception(f"Ошибка импорта из XML {file_path}: {e}")
            return

        messagebox.showinfo("Импорт XML",
                            f"Импорт завершен.\nДобавлено записей: {added_count}\nПропущено записей: {skipped_count}")

    def validate_and_insert_row(self, row):
        """
        Валидирует данные строки и вставляет их в базу данных.
        Возвращает True если успешно, False если ошибка.
        """
        personnel_number = row.get('PersonnelNumber', '').strip()
        lastname = row.get('LastName', '').strip()
        firstname = row.get('FirstName', '').strip()
        middlename = row.get('MiddleName', '').strip()
        birth_date_str = row.get('BirthDate', '').strip()
        gender_name = row.get('GenderName', '').strip()
        position_name = row.get('PositionName', '').strip()
        department_name = row.get('DepartmentName', '').strip()
        state_name = row.get('StateName', '').strip()

        if not all([personnel_number, lastname, firstname, birth_date_str, gender_name, position_name, department_name, state_name]):
            log.error(f"Ошибка импорта: Не все поля заполнены. Строка: {row}")
            return False

        if not re.match(r"^\d{1,10}$", personnel_number):
            log.error(
                f"Ошибка импорта: Некорректный табельный номер {personnel_number}!")
            return False

        if self.db.personnel_number_exists(personnel_number):
            log.warning(
                f"Ошибка импорта: дубликат табельного номера {personnel_number}")
            return False

        if not re.match(r"^[а-яА-ЯёЁ -]+$", lastname):
            log.error(f"Ошибка импорта: Некорректная фамилия: {lastname}")
            return False
        if not re.match(r"^[а-яА-ЯёЁ -]+$", firstname):
            log.error(f"Ошибка импорта: Некорректное имя: {firstname}")
            return False
        if middlename and not re.match(r"^[а-яА-ЯёЁ -]+$", middlename):
            log.error(f"Ошибка импорта: Некорректное отчество: {middlename}")
            return False
        if len(lastname) > 50 or len(firstname) > 50 or len(middlename) > 50:
            log.error(f"Ошибка импорта: Слишком длинное ФИО. Строка {row}")
            return False

        try:
            birth_date = datetime.datetime.strptime(
                birth_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            if birth_date > today:
                log.error(f"Ошибка импорта: Дата в будущем {birth_date_str}")
                return False

            age = today.year - birth_date.year - \
                ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                log.error(
                    f"Ошибка импорта: Сотрудник младше 18 {birth_date_str}")
                return False

        except ValueError:
            log.error(f"Ошибка импорта: Некорректная дата {birth_date_str}")
            return False

        gender_id = self.db.get_gender_id(gender_name)
        position_id = self.db.get_position_id(position_name)
        department_ids = self.db.get_department_by_name(department_name)
        department_id = [item[0]
                         for item in department_ids][0] if department_ids else None
        state_id = self.db.get_state_id(state_name)

        if gender_id is None or position_id is None or department_id is None or state_id is None:
            log.error(
                f"Ошибка импорта: Не найдены ID в справочниках. Строка: {row}")
            return False

        success = self.db.insert_employee(
            personnel_number, lastname, firstname, middlename, birth_date_str,
            gender_id, position_id, department_id, state_id
        )

        if not success:
            log.error(
                f"Ошибка при добавлении сотрудника {personnel_number} в БД")
            return False
        return True

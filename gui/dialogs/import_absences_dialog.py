# gui/dialogs/import_absences_dialog.py
import customtkinter as ctk
import tkinter as tk  # Для tk.TclError
from tkinterdnd2 import DND_FILES, TkinterDnD  # Используем для Drag & Drop
from tkinter import messagebox
import logging
import csv
import xml.etree.ElementTree as ET
import codecs  # Для utf-8-sig
import re  # Для валидации
import datetime  # Для валидации и определения дня недели
from db.absence_repository import AbsenceRepository  # Импортируем наш репозиторий
import os

log = logging.getLogger(__name__)


class ImportAbsencesDialog(ctk.CTkToplevel):  # Наследуемся от CTkToplevel
    """ Диалог для импорта данных об отсутствиях из CSV/XML. """

    def __init__(self, master, repository: AbsenceRepository):
        super().__init__(master)
        # Проверка и требование TkinterDnD
        try:
            TkinterDnD._require(self)
            self.dnd_enabled = True
        except tk.TclError:
            log.warning(
                "TkinterDnD не доступен. Drag & Drop для импорта будет отключен.")
            self.dnd_enabled = False

        self.repository = repository  # Репозиторий отсутствий
        # Ссылка на родительский фрейм (AbsencesFrame)
        self.master_frame = master

        self.title("Импорт отсутствий")
        self.geometry("500x400")  # Размер как у импорта сотрудников
        self.resizable(False, False)
        self.grab_set()

        # Сохраняем черный фон (если он нужен)
        # self.configure(bg="#000000") # Убрал, пусть будет системный

        self.create_widgets()

    def create_widgets(self):
        """ Создает виджеты: область Drag&Drop и кнопку Отмена. """
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        # --- Область Drag & Drop ---
        # Зеленый цвет (как у кнопки импорта)
        drop_frame_border_color = "#4CAF50"

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
        # Размещаем по центру
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
        """ Обрабатывает событие перетаскивания файлов. """
        # Пытаемся разобрать список файлов
        try:
            # Используем стандартный метод splitlist, он обычно работает лучше
            file_paths = self.tk.splitlist(event.data)
            if not file_paths:  # Если вернулся пустой кортеж
                raise ValueError("Не удалось разобрать список файлов.")
        except Exception as e:
            log.error(f"Ошибка разбора файлов из event.data: {e}")
            messagebox.showerror("Ошибка Drag&Drop",
                                 "Не удалось определить перетащенные файлы.")
            return

        log.info(f"Перетащены файлы: {file_paths}")
        total_added = 0
        total_skipped = 0
        total_errors = 0

        processed_files = 0
        for path in file_paths:
            # Проверяем расширение в нижнем регистре
            lower_path = path.lower()
            added, skipped, errors = 0, 0, 0  # Счетчик для текущего файла
            try:
                if lower_path.endswith(".csv"):
                    added, skipped, errors = self.process_csv(path)
                elif lower_path.endswith(".xml"):
                    added, skipped, errors = self.process_xml(path)
                else:
                    messagebox.showwarning(
                        "Неверный формат", f"Файл '{os.path.basename(path)}' имеет неподдерживаемый формат.")
                    errors = 1  # Считаем как ошибку обработки файла
            except Exception as e:
                messagebox.showerror(
                    "Критическая ошибка", f"Ошибка при обработке файла '{os.path.basename(path)}':\n{e}")
                errors = 1  # Считаем как ошибку
                log.exception(f"Критическая ошибка при обработке файла {path}")

            total_added += added
            total_skipped += skipped
            total_errors += errors
            processed_files += 1

        # Финальное сообщение по всем файлам
        messagebox.showinfo("Импорт завершен",
                            f"Обработано файлов: {processed_files}\n"
                            f"Добавлено записей: {total_added}\n"
                            f"Пропущено (дубликаты/ошибки данных): {total_skipped}\n"
                            f"Ошибки обработки файлов: {total_errors}")

        # Обновляем данные в родительском фрейме
        if self.master_frame and hasattr(self.master_frame, "load_data"):
            self.master_frame.load_data()
        if self.master_frame and hasattr(self.master_frame, "display_data"):
            self.master_frame.display_data()

    def process_csv(self, file_path):
        """ Обрабатывает CSV файл. Возвращает (added, skipped, errors). """
        log.info(f"Обработка CSV: {file_path}")
        added, skipped = 0, 0
        # Проверяем наличие в нижнем регистре
        required_headers = {"personnelnumber",
                            "absencedate", "fullday", "reason"}
        try:
            with codecs.open(file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                # Проверка заголовков (в нижнем регистре)
                headers = {h.lower().strip()
                           for h in reader.fieldnames} if reader.fieldnames else set()
                if not required_headers.issubset(headers):
                    missing = required_headers - headers
                    messagebox.showerror(
                        "Ошибка CSV", f"Отсутствуют обязательные колонки в файле '{os.path.basename(file_path)}': {', '.join(missing)}")
                    return 0, 0, 1  # 1 ошибка файла

                line_num = 1  # Для логирования номера строки
                for row in reader:
                    line_num += 1
                    # Переводим ключи строки в нижний регистр для унификации
                    row_lower = {k.lower().strip(): v for k,
                                 v in row.items() if k}
                    if self.validate_and_insert_absence_row(row_lower, f"CSV строка {line_num}"):
                        added += 1
                    else:
                        skipped += 1  # Ошибка валидации или дубликат = пропуск
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл не найден: {file_path}")
            return 0, 0, 1
        except Exception as e:
            messagebox.showerror(
                "Ошибка CSV", f"Ошибка чтения CSV файла '{os.path.basename(file_path)}':\n{e}")
            log.exception(f"Ошибка обработки CSV: {file_path}")
            return added, skipped, 1  # Считаем ошибкой файла
        return added, skipped, 0  # Нет ошибки файла

    def process_xml(self, file_path):
        """ Обрабатывает XML файл. Возвращает (added, skipped, errors). """
        log.info(f"Обработка XML: {file_path}")
        added, skipped = 0, 0
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            if root.tag.lower() != "absences":  # Ожидаем корневой тег <Absences>
                messagebox.showerror(
                    "Ошибка XML", f"Неверный корневой тег в файле '{os.path.basename(file_path)}' (ожидается <Absences>).")
                return 0, 0, 1

            # Находим все записи <Absence>
            for index, absence_node in enumerate(root.findall('Absence')):
                # Собираем данные из дочерних тегов
                row_data = {}
                for child in absence_node:
                    # Имя тега в нижний регистр, значение - текст (или пустая строка)
                    tag_lower = child.tag.lower().strip()
                    value = child.text.strip() if child.text else ""
                    row_data[tag_lower] = value

                if self.validate_and_insert_absence_row(row_data, f"XML запись #{index + 1}"):
                    added += 1
                else:
                    skipped += 1
        except ET.ParseError as e:
            messagebox.showerror(
                "Ошибка XML", f"Ошибка разбора XML файла '{os.path.basename(file_path)}':\n{e}")
            return 0, 0, 1
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл не найден: {file_path}")
            return 0, 0, 1
        except Exception as e:
            messagebox.showerror(
                "Ошибка XML", f"Непредвиденная ошибка при обработке XML '{os.path.basename(file_path)}':\n{e}")
            log.exception(f"Ошибка обработки XML: {file_path}")
            return added, skipped, 1
        return added, skipped, 0

    def validate_and_insert_absence_row(self, row_data, source_info=""):
        """
        Валидирует данные из строки (словаря) и вставляет в БД.
        Возвращает True при успехе, False при ошибке/пропуске.
        Логирует детали ошибок.
        """
        # 1. Извлечение и базовая проверка наличия
        pn = row_data.get('personnelnumber', '').strip()
        date_str = row_data.get('absencedate', '').strip()
        fullday_raw = row_data.get('fullday', '').strip()
        reason = row_data.get('reason', '').strip()
        # Может быть пустым для FullDay=1
        start_t = row_data.get('starttime', '').strip()
        # Может быть пустым для FullDay=1
        end_t = row_data.get('endtime', '').strip()

        if not (pn and date_str and fullday_raw and reason):
            log.warning(
                f"Импорт пропущен ({source_info}): Не заполнены обязательные поля (PersonnelNumber, AbsenceDate, FullDay, Reason). Данные: {row_data}")
            return False

        # 2. Валидация табельного номера (просто что цифры, существование проверим позже)
        if not pn.isdigit():
            log.warning(
                f"Импорт пропущен ({source_info}): Некорректный PersonnelNumber '{pn}'. Должен содержать только цифры.")
            return False

        # 3. Валидация и парсинг даты
        try:
            absence_date = datetime.datetime.strptime(
                date_str, "%Y-%m-%d").date()
        except ValueError:
            log.warning(
                f"Импорт пропущен ({source_info}): Некорректный формат AbsenceDate '{date_str}'. Ожидается ГГГГ-ММ-ДД.")
            return False

        # 4. Парсинг FullDay
        full_day = -1  # Невалидное значение
        if fullday_raw in ('1', 'true', 'yes', 'да'):
            full_day = 1
        elif fullday_raw in ('0', 'false', 'no', 'нет'):
            full_day = 0
        else:
            log.warning(
                f"Импорт пропущен ({source_info}): Некорректное значение FullDay '{fullday_raw}'. Ожидается 0/1/True/False/Да/Нет.")
            return False

        # 5. Валидация времени (если FullDay=0)
        start_time_final = None
        end_time_final = None
        schedule_id_final = None  # ID графика будем получать позже

        if full_day == 0:
            if not (start_t and end_t):
                log.warning(
                    f"Импорт пропущен ({source_info}): Для FullDay=0 не указаны StartTime и/или EndTime.")
                return False
            time_pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
            if not re.match(time_pattern, start_t) or not re.match(time_pattern, end_t):
                log.warning(
                    f"Импорт пропущен ({source_info}): Некорректный формат StartTime ('{start_t}') или EndTime ('{end_t}'). Ожидается ЧЧ:ММ.")
                return False
            try:
                t1 = datetime.datetime.strptime(start_t, "%H:%M").time()
                t2 = datetime.datetime.strptime(end_t, "%H:%M").time()
                if t1 >= t2:
                    log.warning(
                        f"Импорт пропущен ({source_info}): EndTime ('{end_t}') должен быть позже StartTime ('{start_t}').")
                    return False
                start_time_final = start_t
                end_time_final = end_t
            except ValueError:  # На всякий случай
                log.warning(
                    f"Импорт пропущен ({source_info}): Ошибка сравнения времени '{start_t}' - '{end_t}'.")
                return False
            schedule_id_final = None  # Ручной ввод времени -> ScheduleID=None

        # 6. Проверка существования сотрудника и получение его графика (если FullDay=1)
        position_id = self.repository.get_employee_position_id(pn)
        if not position_id:
            log.warning(
                f"Импорт пропущен ({source_info}): Сотрудник с PersonnelNumber '{pn}' не найден или не удалось определить его должность.")
            return False

        # 7. Получение ScheduleID и времени для FullDay=1 / Проверка времени для FullDay=0
        working_hours_info = None
        try:
            day_of_week = absence_date.isoweekday()
            working_hours_info = self.repository.get_working_hours(
                position_id, day_of_week)
        except Exception as e:
            log.error(
                f"Ошибка получения графика для PN={pn}, PosID={position_id}, Date={absence_date}: {e}")
            # Можно решить, пропускать ли запись или нет. Пока пропустим.
            log.warning(
                f"Импорт пропущен ({source_info}): Ошибка получения графика работы для сотрудника '{pn}'.")
            return False

        if full_day == 1:
            if working_hours_info:
                s_id, w_start, w_end = working_hours_info
                if w_start == "00:00" and w_end == "00:00":
                    log.warning(
                        f"Импорт пропущен ({source_info}): Попытка добавить отсутствие 'Полный день' на выходной ({absence_date}) для сотрудника '{pn}'.")
                    return False
                start_time_final = w_start
                end_time_final = w_end
                schedule_id_final = s_id
            else:
                log.warning(
                    f"Импорт пропущен ({source_info}): Не найден график работы для сотрудника '{pn}' на {absence_date} для установки 'Полный день'.")
                return False
        elif full_day == 0:  # Дополнительная проверка времени на вхождение в график
            if working_hours_info:
                _, w_start, w_end = working_hours_info
                try:
                    abs_s = datetime.datetime.strptime(
                        start_time_final, "%H:%M").time()
                    abs_e = datetime.datetime.strptime(
                        end_time_final, "%H:%M").time()
                    w_s = datetime.datetime.strptime(w_start, "%H:%M").time()
                    w_e = datetime.datetime.strptime(w_end, "%H:%M").time()
                    if not (w_s <= abs_s < abs_e <= w_e):
                        log.warning(
                            f"Импорт пропущен ({source_info}): Время '{start_time_final}-{end_time_final}' выходит за график '{w_start}-{w_end}' для сотрудника '{pn}' на {absence_date}.")
                        return False
                # Если w_start/w_end оказались невалидными (хотя не должны)
                except ValueError:
                    log.warning(
                        f"Импорт пропущен ({source_info}): Ошибка сравнения импортируемого времени с графиком для '{pn}'.")
                    return False
            else:  # Графика нет, как проверить? Лучше пропустить.
                log.warning(
                    f"Импорт пропущен ({source_info}): Не найден график для проверки времени '{start_time_final}-{end_time_final}' для сотрудника '{pn}'.")
                return False

        # 8. Проверка на дубликат (сотрудник + дата)
        if self.repository.absence_exists(pn, date_str):
            log.warning(
                f"Импорт пропущен ({source_info}): Запись об отсутствии для сотрудника '{pn}' на дату '{date_str}' уже существует.")
            return False

        # 9. Если все проверки пройдены, вставляем запись
        try:
            success = self.repository.insert_absence(
                personnel_number=pn,
                absence_date=date_str,
                full_day=full_day,
                start_time=start_time_final,  # Эти значения уже определены
                end_time=end_time_final,
                reason=reason,
                schedule_id=schedule_id_final  # Может быть None
            )
            if success:
                log.info(
                    f"Импорт ({source_info}): Успешно добавлена запись для '{pn}' на '{date_str}'.")
                return True
            else:
                log.error(
                    f"Импорт ({source_info}): Не удалось добавить запись для '{pn}' на '{date_str}' (ошибка репозитория).")
                return False
        except Exception as e:
            log.exception(
                f"Импорт ({source_info}): Критическая ошибка при вставке записи для '{pn}' на '{date_str}'.")
            return False

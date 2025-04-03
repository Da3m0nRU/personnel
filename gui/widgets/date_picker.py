# gui/widgets/date_picker.py
import customtkinter as ctk
import datetime
import calendar
import logging

log = logging.getLogger(__name__)


class DatePickerWidget(ctk.CTkFrame):
    """
    Простой виджет выбора даты с использованием CTkOptionMenu/CTkEntry.
    """

    def __init__(self, master, label_text="Дата:", default_date=None, command=None, font=None, **kwargs):
        """
        Инициализирует виджет выбора даты.

        Args:
            master: Родительский виджет.
            label_text (str): Текст метки перед полями даты.
            default_date (datetime.date, optional): Дата для установки по умолчанию.
            command (callable, optional): Функция, вызываемая при изменении даты.
                                            Принимает объект date или None.
            font: Шрифт для виджетов.
            **kwargs: Дополнительные аргументы для CTkFrame.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self._command = command
        self._font = font or ("Arial", 12)  # Шрифт по умолчанию

        # Карта и список месяцев
        self.month_map_int_str = {
            1: "Янв", 2: "Фев", 3: "Мар", 4: "Апр", 5: "Май", 6: "Июн",
            7: "Июл", 8: "Авг", 9: "Сен", 10: "Окт", 11: "Ноя", 12: "Дек"
        }
        self.month_map_str_int = {v: k for k,
                                  v in self.month_map_int_str.items()}
        self.month_names_short = list(self.month_map_int_str.values())

        # Диапазон лет для выбора
        current_year = datetime.date.today().year
        self.year_range = [str(y) for y in range(
            current_year - 80, current_year + 6)]  # Расширенный диапазон лет

        # CTk переменные для хранения текущих значений (текстовых)
        self._selected_day = ctk.StringVar(self)
        self._selected_month = ctk.StringVar(self)
        # _selected_year не нужна как StringVar, т.к. год в CTkEntry

        # --- Создание виджетов с использованием grid ---
        # Колонки виджетов не растягиваются
        self.grid_columnconfigure((1, 2, 3), weight=0)
        self.grid_columnconfigure(0, weight=0)  # Метка тоже

        # Метка (если текст задан)
        if label_text:
            self.label = ctk.CTkLabel(self, text=label_text, font=self._font)
            self.label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        # День (OptionMenu)
        self.day_combo = ctk.CTkOptionMenu(
            self, variable=self._selected_day, values=[], width=65,
            font=self._font, dynamic_resizing=False, state="readonly",
            command=self._date_changed  # Вызывает при выборе из списка
        )
        self.day_combo.grid(row=0, column=1, padx=2, pady=5)

        # Месяц (OptionMenu)
        self.month_combo = ctk.CTkOptionMenu(
            self, variable=self._selected_month, values=self.month_names_short, width=75,
            font=self._font, dynamic_resizing=False, state="readonly",
            command=self._date_changed  # Вызывает при выборе из списка
        )
        self.month_combo.grid(row=0, column=2, padx=2, pady=5)

        # Год (Entry)
        self.year_entry = ctk.CTkEntry(self, width=60, font=self._font)
        self.year_entry.grid(row=0, column=3, padx=2, pady=5)
        # Привязываем обработчики к изменению года
        # '+' для совмещения с другими биндами
        self.year_entry.bind("<KeyRelease>", self._year_entry_changed, add="+")
        self.year_entry.bind("<FocusOut>", self._year_entry_changed, add="+")

        # --- Инициализация состояния ---
        # Сначала установим месяц и год по умолчанию или текущие
        init_date = default_date or datetime.date.today()
        init_year_str = str(init_date.year)
        init_month_str = self.month_map_int_str.get(init_date.month)

        # Установка начального года и месяца
        self.year_entry.insert(0, init_year_str)
        if init_month_str:
            self._selected_month.set(init_month_str)
        else:
            self._selected_month.set(
                self.month_names_short[0])  # На случай ошибки

        # Обновляем список дней ДО установки дня
        self.update_days_list()

        # Устанавливаем день по умолчанию, если он валиден
        init_day_str = str(init_date.day)
        if init_day_str in self.day_combo.cget("values"):
            self._selected_day.set(init_day_str)
        else:  # Если дата по умолчанию была некорректной (напр. 31 апр)
            self._selected_day.set("")

    def update_days_list(self):
        """ Обновляет список дней в выпадающем списке `day_combo`. """
        current_day = self._selected_day.get()  # Запоминаем текущий выбор дня
        year_str = self.year_entry.get().strip()  # Берем год из Entry
        month_str = self._selected_month.get()  # Берем месяц из OptionMenu

        days_in_month = 31  # Значение по умолчанию
        try:
            if year_str.isdigit() and len(year_str) == 4 and month_str:
                year = int(year_str)
                month = self.month_map_str_int.get(month_str)
                if month and 1900 <= year <= 2100:  # Ограничиваем разумным диапазоном
                    days_in_month = calendar.monthrange(year, month)[1]
                else:
                    log.debug(
                        f"Невалидный месяц/год в update_days_list: {year_str}-{month_str}")
            else:
                log.debug(f"Год или месяц не заданы для update_days_list.")
        except (ValueError, TypeError) as e:
            log.warning(f"Ошибка при получении дней в месяце: {e}")
            # Остается 31 по умолчанию

        # Создаем новый список дней
        new_day_list = [str(i) for i in range(1, days_in_month + 1)]
        # Обновляем значения в ComboBox
        current_values = self.day_combo.cget("values")
        if current_values != new_day_list:  # Обновляем только если список изменился
            log.debug(f"Обновляем дни: {new_day_list}")
            self.day_combo.configure(values=new_day_list)
            # Пытаемся восстановить выбранный день, если он есть в новом списке
            if current_day in new_day_list:
                self._selected_day.set(current_day)
            else:
                # Сбрасываем день, если он стал невалидным
                self._selected_day.set("")
        # Если список дней не изменился, ничего не делаем

    def _year_entry_changed(self, event=None):
        """Обработчик изменения в поле года."""
        year_val = self.year_entry.get().strip()
        # Валидируем год: 4 цифры, в разумном диапазоне
        if year_val.isdigit() and len(year_val) == 4 and (1900 <= int(year_val) <= 2100):
            # Обновляем список дней (может измениться из-за високосного года)
            self.update_days_list()
            # Вызываем общий обработчик изменения даты
            self._date_changed()
        else:
            # Можно визуально пометить поле как некорректное
            pass  # Пока просто ничего не делаем, если год некорректен

    def _date_changed(self, event=None):
        """
        Внутренний обработчик изменения даты (вызывается при выборе дня/месяца или валидном изменении года).
        """
        # При изменении месяца - обновить дни обязательно
        # Мы это сделали в update_days_list, который вызывается перед этим методом или из year_entry_changed
        # self.update_days_list() # Можно раскомментировать для надежности, но может быть излишне

        selected_date = self.get_date()  # Пытаемся получить валидную дату
        log.debug(
            f"DatePicker: _date_changed вызван, получена дата: {selected_date}")
        if self._command:  # Если есть внешний обработчик
            try:
                # Передаем ему объект date или None
                self._command(selected_date)
            except Exception as e:
                log.error(f"Ошибка при вызове command DatePickerWidget: {e}")

    def get_date(self):
        """
        Возвращает выбранную дату как объект datetime.date или None, если дата некорректна.
        """
        day_str = self._selected_day.get()
        month_str = self._selected_month.get()
        year_str = self.year_entry.get().strip()  # Всегда берем актуальное из Entry

        if not (day_str and month_str and year_str):
            return None  # Не все компоненты выбраны

        try:
            day = int(day_str)
            month = self.month_map_str_int.get(month_str)
            year = int(year_str)

            # Проверяем валидность года и месяца
            if not (month and 1900 <= year <= 2100):
                return None
            # Проверяем валидность дня для этого месяца/года
            max_days = calendar.monthrange(year, month)[1]
            if not (1 <= day <= max_days):
                return None

            return datetime.date(year, month, day)
        except (ValueError, TypeError):  # Ошибка парсинга int или невалидный месяц
            return None

    def get_date_str(self):
        """
        Возвращает выбранную дату в формате "YYYY-MM-DD" или пустую строку, если дата некорректна.
        """
        date_obj = self.get_date()
        return date_obj.strftime("%Y-%m-%d") if date_obj else ""

    def set_date(self, date_obj):
        """
        Устанавливает дату в виджете.

        Args:
            date_obj (datetime.date): Объект даты для установки.
        """
        if not isinstance(date_obj, datetime.date):
            log.warning(f"Неверный тип для set_date: {type(date_obj)}")
            self.clear()
            return

        year_str = str(date_obj.year)
        month_str = self.month_map_int_str.get(date_obj.month)
        day_str = str(date_obj.day)

        # Проверяем, что дата в допустимых пределах виджета
        if month_str and (1900 <= date_obj.year <= 2100):
            # 1. Устанавливаем год в Entry
            self.year_entry.delete(0, "end")
            self.year_entry.insert(0, year_str)
            # 2. Устанавливаем месяц в OptionMenu
            self._selected_month.set(month_str)
            # 3. ОБЯЗАТЕЛЬНО обновляем список дней для этого месяца/года
            self.update_days_list()
            # 4. Устанавливаем день, ТОЛЬКО если он есть в обновленном списке
            if day_str in self.day_combo.cget("values"):
                self._selected_day.set(day_str)
            else:
                # Если день невалиден (напр., пытаемся поставить 31 февраля)
                log.warning(
                    f"Не удалось установить день {day_str} для {year_str}-{month_str}")
                self._selected_day.set("")  # Сбрасываем день
        else:
            log.warning(
                f"Дата {date_obj} некорректна или вне диапазона виджета.")
            self.clear()  # Очищаем поля, если дата невалидна

        # Не вызываем _date_changed(), чтобы избежать потенциальной рекурсии,
        # если set_date вызван из внешнего command обработчика.
        # Предполагается, что внешний код сам обработает последствие установки.

    def clear(self):
        """ Очищает выбор даты. """
        self._selected_day.set("")
        # Можно сбросить месяц/год на текущие или тоже очистить
        self._selected_month.set(
            self.month_names_short[datetime.date.today().month - 1])
        self.year_entry.delete(0, "end")
        self.year_entry.insert(0, str(datetime.date.today().year))
        self.update_days_list()
        # Вызываем обработчик, чтобы уведомить об изменении (дата стала None)
        self._date_changed()

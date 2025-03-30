# gui/reports_frame.py
import customtkinter as ctk
from config import *  # Импорт констант (цвета, шрифты и т.д.)
import logging
from .utils import load_icon  # Для иконок кнопок
import datetime  # Для валидации и обработки дат
from tkinter import messagebox
import matplotlib  # Явный импорт для возможной установки backend
# matplotlib.use('TkAgg') # Можно раскомментировать, если будут проблемы с backend
import matplotlib.pyplot as plt
# Для встраивания в Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure  # Явно создаем Figure
import matplotlib.dates as mdates  # Для форматирования дат на оси X
import matplotlib.ticker as mticker  # Для форматирования оси Y
from tksheet import Sheet  # Для таблицы результатов
import tkinter as tk  # Для tk.TOP и др.
import os  # Для создания папок экспорта
import csv  # Для экспорта в CSV
import codecs  # Для экспорта CSV с BOM

# Импортируем репозитории
from db.employee_event_repository import EmployeeEventRepository
from db.absence_repository import AbsenceRepository

log = logging.getLogger(__name__)


class ReportsFrame(ctk.CTkFrame):
    """
    Фрейм для формирования и отображения отчетов с вкладками для каждого отчета
    и внутренними вкладками "График" / "Таблица" для результатов.
    """

    def __init__(self, master, db):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        # Создаем экземпляры необходимых репозиториев
        self.event_repo = EmployeeEventRepository(self.db)
        self.absence_repo = AbsenceRepository(self.db)

        # Словарь для хранения данных сгенерированных отчетов (для экспорта)
        self.report_data_cache = {}

        self.create_widgets()

        # Установка дат по умолчанию (например, начало текущего месяца и сегодня)
        today = datetime.date.today()
        first_day_of_month = today.replace(day=1)
        today_str = today.strftime("%Y-%m-%d")
        first_day_str = first_day_of_month.strftime("%Y-%m-%d")

        if hasattr(self, 'dismissal_start_date_entry'):
            self.dismissal_start_date_entry.insert(0, first_day_str)
        if hasattr(self, 'dismissal_end_date_entry'):
            self.dismissal_end_date_entry.insert(0, today_str)
        if hasattr(self, 'absence_start_date_entry'):
            self.absence_start_date_entry.insert(0, first_day_str)
        if hasattr(self, 'absence_end_date_entry'):
            self.absence_end_date_entry.insert(0, today_str)

    def create_widgets(self):
        """ Создает базовую структуру вкладки отчетов. """
        log.debug("Создание виджетов для ReportsFrame")
        # Заголовок
        title_label = ctk.CTkLabel(
            self, text="ОТЧЕТЫ", font=TITLE_BOLD_FONT, text_color=LABEL_TEXT_COLOR, anchor="w")
        title_label.place(x=27, y=40)
        # Внешний Tabview
        self.report_type_tabview = ctk.CTkTabview(self)
        self.report_type_tabview.place(
            x=27, y=110, relwidth=0.96, relheight=0.85)
        # Добавляем вкладки
        self.report_type_tabview.add("Анализ увольнений")
        self.report_type_tabview.add("Анализ отсутствий")
        # Наполняем вкладки
        self.create_report_tab_content(
            self.report_type_tabview.tab("Анализ увольнений"), "dismissal")
        self.create_report_tab_content(
            self.report_type_tabview.tab("Анализ отсутствий"), "absence")
        log.debug("Базовые виджеты ReportsFrame созданы.")

    def create_report_tab_content(self, parent_tab, report_prefix):
        """ Создает содержимое для одной вкладки отчета. """
        log.debug(f"Создание контента для вкладки отчета: {report_prefix}")
        # --- Фрейм параметров ---
        # Выше для увольнений из-за группировки
        params_frame_height = 110 if report_prefix == "dismissal" else 80
        params_frame = ctk.CTkFrame(
            parent_tab, fg_color="transparent", height=params_frame_height)
        params_frame.pack(fill="x", padx=10, pady=(10, 5))
        params_frame.pack_propagate(False)

        # Даты
        ctk.CTkLabel(params_frame, text="Дата начала:",
                     font=DEFAULT_FONT).place(x=0, y=10)
        start_date_entry = ctk.CTkEntry(
            params_frame, placeholder_text="ГГГГ-ММ-ДД", width=150, font=DEFAULT_FONT)
        start_date_entry.place(x=110, y=10)
        ctk.CTkLabel(params_frame, text="Дата окончания:",
                     font=DEFAULT_FONT).place(x=0, y=45)
        end_date_entry = ctk.CTkEntry(
            params_frame, placeholder_text="ГГГГ-ММ-ДД", width=150, font=DEFAULT_FONT)
        end_date_entry.place(x=130, y=45)

        # Группировка графика (только для увольнений)
        if report_prefix == "dismissal":
            ctk.CTkLabel(params_frame, text="Группировка графика:",
                         font=DEFAULT_FONT).place(x=300, y=10)
            grouping_selector = ctk.CTkSegmentedButton(params_frame, values=[
                                                       "По дням", "По месяцам", "По годам"], font=DEFAULT_FONT, width=360, height=30)
            grouping_selector.place(x=480, y=10)
            grouping_selector.set("По месяцам")
            setattr(self, f"{report_prefix}_grouping_selector",
                    grouping_selector)

        # Кнопки
        generate_y = 70  # Сдвинуты вниз, если есть группировка
        export_y = 70
        # Кнопка Сформировать
        generate_btn = ctk.CTkButton(
            params_frame, text="  Сформировать", font=BOLD_FONT,
            command=lambda p=report_prefix: self.generate_report(p), width=200, height=40,
            corner_radius=12, image=load_icon("plus.png", size=(20, 20)), compound="left",
            fg_color=BUTTON_BG_COLOR, text_color="#0057FC", border_width=2, border_color="#0057FC", hover_color=BUTTON_HOVER_COLOR)
        generate_btn.place(x=300, y=generate_y)
        # Кнопка Экспорт
        export_btn = ctk.CTkButton(
            params_frame, text="  Экспорт", font=BOLD_FONT,
            command=lambda p=report_prefix: self.export_report_data(p), state="disabled",
            width=160, height=40, corner_radius=12, image=load_icon("export.png", size=(20, 20)),
            compound="left", fg_color=BUTTON_BG_COLOR, text_color="#2196F3", border_width=2,
            border_color="#2196F3", hover_color=BUTTON_HOVER_COLOR)
        export_btn.place(x=530, y=export_y)

        # Сохраняем ссылки
        setattr(self, f"{report_prefix}_start_date_entry", start_date_entry)
        setattr(self, f"{report_prefix}_end_date_entry", end_date_entry)
        setattr(self, f"{report_prefix}_generate_button", generate_btn)
        setattr(self, f"{report_prefix}_export_button", export_btn)

        # --- Внутренний Tabview для Графика/Таблицы ---
        results_tabview = ctk.CTkTabview(parent_tab)
        results_tabview.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        results_tabview.add("График")
        results_tabview.add("Таблица")
        # Контейнеры
        graph_cont = ctk.CTkFrame(
            results_tabview.tab("График"), fg_color="white")
        graph_cont.pack(expand=True, fill="both", padx=5, pady=5)
        table_cont = ctk.CTkFrame(
            results_tabview.tab("Таблица"), fg_color="white")
        table_cont.pack(expand=True, fill="both", padx=5, pady=5)
        # Заглушки
        ctk.CTkLabel(graph_cont, text="Задайте параметры и нажмите 'Сформировать'").place(
            relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(table_cont, text="Задайте параметры и нажмите 'Сформировать'").place(
            relx=0.5, rely=0.5, anchor="center")
        # Сохраняем ссылки
        setattr(self, f"{report_prefix}_graph_container", graph_cont)
        setattr(self, f"{report_prefix}_table_container", table_cont)
        setattr(self, f"{report_prefix}_results_tabview", results_tabview)

    def validate_dates(self, start_date_str, end_date_str):
        """ Проверяет корректность введенных дат. """
        try:
            start_date = datetime.datetime.strptime(
                start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d").date()
            if start_date > end_date:
                messagebox.showerror("Ошибка", ...)
                return None, None
            if (end_date - start_date).days > 365 * 10:  # Проверка > 10 лет
                if not messagebox.askyesno("Предупреждение", ...):
                    return None, None
                log.warning("Отчет > 10 лет.")
            return start_date, end_date
        except ValueError:
            messagebox.showerror("Ошибка", "Формат даты ГГГГ-ММ-ДД.")
            return None, None

    def generate_report(self, report_prefix):
        """ Общий обработчик кнопки 'Сформировать'. """
        log.info(f"Запрос отчета: {report_prefix}")
        # Получение виджетов и дат
        start_entry = getattr(self, f"{report_prefix}_start_date_entry")
        end_entry = getattr(self, f"{report_prefix}_end_date_entry")
        export_btn = getattr(self, f"{report_prefix}_export_button")
        graph_cont = getattr(self, f"{report_prefix}_graph_container")
        table_cont = getattr(self, f"{report_prefix}_table_container")
        start_str, end_str = start_entry.get().strip(), end_entry.get().strip()
        start_date, end_date = self.validate_dates(start_str, end_str)
        if start_date is None:
            log.warning("Отмена генерации (неверные даты)")
            return

        # Очистка и сообщение о загрузке
        log.debug(f"Очистка '{report_prefix}'")
        export_btn.configure(state="disabled")
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()
        self.report_data_cache.pop(f"{report_prefix}_graph", None)
        self.report_data_cache.pop(f"{report_prefix}_table", None)
        lg_g = ctk.CTkLabel(graph_cont, text="Загрузка...", font=DEFAULT_FONT)
        lg_g.place(relx=0.5, rely=0.5, anchor="center")
        lg_t = ctk.CTkLabel(table_cont, text="Загрузка...", font=DEFAULT_FONT)
        lg_t.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()

        # Вызов специфической генерации
        try:
            data_generated = False
            if report_prefix == "dismissal":
                grouping_sel = getattr(
                    self, f"{report_prefix}_grouping_selector")
                grouping_type = grouping_sel.get()
                log.debug(f"Группировка увольнений: {grouping_type}")
                data_generated = self._generate_dismissal_widgets(
                    start_date, end_date, grouping_type, graph_cont, table_cont)
            elif report_prefix == "absence":
                data_generated = self._generate_absence_widgets(
                    start_date, end_date, graph_cont, table_cont)

            if data_generated:
                export_btn.configure(state="normal")
                log.info(f"Отчет '{report_prefix}' ОК.")
            else:
                log.info(f"Отчет '{report_prefix}' - нет данных.")
        except Exception as e:  # Глобальная обработка ошибок генерации
            log.exception(f"Критич. ошибка генерации '{report_prefix}': {e}")
            messagebox.showerror("Ошибка", f"Ошибка формирования отчета:\n{e}")
            lg_g.destroy()
            lg_t.destroy()  # Убираем "Загрузка..."
            self._show_error_in_widget(graph_cont)
            self._show_error_in_widget(table_cont)

    def _generate_dismissal_widgets(self, start_date, end_date, grouping_type, graph_cont, table_cont):
        """ Генерирует ЛИНЕЙНЫЙ график и таблицу увольнений с явными метками. """
        log.debug(
            f"Генерация увольнений (линейный): {start_date}-{end_date}, Группа: {grouping_type}")

        # 1. Запрос данных для графика
        graph_data = None
        x_label_title = ''
        try:
            if grouping_type == "По дням":
                graph_data = self.event_repo.get_dismissal_counts_by_day(
                    str(start_date), str(end_date))
                x_label_title = 'День'
            elif grouping_type == "По годам":
                graph_data = self.event_repo.get_dismissal_counts_by_year(
                    str(start_date), str(end_date))
                x_label_title = 'Год'
            else:  # По месяцам
                graph_data = self.event_repo.get_dismissal_counts_by_month(
                    str(start_date), str(end_date))
                x_label_title = 'Месяц'
        except Exception as e:
            log.exception("Ошибка гр. данных")
            self._show_error_in_widget(graph_cont)
            graph_data = None

        # 2. Запрос данных для таблицы
        table_data = None
        try:
            table_data = self.event_repo.get_dismissed_employees_details(
                str(start_date), str(end_date))
        except Exception as e:
            log.exception("Ошибка табл. данных")
            self._show_error_in_widget(table_cont)
            table_data = None

        # Кэшируем то, что получили
        self.report_data_cache["dismissal_graph"] = graph_data
        self.report_data_cache["dismissal_table"] = table_data

        # Очистка
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()
        has_data = False  # Был ли сгенерирован хотя бы один виджет

        # 3. Строим график, если есть данные
        if graph_data:
            try:
                # Подготовка данных для осей
                # Оси X - это просто индексы
                x_indices = list(range(len(graph_data)))
                y_counts = [item[1]
                            for item in graph_data]  # Значения Y - количество
                x_tick_labels = []  # Метки для оси X
                rotation_angle = 25  # Угол поворота меток по умолчанию
                label_fontsize = 8  # Размер шрифта меток

                # Формируем метки X в зависимости от группировки
                if grouping_type == "По дням":
                    x_tick_labels = [datetime.datetime.strptime(
                        item[0], '%Y-%m-%d').strftime('%d.%m.%y') for item in graph_data]
                    rotation_angle = 45  # Увеличиваем угол для дат
                    label_fontsize = 7  # Уменьшаем шрифт, если дат много
                elif grouping_type == "По годам":
                    x_tick_labels = [item[0] for item in graph_data]
                    rotation_angle = 0  # Годы можно не поворачивать
                    label_fontsize = 9
                else:  # По месяцам
                    x_tick_labels = [datetime.datetime.strptime(
                        item[0] + '-01', '%Y-%m-%d').strftime('%b %Y') for item in graph_data]

                # Создаем фигуру и оси
                # Можно подбирать размеры
                fig = Figure(figsize=(7.5, 4.8), dpi=100)
                ax = fig.add_subplot(111)

                # Строим линейный график
                ax.plot(x_indices, y_counts, marker='o', linestyle='-',
                        color=ACCENT_COLOR, zorder=3, markersize=4)

                # Добавляем значения над точками
                for i, count in enumerate(y_counts):
                    if count > 0:
                        ax.annotate(int(count), (x_indices[i], count), textcoords="offset points", xytext=(
                            0, 4), ha='center', fontsize=7, zorder=4)

                # Настройки графика
                ax.set_ylabel('Кол-во уволенных', fontsize=9)
                ax.set_title(
                    f'Динамика увольнений ({grouping_type})', fontsize=11)
                ax.set_xlabel(x_label_title, fontsize=9)  # Подпись оси X

                # Устанавливаем тики и метки по индексам
                ax.set_xticks(x_indices)
                ax.set_xticklabels(
                    x_tick_labels, rotation=rotation_angle, ha='right', fontsize=label_fontsize)

                # Прореживание меток, если их слишком много
                current_ticks, current_labels = ax.get_xticks(), ax.get_xticklabels()
                if len(current_ticks) > 15:  # Эмпирическое значение, подбирать по месту
                    # Показываем около 10 меток
                    step = max(1, len(current_ticks) // 10)
                    ax.set_xticks(current_ticks[::step])
                    ax.set_xticklabels(current_labels[::step])

                ax.yaxis.set_major_locator(mticker.MaxNLocator(
                    integer=True, min_n_ticks=3))  # Целые на Y
                ax.grid(True, axis='both', linestyle=':',
                        alpha=0.5)  # Сетка для обоих осей
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_ylim(bottom=0)  # Y от нуля
                # Установка пределов X по индексам с отступом
                ax.set_xlim(x_indices[0]-0.5 if x_indices else -
                            0.5, x_indices[-1]+0.5 if x_indices else 0.5)

                fig.tight_layout()  # Компактное размещение

                # Встраивание в Tkinter
                canvas = FigureCanvasTkAgg(fig, master=graph_cont)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                has_data = True
            except Exception as e:
                log.exception("Ошибка построения графика")
                self._show_error_in_widget(graph_cont)
        else:
            self._show_no_data_in_widget(graph_cont)

        # 4. Таблица (Код без изменений, т.к. table_data не зависит от группировки графика)
        if table_data:
            try:
                headers = ["Таб.№", "ФИО", "Должность",
                           "Отдел", "Прием", "Увольн.", "Причина"]
                tf = ctk.CTkFrame(table_cont, fg_color="transparent")
                tf.pack(expand=True, fill='both')
                s = Sheet(tf, data=table_data, headers=headers,
                          font=TABLE_FONT, header_font=TABLE_HEADER_FONT)
                s.enable_bindings("single_select", "row_select",
                                  "column_width_resize", "arrowkeys", "copy")
                s.pack(expand=True, fill="both")
                s.readonly(True)
                has_data = True
            except Exception as e:
                log.exception("Ошибка таблицы")
                self._show_error_in_widget(table_cont)
        else:
            self._show_no_data_in_widget(table_cont)

        return has_data  # Возвращаем True, если были данные для графика или таблицы

    def _generate_absence_widgets(self, start_date, end_date, graph_cont, table_cont):
        """ Заглушка для отчета по отсутствиям. """
        log.debug(f"Заглушка генерации отсутствий: {start_date} - {end_date}")
        for w in graph_cont.winfo_children():
            w.destroy()
        for w in table_cont.winfo_children():
            w.destroy()
        self._show_error_in_widget(graph_cont, "Отчет\nв разработке")
        self._show_error_in_widget(table_cont, "Отчет\nв разработке")
        return False

    def export_report_data(self, report_prefix):
        """ Экспорт данных активной вкладки отчета в CSV. """
        log.info(f"Запрос на экспорт: {report_prefix}")
        results_tabview = getattr(self, f"{report_prefix}_results_tabview")
        active_tab = results_tabview.get()
        data_key_suffix = "graph" if active_tab == "График" else "table"
        data_key = f"{report_prefix}_{data_key_suffix}"
        data_to_export = self.report_data_cache.get(data_key)
        log.debug(f"Экспорт '{active_tab}' из '{data_key}'")

        if not data_to_export:
            messagebox.showwarning(...)
            log.warning(...)
            return

        headers = []
        fname = f"{report_prefix}_{active_tab.lower()}"
        if report_prefix == "dismissal":
            grouping_type = getattr(self, "dismissal_grouping_selector").get()
            fname = f"dismissal_{grouping_type.replace(' ','_').lower()}"
            if active_tab == "Таблица":
                headers = ["ТН", "ФИО", "Должн",
                           "Отд", "Прием", "Увольн", "Прич"]
                fname += "_table"
            else:  # График
                if grouping_type == "По дням":
                    headers = ["Дата (ГГГГ-ММ-ДД)", "Кол-во"]
                elif grouping_type == "По годам":
                    headers = ["Год", "Кол-во"]
                else:
                    headers = ["Месяц (ГГГГ-ММ)", "Кол-во"]
                fname += "_graph"
        elif report_prefix == "absence":
            log.warning("Экспорт отсутствий не реализован.")
            messagebox.showinfo("Инфо", "Экспорт этого отчета не готов.")
            return
            # TODO: Заголовки и имя файла для absence

        # Диалог сохранения файла
        export_dir = "export_reports"
        os.makedirs(export_dir, exist_ok=True)
        initial_f = f"{fname}_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
        fpath = ctk.filedialog.asksaveasfilename(initialdir=export_dir, initialfile=initial_f,
                                                 title="Экспорт данных", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not fpath:
            log.info("Отмена экспорта.")
            return

        # Запись в CSV
        try:
            with codecs.open(fpath, "w", "utf-8-sig") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data_to_export)
            log.info(f"Экспортировано: {fpath}")
            messagebox.showinfo("Успех", f"Сохранено:\n{fpath}")
        except Exception as e:
            log.exception(f"Ошибка экспорта {fpath}")
            messagebox.showerror("Ошибка", f"{e}")

    def _show_no_data_in_widget(self, container):
        """ Показывает 'Нет данных'. """
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text="Нет данных", font=DEFAULT_FONT,
                     text_color="grey").place(relx=0.5, rely=0.5, anchor="center")

    def _show_error_in_widget(self, container, text="Ошибка"):
        """ Показывает ошибку. """
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text=text, font=DEFAULT_FONT, text_color="red").place(
            relx=0.5, rely=0.5, anchor="center")

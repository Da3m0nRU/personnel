# gui/reports_frame.py
import customtkinter as ctk
from config import *
import logging
from .utils import load_icon
import datetime
from tkinter import messagebox
import matplotlib
# matplotlib.use('TkAgg') # На случай проблем с backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from tksheet import Sheet
import tkinter as tk
import os
import csv
import codecs

from db.employee_event_repository import EmployeeEventRepository
from db.absence_repository import AbsenceRepository

log = logging.getLogger(__name__)


class ReportsFrame(ctk.CTkFrame):
    """
    Фрейм для формирования и отображения отчетов.
    """

    def __init__(self, master, db):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        self.event_repo = EmployeeEventRepository(self.db)
        self.absence_repo = AbsenceRepository(self.db)
        self.report_data_cache = {}
        self.create_widgets()

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
        title_label = ctk.CTkLabel(
            self, text="ОТЧЕТЫ", font=TITLE_BOLD_FONT, text_color=LABEL_TEXT_COLOR, anchor="w")
        title_label.place(x=27, y=40)
        self.report_type_tabview = ctk.CTkTabview(self)
        self.report_type_tabview.place(
            x=27, y=110, relwidth=0.96, relheight=0.85)
        self.report_type_tabview.add("Анализ увольнений")
        self.report_type_tabview.add("Анализ отсутствий")
        self.create_report_tab_content(
            self.report_type_tabview.tab("Анализ увольнений"), "dismissal")
        self.create_report_tab_content(
            self.report_type_tabview.tab("Анализ отсутствий"), "absence")
        log.debug("Базовые виджеты ReportsFrame созданы.")

    def create_report_tab_content(self, parent_tab, report_prefix):
        """ Создает содержимое для одной вкладки отчета. """
        log.debug(f"Создание контента для вкладки отчета: {report_prefix}")
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

        # Группировка для увольнений
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
        generate_y = 70 if report_prefix == "dismissal" else 25
        export_y = generate_y
        generate_btn_style = {"font": BOLD_FONT, "width": 200, "height": 40, "corner_radius": 12, "image": load_icon("plus.png", size=(
            20, 20)), "compound": "left", "fg_color": BUTTON_BG_COLOR, "text_color": "#0057FC", "border_width": 2, "border_color": "#0057FC", "hover_color": BUTTON_HOVER_COLOR}
        export_btn_style = {"font": BOLD_FONT, "state": "disabled", "width": 160, "height": 40, "corner_radius": 12, "image": load_icon("export.png", size=(
            20, 20)), "compound": "left", "fg_color": BUTTON_BG_COLOR, "text_color": "#2196F3", "border_width": 2, "border_color": "#2196F3", "hover_color": BUTTON_HOVER_COLOR}

        generate_btn = ctk.CTkButton(params_frame, text="  Сформировать",
                                     command=lambda p=report_prefix: self.generate_report(p), **generate_btn_style)
        generate_btn.place(x=300, y=generate_y)
        export_btn = ctk.CTkButton(params_frame, text="  Экспорт",
                                   command=lambda p=report_prefix: self.export_report_data(p), **export_btn_style)
        export_btn.place(x=530, y=export_y)

        # Сохранение ссылок
        setattr(self, f"{report_prefix}_start_date_entry", start_date_entry)
        setattr(self, f"{report_prefix}_end_date_entry", end_date_entry)
        setattr(self, f"{report_prefix}_generate_button", generate_btn)
        setattr(self, f"{report_prefix}_export_button", export_btn)

        # Внутренний Tabview
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
        ctk.CTkLabel(graph_cont, text="Задайте параметры\nи нажмите 'Сформировать'").place(
            relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(table_cont, text="Задайте параметры\nи нажмите 'Сформировать'").place(
            relx=0.5, rely=0.5, anchor="center")
        # Сохранение ссылок
        setattr(self, f"{report_prefix}_graph_container", graph_cont)
        setattr(self, f"{report_prefix}_table_container", table_cont)
        setattr(self, f"{report_prefix}_results_tabview", results_tabview)

    def validate_dates(self, start_date_str, end_date_str):
        """ Проверяет корректность дат. Возвращает (date, date) или (None, None). """
        try:
            start = datetime.datetime.strptime(
                start_date_str, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if start > end:
                messagebox.showerror(
                    "Ошибка", "Дата начала не может быть позже даты окончания.")
                return None, None
            # Убрал предупреждение о > 10 лет для упрощения
            return start, end
        except ValueError:
            # Pylance может здесь ошибочно ругаться на start_str/end_str, но они определены как параметры.
            # Проблема в том, что strptime вызвал исключение ДО того, как мы что-то вернули.
            messagebox.showerror(
                "Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return None, None

    def generate_report(self, report_prefix):
        """ Общий обработчик 'Сформировать'. """
        log.info(f"Запрос отчета: {report_prefix}")
        start_entry = getattr(self, f"{report_prefix}_start_date_entry")
        end_entry = getattr(self, f"{report_prefix}_end_date_entry")
        export_btn = getattr(self, f"{report_prefix}_export_button")
        graph_cont = getattr(self, f"{report_prefix}_graph_container")
        table_cont = getattr(self, f"{report_prefix}_table_container")
        start_str, end_str = start_entry.get().strip(), end_entry.get().strip()
        start_date, end_date = self.validate_dates(start_str, end_str)
        if start_date is None:
            return

        log.debug(f"Очистка и загрузка для '{report_prefix}'")
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

        try:
            data_generated = False
            if report_prefix == "dismissal":
                grouping_type = getattr(
                    self, f"{report_prefix}_grouping_selector").get()
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
        except Exception as e:
            log.exception(f"Крит. ошибка генерации '{report_prefix}': {e}")
            messagebox.showerror("Ошибка", f"{e}")
            lg_g.destroy()
            lg_t.destroy()
            self._show_error_in_widget(graph_cont)
            self._show_error_in_widget(table_cont)

    def _calculate_total_absence_time(self, raw_data):
        """ Рассчитывает суммарное время отсутствия в часах для каждого сотрудника. """
        log.debug(f"Расчет сумм времени для {len(raw_data)} записей.")
        employee_totals = {}  # { PN: {"name": FullName, "total_minutes": total_minutes} }
        # Кэш графиков { (pos_id, day_id): duration_minutes_or_None }
        schedule_cache = {}
        DEFAULT_WORKDAY_MINUTES = 8 * 60  # 8 часов

        for row in raw_data:
            try:
                pn, name, pos_id, date_str, full_day, start_t, end_t, _ = row  # SchedID не нужен
                absence_date = datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').date()
                duration_minutes = 0
                if full_day == 1:
                    day_of_week_id = absence_date.isoweekday()
                    cache_key = (pos_id, day_of_week_id)
                    workday_minutes = schedule_cache.get(
                        cache_key, Ellipsis)  # Ellipsis как флаг "не искали"
                    if workday_minutes is Ellipsis:
                        schedule_info = self.absence_repo.get_working_hours(
                            pos_id, day_of_week_id)
                        if schedule_info:
                            _, w_start, w_end = schedule_info
                            if w_start != "00:00" or w_end != "00:00":
                                try:
                                    t_s = datetime.datetime.strptime(
                                        w_start, '%H:%M')
                                    t_e = datetime.datetime.strptime(
                                        w_end, '%H:%M')
                                    delta_m = (t_e-t_s).total_seconds()/60
                                    workday_minutes = delta_m if delta_m > 0 else None
                                except ValueError:
                                    workday_minutes = None
                            else:
                                workday_minutes = 0  # Выходной
                        else:
                            workday_minutes = None  # График не найден
                        # Кэшируем результат
                        schedule_cache[cache_key] = workday_minutes
                    duration_minutes = workday_minutes if workday_minutes is not None else DEFAULT_WORKDAY_MINUTES
                elif start_t and end_t:
                    try:
                        t_s = datetime.datetime.strptime(start_t, '%H:%M')
                        t_e = datetime.datetime.strptime(end_t, '%H:%M')
                        duration_minutes = (t_e-t_s).total_seconds()/60
                        duration_minutes = max(0, duration_minutes)  # Не < 0
                    except ValueError:
                        log.warning(f"Ошибка парсинга времени {row}")
                        duration_minutes = 0
                if duration_minutes > 0:
                    if pn not in employee_totals:
                        employee_totals[pn] = {
                            "name": name, "total_minutes": 0}
                    employee_totals[pn]["total_minutes"] += duration_minutes
            except Exception as e:
                log.exception(f"Ошибка обработки строки {row}: {e}")
        result = [(pn, data["name"], round(data["total_minutes"]/60, 2))
                  for pn, data in employee_totals.items()]
        result.sort(key=lambda i: i[2], reverse=True)
        log.info(f"Расчет сумм ОК: {len(result)}")
        return result

    def _generate_dismissal_widgets(self, start_date, end_date, grouping_type, graph_cont, table_cont):
        """ Генерирует ЛИНЕЙНЫЙ график и таблицу увольнений с явными метками. """
        log.debug(
            f"Генерация увольнений (лин.): {start_date}-{end_date}, Группа: {grouping_type}")
        # 1. Данные графика
        graph_data = None
        x_lbl = ''
        d_fmt = ''
        loc = None
        fmt = None
        has_data = False
        try:
            if grouping_type == "По дням":
                graph_data = self.event_repo.get_dismissal_counts_by_day(
                    str(start_date), str(end_date))
                x_lbl = 'День'
                d_fmt = '%Y-%m-%d'
                loc = mdates.DayLocator(interval=max(
                    1, (end_date-start_date).days//10+1))
                fmt = mdates.DateFormatter('%d.%m.%y')
            elif grouping_type == "По годам":
                graph_data = self.event_repo.get_dismissal_counts_by_year(
                    str(start_date), str(end_date))
                x_lbl = 'Год'
                d_fmt = '%Y'
                loc = mdates.YearLocator()
                fmt = mdates.DateFormatter('%Y')
            else:
                graph_data = self.event_repo.get_dismissal_counts_by_month(
                    str(start_date), str(end_date))
                x_lbl = 'Месяц'
                d_fmt = '%Y-%m'
                loc = mdates.MonthLocator(interval=max(
                    1, len(graph_data)//8 if graph_data else 1))
                fmt = mdates.DateFormatter('%b %y')
        except Exception as e:
            log.exception(...)
            self._show_error_in_widget(graph_cont)
            graph_data = None
        # 2. Данные таблицы
        table_data = None
        try:
            table_data = self.event_repo.get_dismissed_employees_details(
                str(start_date), str(end_date))
        except Exception as e:
            log.exception(...)
            self._show_error_in_widget(table_cont)
            table_data = None
        # Кэш
        self.report_data_cache["dismissal_graph"] = graph_data
        self.report_data_cache["dismissal_table"] = table_data
        # Очистка
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()
        # 3. График
        if graph_data:
            try:
                x_idx = list(range(len(graph_data)))
                y_cnt = [item[1] for item in graph_data]
                x_lbls = []
                rot_angle = 25
                lbl_fs = 8
                if grouping_type == "По дням":
                    x_lbls = [datetime.datetime.strptime(item[0], d_fmt).strftime(
                        '%d.%m.%y') for item in graph_data]
                    rot_angle = 45
                    lbl_fs = 7
                elif grouping_type == "По годам":
                    x_lbls = [item[0] for item in graph_data]
                    rot_angle = 0
                    lbl_fs = 9
                else:
                    x_lbls = [datetime.datetime.strptime(
                        item[0]+'-01', d_fmt+'-%d').strftime('%b %y') for item in graph_data]

                fig = Figure(figsize=(7.5, 4.8), dpi=95)
                ax = fig.add_subplot(111)
                ax.plot(x_idx, y_cnt, marker='o', linestyle='-',
                        color=ACCENT_COLOR, zorder=3, markersize=4)
                for i, c in enumerate(y_cnt):
                    if c > 0:
                        ax.annotate(int(c), (x_idx[i], c), textcoords="offset points", xytext=(
                            0, 4), ha='center', fontsize=7, zorder=4)
                ax.set_ylabel('Кол-во')
                ax.set_title(f'Увольнения ({grouping_type})')
                ax.set_xlabel(x_lbl)
                ax.set_xticks(x_idx)
                ax.set_xticklabels(x_lbls, rotation=rot_angle,
                                   ha='right', fontsize=lbl_fs)
                # Прореживание меток
                ticks_to_show = 12
                if len(x_idx) > ticks_to_show:
                    step = len(x_idx)//ticks_to_show
                    ax.set_xticks(x_idx[::step])
                    ax.set_xticklabels(x_lbls[::step])

                ax.yaxis.set_major_locator(
                    mticker.MaxNLocator(integer=True, min_n_ticks=3))
                ax.grid(True, axis='both', linestyle=':', alpha=0.5)
                ax.spines[['top', 'right']].set_visible(False)
                ax.set_ylim(bottom=0)
                # Установили пределы X по индексам
                ax.set_xlim(-0.5, len(x_idx)-0.5 if x_idx else 0.5)
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=graph_cont)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                has_data = True
            except Exception as e:
                log.exception(...)
                self._show_error_in_widget(graph_cont)
        else:
            self._show_no_data_in_widget(graph_cont)
        # 4. Таблица
        if table_data:
            try:
                hdrs = ["ТН", "ФИО", "Должн", "Отд", "Прием", "Увольн", "Прич"]
                tf = ctk.CTkFrame(table_cont, fg_color="transparent")
                tf.pack(ex=1, fill='both')
                s = Sheet(tf, data=table_data, headers=hdrs,
                          font=TABLE_FONT, header_font=TABLE_HEADER_FONT)
                s.enable_bindings("single_select", "row_select",
                                  "column_width_resize", "arrowkeys", "copy")
                s.pack(ex=1, fill='both')
                s.readonly(True)
                has_data = True
            except Exception as e:
                log.exception(...)
                self._show_error_in_widget(table_cont)
        else:
            self._show_no_data_in_widget(table_cont)
        return has_data

    # --- Генерация отчета по ОТСУТСТВИЯМ ---

    def _generate_absence_widgets(self, start_date, end_date, graph_cont, table_cont):
        """ Генерирует столбчатый график и таблицу сумм отсутствий. """
        log.debug(f"Генерация отсутствий: {start_date} - {end_date}")
        calculated_data = []
        has_data = False
        try:
            raw_data = self.absence_repo.get_raw_absence_data(
                str(start_date), str(end_date))
            if raw_data:
                calculated_data = self._calculate_total_absence_time(raw_data)
        except Exception as e:
            log.exception("Ошибка данных/расчета отсутствий")
            self._show_error_in_widget(graph_cont)
            self._show_error_in_widget(table_cont)
            return False
        # Кэш
        self.report_data_cache["absence_graph"] = calculated_data
        self.report_data_cache["absence_table"] = calculated_data
        # Очистка
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()

        # График (Топ N)
        if calculated_data:
            try:
                MAX_BARS = 15
                plot_data = calculated_data[:MAX_BARS]
                labels = [f"{item[1]}\n({item[0]})" for item in plot_data]
                hours = [item[2] for item in plot_data]
                indices = list(range(len(plot_data)))
                fig = Figure(figsize=(7.5, 4.8), dpi=95)
                ax = fig.add_subplot(111)
                bars = ax.bar(indices, hours,
                              color=SECONDARY_BG_COLOR, zorder=3)
                for bar in bars:
                    yval = bar.get_height()
                    if yval > 0.1:
                        ax.text(bar.get_x()+bar.get_width()/2., yval,
                                f'{yval:.1f} ч', va='bottom', ha='center', fontsize=8, zorder=4)
                ax.set_ylabel('Суммарные часы')
                ax.set_title(f'Время отсутствий (Топ-{len(plot_data)})')
                ax.set_xticks(indices)
                ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=7)
                ax.yaxis.set_major_locator(mticker.MaxNLocator(min_n_ticks=3))
                ax.grid(True, axis='y', linestyle=':', alpha=0.6)
                ax.spines[['top', 'right']].set_visible(False)
                ax.set_ylim(bottom=0)
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=graph_cont)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                has_data = True
            except Exception as e:
                log.exception("Ошибка графика отсутств.")
                self._show_error_in_widget(graph_cont)
        else:
            self._show_no_data_in_widget(graph_cont)
        # Таблица (Все)
        if calculated_data:
            try:
                headers = ["Таб.№", "ФИО", "Суммарные часы"]
                tf = ctk.CTkFrame(table_cont, fg_color="transparent")
                tf.pack(ex=1, fill='both')
                s = Sheet(tf, data=calculated_data, headers=headers,
                          font=TABLE_FONT, header_font=TABLE_HEADER_FONT)
                s.enable_bindings("single_select", "row_select",
                                  "column_width_resize", "arrowkeys", "copy")
                s.pack(ex=1, fill='both')
                s.readonly(True)
                has_data = True  # Подтверждаем наличие данных, если таблица создана
            except Exception as e:
                log.exception("Ошибка таблицы отсутств.")
                self._show_error_in_widget(table_cont)
        else:
            if not has_data:
                # Показываем "нет данных", только если и графика не было
                self._show_no_data_in_widget(table_cont)

        return has_data  # Возвращаем True, если были данные

    # --- Экспорт ---

    def export_report_data(self, report_prefix):
        log.info(f"Запрос на экспорт: {report_prefix}")
        results_tabview = getattr(self, f"{report_prefix}_results_tabview")
        active_tab = results_tabview.get()
        data_key = f"{report_prefix}_{'graph' if active_tab=='График' else 'table'}"
        data_to_export = self.report_data_cache.get(data_key)
        log.debug(f"Экспорт: '{active_tab}' из '{data_key}'")

        if not data_to_export:
            messagebox.showwarning("Нет данных", f"Нет данных для экспорта.")
            return

        headers = []
        fname = f"{report_prefix}_{active_tab.lower()}"
        if report_prefix == "dismissal":
            g_type = getattr(self, "dismissal_grouping_selector").get()
            fname = f"dismissal_{g_type.replace(' ','_').lower()}"
            if active_tab == "Таблица":
                headers = ["ТН", "ФИО", "Должн",
                           "Отд", "Прием", "Увольн", "Прич"]
                fname += "_table"
            else:
                if g_type == "По дням":
                    headers = ["Дата", "Кол-во"]
                elif g_type == "По годам":
                    headers = ["Год", "Кол-во"]
                else:
                    headers = ["Месяц", "Кол-во"]
                fname += "_graph"
        elif report_prefix == "absence":
            # Заголовки для absence (одинаковые для графика и таблицы в нашем случае)
            headers = ["Таб.№", "ФИО Сотрудника", "Суммарные часы отсутствия"]
            fname = "absence_summary"  # Имя не зависит от вкладки график/таблица

        # Диалог сохранения
        export_dir = "export_reports"
        os.makedirs(export_dir, exist_ok=True)
        initial_f = f"{fname}_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
        fpath = ctk.filedialog.asksaveasfilename(initialdir=export_dir, initialfile=initial_f,
                                                 title="Экспорт", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not fpath:
            log.info("Отмена.")
            return
        try:  # Запись CSV
            with codecs.open(fpath, "w", "utf-8-sig") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                    writer.writerows(data_to_export)
            log.info(f"Сохранено: {fpath}")
            messagebox.showinfo("Успех", f"Файл сохранен:\n{fpath}")
        except Exception as e:
            log.exception(f"Ошибка {fpath}")
            messagebox.showerror("Ошибка", f"{e}")

    # --- Вспомогательные ---

    def _show_no_data_in_widget(self, container):
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text="Нет данных\nдля этого периода", font=DEFAULT_FONT,
                     text_color="grey").place(relx=0.5, rely=0.5, anchor="center")

    def _show_error_in_widget(self, container, text="Ошибка\nгенерации"):
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text=text, font=DEFAULT_FONT, text_color="red").place(
            relx=0.5, rely=0.5, anchor="center")

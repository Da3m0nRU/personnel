# gui/reports_frame.py
import customtkinter as ctk
from config import *
import logging
from .utils import load_icon
import datetime
from tkinter import messagebox
import matplotlib
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
# !!! Импорт нового виджета !!!
from .widgets.date_picker import DatePickerWidget

log = logging.getLogger(__name__)

# Вспомогательные функции для стилей кнопок (чтобы не дублировать)


def generate_btn_style():
    return {"font": BOLD_FONT, "width": 200, "height": 40, "corner_radius": 12, "image": load_icon("plus.png", size=(20, 20)), "compound": "left", "fg_color": BUTTON_BG_COLOR, "text_color": "#0057FC", "border_width": 2, "border_color": "#0057FC", "hover_color": BUTTON_HOVER_COLOR}


def export_btn_style():
    return {"font": BOLD_FONT, "state": "disabled", "width": 160, "height": 40, "corner_radius": 12, "image": load_icon("export.png", size=(20, 20)), "compound": "left", "fg_color": BUTTON_BG_COLOR, "text_color": "#2196F3", "border_width": 2, "border_color": "#2196F3", "hover_color": BUTTON_HOVER_COLOR}


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

        # Установка дат по умолчанию через метод виджета
        today = datetime.date.today()
        first_day_of_month = today.replace(day=1)
        # first_day_of_year = today.replace(month=1, day=1)

        if hasattr(self, 'dismissal_start_date_picker'):
            self.dismissal_start_date_picker.set_date(first_day_of_month)
        if hasattr(self, 'dismissal_end_date_picker'):
            self.dismissal_end_date_picker.set_date(today)
        if hasattr(self, 'absence_start_date_picker'):
            self.absence_start_date_picker.set_date(first_day_of_month)
        if hasattr(self, 'absence_end_date_picker'):
            self.absence_end_date_picker.set_date(today)

    def create_widgets(self):
        """ Создает базовую структуру вкладки отчетов. """
        log.debug("Создание виджетов для ReportsFrame")
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
        log.debug(f"Создание контента для вкладки: {report_prefix}")
        # Фрейм параметров
        # Высота для группировки
        params_frame_height = 110 if report_prefix == "dismissal" else 80
        params_frame = ctk.CTkFrame(
            parent_tab, fg_color="transparent", height=params_frame_height)
        params_frame.pack(fill="x", padx=10, pady=(10, 5))
        params_frame.pack_propagate(False)
        # Настраиваем grid внутри params_frame
        params_frame.grid_columnconfigure(
            0, weight=0)  # Колонка с виджетами дат
        # Колонка с кнопками/группировкой
        params_frame.grid_columnconfigure(1, weight=0)
        # Пустая колонка для растягивания
        params_frame.grid_columnconfigure(2, weight=1)

        # --- Используем DatePickerWidget ---
        start_date_picker = DatePickerWidget(
            params_frame, label_text="Дата начала:", font=DEFAULT_FONT)
        start_date_picker.grid(row=0, column=0, padx=(
            0, 10), pady=(5, 2), sticky="w")  # row 0, col 0

        end_date_picker = DatePickerWidget(
            params_frame, label_text="Дата окончания:", font=DEFAULT_FONT)
        end_date_picker.grid(row=1, column=0, padx=(
            0, 10), pady=(2, 10), sticky="w")  # row 1, col 0

        # Размещаем кнопки и группировку в следующих колонках
        button_col_start = 1  # Колонка для кнопок

        # Группировка (только увольнения)
        if report_prefix == "dismissal":
            ctk.CTkLabel(params_frame, text="Группировка:", font=DEFAULT_FONT).grid(
                row=0, column=button_col_start, padx=(20, 5), pady=5, sticky="e")  # Выровнять по правому краю метку
            grouping_selector = ctk.CTkSegmentedButton(params_frame, values=[
                                                       "По дням", "По месяцам", "По годам"], font=DEFAULT_FONT, width=360, height=30)
            grouping_selector.grid(row=0, column=button_col_start + 1,
                                   columnspan=2, padx=5, pady=5, sticky="w")  # Занять две колонки
            grouping_selector.set("По месяцам")
            setattr(self, f"{report_prefix}_grouping_selector",
                    grouping_selector)

        # Кнопки генерации и экспорта (всегда в этих колонках)
        generate_btn = ctk.CTkButton(params_frame, text="  Сформировать",
                                     command=lambda p=report_prefix: self.generate_report(p), **generate_btn_style())
        generate_btn.grid(row=1, column=button_col_start,
                          padx=(20, 5), pady=(5, 10), sticky="w")

        export_btn = ctk.CTkButton(params_frame, text="  Экспорт",
                                   command=lambda p=report_prefix: self.export_report_data(p), **export_btn_style())
        export_btn.grid(row=1, column=button_col_start + 1,
                        padx=5, pady=(5, 10), sticky="w")

        # Сохраняем ссылки на DatePicker и кнопки
        setattr(self, f"{report_prefix}_start_date_picker", start_date_picker)
        setattr(self, f"{report_prefix}_end_date_picker", end_date_picker)
        setattr(self, f"{report_prefix}_generate_button", generate_btn)
        setattr(self, f"{report_prefix}_export_button", export_btn)

        # --- Внутренний Tabview и Контейнеры (без изменений) ---
        results_tabview = ctk.CTkTabview(parent_tab)
        results_tabview.pack(ex=1, fill='both', padx=10, pady=(0, 10))
        results_tabview.add("График")
        results_tabview.add("Таблица")
        graph_cont = ctk.CTkFrame(
            results_tabview.tab("График"), fg_color='white')
        graph_cont.pack(ex=1, fill='both', padx=5, pady=5)
        table_cont = ctk.CTkFrame(
            results_tabview.tab("Таблица"), fg_color='white')
        table_cont.pack(ex=1, fill='both', padx=5, pady=5)
        ctk.CTkLabel(graph_cont, text="Задайте параметры...").place(
            relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(table_cont, text="Задайте параметры...").place(
            relx=0.5, rely=0.5, anchor="center")
        setattr(self, f"{report_prefix}_graph_container", graph_cont)
        setattr(self, f"{report_prefix}_table_container", table_cont)
        setattr(self, f"{report_prefix}_results_tabview", results_tabview)

    # validate_dates БОЛЬШЕ НЕ НУЖЕН

    def generate_report(self, report_prefix):
        """ Общий обработчик 'Сформировать'. """
        log.info(f"Запрос отчета: {report_prefix}")
        # Получаем объекты дат из виджетов DatePickerWidget
        start_picker = getattr(self, f"{report_prefix}_start_date_picker")
        end_picker = getattr(self, f"{report_prefix}_end_date_picker")
        start_date = start_picker.get_date()  # Возвращает date или None
        end_date = end_picker.get_date()    # Возвращает date или None

        export_btn = getattr(self, f"{report_prefix}_export_button")
        graph_cont = getattr(self, f"{report_prefix}_graph_container")
        table_cont = getattr(self, f"{report_prefix}_table_container")

        # Проверка корректности дат
        if start_date is None or end_date is None:
            messagebox.showerror(
                "Ошибка", "Выберите корректные дату начала и дату окончания.")
            log.warning(
                f"Генерация '{report_prefix}' отменена: некорректные даты")
            return
        if start_date > end_date:
            messagebox.showerror(
                "Ошибка", "Дата начала не может быть позже даты окончания.")
            log.warning(f"Генерация '{report_prefix}' отменена: start > end")
            return

        log.debug(
            f"Очистка и загрузка для '{report_prefix}' ({start_date} - {end_date})")
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
            # !!! Передаем объекты date в методы генерации !!!
            if report_prefix == "dismissal":
                grouping_type = getattr(
                    self, "dismissal_grouping_selector").get()
                data_generated = self._generate_dismissal_widgets(
                    start_date, end_date, grouping_type, graph_cont, table_cont)
            elif report_prefix == "absence":
                data_generated = self._generate_absence_widgets(
                    start_date, end_date, graph_cont, table_cont)

            if data_generated:
                export_btn.configure(state="normal")
                log.info(f"Отчет '{report_prefix}' OK.")
            else:
                log.info(f"Отчет '{report_prefix}' - нет данных.")
        except Exception as e:
            log.exception(f"Крит. ошибка '{report_prefix}': {e}")
            messagebox.showerror("Ошибка", f"{e}")
            lg_g.destroy()
            lg_t.destroy()
            self._show_error_in_widget(graph_cont)
            self._show_error_in_widget(table_cont)

    def _calculate_total_absence_time(self, raw_data):
        """ Рассчитывает суммарное время отсутствия в часах. """
        # ... (Код расчета БЕЗ ИЗМЕНЕНИЙ) ...
        log.debug(f"Расчет сумм времени для {len(raw_data)} записей.")
        employee_totals = {}
        schedule_cache = {}
        DEFAULT_WORKDAY_MINUTES = 8 * 60
        for row in raw_data:
            try:
                pn, name, pos_id, date_str, full_day, start_t, end_t, _ = row
                absence_date = datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').date()
                duration_minutes = 0
                if full_day == 1:
                    day_id = absence_date.isoweekday()
                    key = (pos_id, day_id)
                    wk_m = schedule_cache.get(key, Ellipsis)
                    if wk_m is Ellipsis:
                        info = self.absence_repo.get_working_hours(
                            pos_id, day_id)
                        wk_m = None
                        if info:
                            _, w_s, w_e = info
                            if w_s != "00:00" or w_e != "00:00":
                                try:
                                    t_s = datetime.datetime.strptime(
                                        w_s, '%H:%M')
                                    t_e = datetime.datetime.strptime(
                                        w_e, '%H:%M')
                                    delta = (t_e-t_s).total_seconds()/60
                                    wk_m = delta if delta > 0 else None
                                except ValueError:
                                    pass
                            else:
                                wk_m = 0  # Выходной
                        schedule_cache[key] = wk_m
                    duration_minutes = wk_m if wk_m is not None else DEFAULT_WORKDAY_MINUTES
                elif start_t and end_t:
                    try:
                        t_s = datetime.datetime.strptime(start_t, '%H:%M')
                        t_e = datetime.datetime.strptime(end_t, '%H:%M')
                        duration_minutes = max(0, (t_e-t_s).total_seconds()/60)
                    except ValueError:
                        duration_minutes = 0
                if duration_minutes > 0:
                    if pn not in employee_totals:
                        employee_totals[pn] = {
                            "name": name, "total_minutes": 0}
                    employee_totals[pn]["total_minutes"] += duration_minutes
            except Exception as e:
                log.exception(f"Ошибка строки {row}: {e}")
        result = [(pn, data["name"], round(data["total_minutes"]/60, 2))
                  for pn, data in employee_totals.items()]
        result.sort(key=lambda i: i[2], reverse=True)
        log.info(f"Расчет сумм ОК: {len(result)}")
        return result

    def _generate_dismissal_widgets(self, start_date, end_date, grouping_type, graph_cont, table_cont):
        """ Генерирует ЛИНЕЙНЫЙ график и таблицу увольнений. """
        log.debug(
            f"Генерация увольнений (лин.): {start_date}-{end_date}, Группа: {grouping_type}")
        graph_data = None
        table_data = None
        has_data = False
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        try:  # Получаем данные графика
            if grouping_type == "По дням":
                graph_data = self.event_repo.get_dismissal_counts_by_day(
                    start_str, end_str)
            elif grouping_type == "По годам":
                graph_data = self.event_repo.get_dismissal_counts_by_year(
                    start_str, end_str)
            else:
                graph_data = self.event_repo.get_dismissal_counts_by_month(
                    start_str, end_str)
        except Exception as e:
            log.exception(...)
            self._show_error_in_widget(graph_cont)
        try:  # Данные таблицы
            table_data = self.event_repo.get_dismissed_employees_details(
                start_str, end_str)
        except Exception as e:
            log.exception(...)
            self._show_error_in_widget(table_cont)

        self.report_data_cache["dismissal_graph"] = graph_data
        self.report_data_cache["dismissal_table"] = table_data
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()

        # График
        if graph_data:
            try:
                x_indices = list(range(len(graph_data)))
                y_counts = [item[1] for item in graph_data]
                x_labels = []
                rot = 25
                fs = 8
                title_lbl = grouping_type
                if grouping_type == "По дням":
                    x_labels = [datetime.datetime.strptime(
                        i[0], '%Y-%m-%d').strftime('%d.%m.%y') for i in graph_data]
                    rot = 45
                    fs = 7
                    title_lbl = "по Дням"
                elif grouping_type == "По годам":
                    x_labels = [i[0] for i in graph_data]
                    rot = 0
                    fs = 9
                    title_lbl = "по Годам"
                else:
                    x_labels = [datetime.datetime.strptime(
                        i[0]+'-01', '%Y-%m-%d').strftime('%b %y') for i in graph_data]
                    title_lbl = "по Месяцам"

                fig = Figure(figsize=(7.5, 4.8), dpi=95)
                ax = fig.add_subplot(111)
                ax.plot(x_indices, y_counts, marker='o', ls='-',
                        color=ACCENT_COLOR, zorder=3, ms=4)
                for i, c in enumerate(y_counts):
                    if c > 0:
                        ax.annotate(int(c), (x_indices[i], c), textcoords="offset points", xytext=(
                            0, 4), ha='center', fontsize=7, zorder=4)
                ax.set_ylabel('Кол-во')
                ax.set_title(f'Увольнения ({title_lbl})')  # ax.set_xlabel(...)
                ax.set_xticks(x_indices)
                ax.set_xticklabels(x_labels, rotation=rot,
                                   ha='right', fontsize=fs)
                # Прореживание
                ticks_to_show = 15
                if len(x_indices) > ticks_to_show:
                    step = len(x_indices)//ticks_to_show
                    ax.set_xticks(x_indices[::step])
                    ax.set_xticklabels(x_labels[::step])
                ax.yaxis.set_major_locator(
                    mticker.MaxNLocator(integer=True, min_n_ticks=3))
                ax.grid(True, axis='both', ls=':', alpha=0.5)
                ax.spines[['top', 'right']].set_visible(False)
                ax.set_ylim(bottom=0)
                ax.set_xlim(-0.5, len(x_indices)-0.5 if x_indices else 0.5)
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
        # Таблица
        if table_data:
            try:
                hdrs = ["ТН", "ФИО", "Должн", "Отд", "Прием", "Увольн", "Прич"]
                tf = ctk.CTkFrame(table_cont, fg_color='transparent')
                tf.pack(ex=1, fill='both')
                s = Sheet(tf, data=table_data, headers=hdrs,
                          font=TABLE_FONT, header_font=TABLE_HEADER_FONT)
                s.enable_bindings("copy")
                s.pack(ex=1, fill='both')
                s.readonly(True)
                has_data = True
            except Exception as e:
                log.exception(...)
                self._show_error_in_widget(table_cont)
        else:
            if not has_data:
                # Показываем "нет данных" если и графика нет
                self._show_no_data_in_widget(table_cont)
        return has_data

    def _generate_absence_widgets(self, start_date, end_date, graph_cont, table_cont):
        """ Генерирует столбчатый график и таблицу сумм отсутствий. """
        log.debug(f"Генерация отсутствий: {start_date} - {end_date}")
        calculated_data = []
        has_data = False
        try:
            raw_data = self.absence_repo.get_raw_absence_data(
                str(start_date), str(end_date))  # Передаем строки
            if raw_data:
                calculated_data = self._calculate_total_absence_time(raw_data)
        except Exception as e:
            log.exception("Ошибка данных/расчета")
            self._show_error_in_widget(graph_cont)
            self._show_error_in_widget(table_cont)
            return False

        self.report_data_cache["absence_graph"] = calculated_data
        self.report_data_cache["absence_table"] = calculated_data
        for w in graph_cont.winfo_children():
            w.destroy()
            for w in table_cont.winfo_children():
                w.destroy()

        # График
        if calculated_data:
            try:
                MAX_BARS = 20
                plot_data = calculated_data[:MAX_BARS]
                labels = [f"{i[1]}\n({i[0]})" for i in plot_data]
                hours = [i[2] for i in plot_data]
                idx = list(range(len(plot_data)))
                fig = Figure(figsize=(7.5, 4.8), dpi=95)
                ax = fig.add_subplot(111)
                bars = ax.bar(idx, hours, color=SECONDARY_BG_COLOR, zorder=3)
                for bar in bars:
                    yval = bar.get_height()
                    if yval > 0.1:
                        ax.text(bar.get_x()+bar.get_width()/2., yval,
                                f'{yval:.1f}ч', va='bottom', ha='center', fontsize=7, zorder=4)
                ax.set_ylabel('Сумм. часы')
                ax.set_title(f'Отсутствия (Топ-{len(plot_data)})')
                ax.set_xticks(idx)
                ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=7)
                ax.yaxis.set_major_locator(mticker.MaxNLocator(min_n_ticks=3))
                ax.grid(True, axis='y', ls=':', alpha=0.6)
                ax.spines[['top', 'right']].set_visible(False)
                ax.set_ylim(bottom=0)
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=graph_cont)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                has_data = True
            except Exception as e:
                log.exception("Ошибка графика отс.")
                self._show_error_in_widget(graph_cont)
        else:
            self._show_no_data_in_widget(graph_cont)
        # Таблица
        if calculated_data:
            try:
                headers = ["Таб.№", "ФИО", "Сумм. часы"]
                tf = ctk.CTkFrame(table_cont, fg_color='transparent')
                tf.pack(ex=1, fill='both')
                s = Sheet(tf, data=calculated_data, headers=headers,
                          font=TABLE_FONT, header_font=TABLE_HEADER_FONT)
                s.enable_bindings("copy")
                s.pack(ex=1, fill='both')
                s.readonly(True)
                has_data = True  # Подтверждаем, если таблица есть
            except Exception as e:
                log.exception("Ошибка таблицы отс.")
                self._show_error_in_widget(table_cont)
        else:
            if not has_data:
                self._show_no_data_in_widget(table_cont)
        return has_data

    def export_report_data(self, report_prefix):
        """ Экспорт данных активной вкладки ('График' или 'Таблица') в CSV. """
        log.info(f"Запрос экспорта: {report_prefix}")
        # ... (Получение active_tab, data_key, data_to_export) ...
        results_tabview = getattr(self, f"{report_prefix}_results_tabview")
        active_tab = results_tabview.get()
        data_key = f"{report_prefix}_{'graph' if active_tab=='График' else 'table'}"
        data_to_export = self.report_data_cache.get(data_key)
        log.debug(f"Экспорт '{active_tab}' из '{data_key}'")
        if not data_to_export:
            messagebox.showwarning("Экспорт", f"Нет данных для экспорта.")
            return

        headers = []
        fname = f"{report_prefix}_{active_tab.lower()}_export"
        if report_prefix == "dismissal":
            g_type = getattr(self, "dismissal_grouping_selector").get()
            fname = f"dismissal_{g_type.replace(' ','_').lower()}"
            if active_tab == "Таблица":
                headers = ["ТН", "ФИО", "Должн",
                           "Отд", "Прием", "Увольн", "Прич"]
                fname += "_table"
            else:  # График
                if g_type == "По дням":
                    headers = ["Дата (ГГГГ-ММ-ДД)", "Кол-во"]
                elif g_type == "По годам":
                    headers = ["Год", "Кол-во"]
                else:
                    headers = ["Месяц (ГГГГ-ММ)", "Кол-во"]
                fname += "_graph"
        elif report_prefix == "absence":
            headers = ["Таб.№", "ФИО", "Суммарные часы отсутствия"]
            fname = "absence_summary"

        # Диалог сохранения и запись
        export_dir = "export_reports"
        os.makedirs(export_dir, exist_ok=True)
        initial_f = f"{fname}_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
        fpath = ctk.filedialog.asksaveasfilename(initialdir=export_dir, initialfile=initial_f,
                                                 title="Экспорт", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not fpath:
            log.info("Отмена экспорта.")
            return
        try:
            with codecs.open(fpath, "w", "utf-8-sig") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                    writer.writerows(data_to_export)
            log.info(f"Экспорт ОК: {fpath}")
            messagebox.showinfo("Успех", f"Сохранено:\n{fpath}")
        except Exception as e:
            log.exception(f"Ошибка экспорта: {fpath}")
            messagebox.showerror("Ошибка", f"{e}")

    def _show_no_data_in_widget(self, container):
        """ Показывает 'Нет данных'. """
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text="Нет данных\nдля выбранного периода",
                     font=DEFAULT_FONT, text_color="grey").place(relx=0.5, rely=0.5, anchor="center")

    def _show_error_in_widget(self, container, text="Ошибка\nпри формировании"):
        """ Показывает ошибку. """
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text=text, font=DEFAULT_FONT, text_color="red").place(
            relx=0.5, rely=0.5, anchor="center")

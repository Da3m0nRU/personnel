# gui/dashboard_frame.py
from tkinter import messagebox  # Добавим импорт messagebox
from db.employee_event_repository import EmployeeEventRepository
from db.employee_repository import EmployeeRepository
from config import *  # Импортируем наши константы
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import customtkinter as ctk
import tkinter as tk
import datetime
import logging
import matplotlib
# Устанавливаем бэкенд для Tkinter ПЕРЕД импортом pyplot
matplotlib.use("TkAgg")

# Импортируем нужные репозитории

log = logging.getLogger(__name__)


class DashboardFrame(ctk.CTkFrame):
    """
    Фрейм для отображения главной страницы (Дашборда)
    с ключевыми показателями и визуализациями.
    """

    def __init__(self, master, db):
        super().__init__(master, fg_color=MAIN_BG_COLOR)
        self.db = db
        # Инициализируем репозитории
        self.employee_repo = EmployeeRepository(self.db)
        self.event_repo = EmployeeEventRepository(self.db)

        # --- Настройка стиля matplotlib с увеличенными шрифтами ---
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except OSError:
            log.warning(
                "Стиль 'seaborn-v0_8-whitegrid' не найден, используется стиль по умолчанию.")
            plt.style.use('classic')

        # Увеличиваем глобальные размеры шрифтов matplotlib
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 11         # Базовый размер шрифта
        plt.rcParams['axes.titlesize'] = 14    # Размер заголовков осей/графика
        plt.rcParams['axes.labelsize'] = 12    # Размер подписей осей (X, Y)
        plt.rcParams['xtick.labelsize'] = 10   # Размер меток на оси X
        plt.rcParams['ytick.labelsize'] = 10   # Размер меток на оси Y
        plt.rcParams['legend.fontsize'] = 10   # Размер шрифта легенды
        # Размер основного заголовка фигуры (если используется)
        plt.rcParams['figure.titlesize'] = 16
        # -----------------------------------------------------------

        self.create_widgets()
        self.load_dashboard_data()  # Загружаем данные при инициализации

    def create_widgets(self):
        """Создает виджеты дашборда: KPI и контейнеры для графиков."""
        log.debug("Создание виджетов для DashboardFrame")

        # --- Заголовок ---
        title_label = ctk.CTkLabel(
            self, text="ГЛАВНАЯ", font=TITLE_BOLD_FONT,  # Используем шрифт из config
            text_color=LABEL_TEXT_COLOR, anchor="w"
        )
        title_label.grid(row=0, column=0, columnspan=2,
                         padx=20, pady=(20, 10), sticky="w")

        # --- Фрейм для KPI ---
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.grid(row=1, column=0, columnspan=2,
                       padx=20, pady=10, sticky="ew")
        kpi_frame.grid_columnconfigure(
            (0, 1, 2), weight=1)  # Растягиваем колонки KPI

        # KPI 1: Всего работающих
        self.total_employees_label = self._create_kpi_card(
            kpi_frame, 0, "Работающих сотрудников")
        # KPI 2: Принято за месяц
        self.hired_last_month_label = self._create_kpi_card(
            kpi_frame, 1, "Принято за 30 дней")
        # KPI 3: Уволено за месяц
        self.fired_last_month_label = self._create_kpi_card(
            kpi_frame, 2, "Уволено за 30 дней")

        # --- Контейнеры для графиков (2x2) ---
        chart_frame = ctk.CTkFrame(self, fg_color="transparent")
        chart_frame.grid(row=2, column=0, columnspan=2,
                         padx=15, pady=15, sticky="nsew")
        chart_frame.grid_rowconfigure((0, 1), weight=1)
        chart_frame.grid_columnconfigure((0, 1), weight=1)

        # Основная строка с графиками должна растягиваться
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)  # Колонки тоже

        # Контейнер для графика по отделам
        self.dept_chart_frame = ctk.CTkFrame(
            chart_frame, fg_color="white", corner_radius=10)
        self.dept_chart_frame.grid(
            row=0, column=0, padx=10, pady=10, sticky="nsew")
        # Контейнер для графика по должностям
        self.pos_chart_frame = ctk.CTkFrame(
            chart_frame, fg_color="white", corner_radius=10)
        self.pos_chart_frame.grid(
            row=0, column=1, padx=10, pady=10, sticky="nsew")
        # Контейнер для графика по возрасту
        self.age_chart_frame = ctk.CTkFrame(
            chart_frame, fg_color="white", corner_radius=10)
        self.age_chart_frame.grid(
            row=1, column=0, padx=10, pady=10, sticky="nsew")
        # Контейнер для графика по полу
        self.gender_chart_frame = ctk.CTkFrame(
            chart_frame, fg_color="white", corner_radius=10)
        self.gender_chart_frame.grid(
            row=1, column=1, padx=10, pady=10, sticky="nsew")

        log.debug("Виджеты DashboardFrame созданы")

    def _create_kpi_card(self, parent, col, title_text):
        """Вспомогательный метод для создания карточки KPI."""
        card_frame = ctk.CTkFrame(
            parent, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        card_frame.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
        card_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(card_frame, text=title_text, font=(
            "Arial", 16), text_color=LABEL_TEXT_COLOR)  # Шрифт подписи KPI увеличен
        title_label.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        value_label = ctk.CTkLabel(card_frame, text="...", font=(
            "Arial", 32, "bold"), text_color=ACCENT_COLOR)  # Шрифт значения KPI увеличен
        value_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        return value_label

    def load_dashboard_data(self):
        """Загружает все данные для дашборда и обновляет виджеты."""
        log.info("Загрузка данных для дашборда...")
        try:
            # --- Загрузка данных для KPI ---
            total_employees = self.employee_repo.get_active_employee_count()
            hired_count = self.event_repo.get_event_count_last_days(
                "Прием", 30)
            fired_count = self.event_repo.get_event_count_last_days(
                "Увольнение", 30)

            # --- Загрузка данных для Графиков ---
            dept_data = self.employee_repo.get_employees_count_by_department()
            pos_data = self.employee_repo.get_employees_count_by_position(
                limit=7)  # Топ 7 должностей
            birth_dates = self.employee_repo.get_active_employee_birth_dates()
            gender_data = self.employee_repo.get_gender_distribution()

            # --- Обновление KPI ---
            self.total_employees_label.configure(text=str(total_employees))
            self.hired_last_month_label.configure(text=str(hired_count))
            self.fired_last_month_label.configure(text=str(fired_count))

            # --- Создание/Обновление Графиков ---
            self._create_department_pie_chart(dept_data)
            self._create_position_bar_chart(pos_data)
            self._create_age_histogram(birth_dates)
            self._create_gender_pie_chart(gender_data)

            log.info("Данные для дашборда успешно загружены и отображены.")

        except Exception as e:
            log.exception("Ошибка при загрузке данных дашборда")
            messagebox.showerror(
                "Ошибка Дашборда", f"Не удалось загрузить данные для главной страницы:\n{e}")
            # Отображаем ошибки в KPI и графиках
            self.total_employees_label.configure(text="Ошибка")
            self.hired_last_month_label.configure(text="Ошибка")
            self.fired_last_month_label.configure(text="Ошибка")
            self._display_error_in_frame(self.dept_chart_frame)
            self._display_error_in_frame(self.pos_chart_frame)
            self._display_error_in_frame(self.age_chart_frame)
            self._display_error_in_frame(self.gender_chart_frame)

    def _clear_frame(self, frame):
        """Очищает фрейм от всех дочерних виджетов."""
        for widget in frame.winfo_children():
            widget.destroy()

    def _display_message_in_frame(self, frame, message, color="grey"):
        """Отображает сообщение внутри фрейма."""
        self._clear_frame(frame)
        # Увеличим шрифт для сообщений об ошибке/нет данных
        label = ctk.CTkLabel(frame, text=message, font=(
            "Arial", 16), text_color=color, wraplength=frame.winfo_width()-20)
        label.place(relx=0.5, rely=0.5, anchor="center")

    def _display_error_in_frame(self, frame):
        self._display_message_in_frame(frame, "Ошибка загрузки данных", "red")

    def _display_no_data_in_frame(self, frame):
        self._display_message_in_frame(frame, "Нет данных для отображения")

    # --- Методы для создания графиков (с увеличенными шрифтами) ---

    def _create_department_pie_chart(self, data):
        """Создает круговую диаграмму распределения по отделам."""
        self._clear_frame(self.dept_chart_frame)
        if not data:
            self._display_no_data_in_frame(self.dept_chart_frame)
            return

        labels = [item[0] for item in data]
        sizes = [item[1] for item in data]
        colors = plt.cm.get_cmap('tab20').colors[:len(labels)]

        try:
            # Немного увеличим размер и dpi
            fig = Figure(figsize=(4.5, 4), dpi=100)
            ax = fig.add_subplot(111)
            wedges, texts, autotexts = ax.pie(
                sizes, labels=None, autopct='%1.1f%%', startangle=90,
                colors=colors, pctdistance=0.85,
                wedgeprops=dict(width=0.4, edgecolor='w')
            )
            ax.axis('equal')
            ax.set_title("Распределение по отделам", pad=20,
                         fontsize=14)  # Увеличен шрифт заголовка

            # Увеличим шрифт легенды
            ax.legend(wedges, labels, title="Отделы", loc="center",
                      bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=10)

            # Увеличим шрифт процентов
            plt.setp(autotexts, size=9, weight="bold", color="white")

            fig.tight_layout(pad=2.0)  # Увеличим отступы

            canvas = FigureCanvasTkAgg(fig, master=self.dept_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except Exception as e:
            log.exception("Ошибка при создании графика по отделам")
            self._display_error_in_frame(self.dept_chart_frame)

    def _create_position_bar_chart(self, data):
        """Создает горизонтальную столбчатую диаграмму по должностям."""
        self._clear_frame(self.pos_chart_frame)
        if not data:
            self._display_no_data_in_frame(self.pos_chart_frame)
            return

        positions = [item[0] for item in data]
        counts = [item[1] for item in data]

        try:
            fig = Figure(figsize=(4.5, 4), dpi=100)
            ax = fig.add_subplot(111)

            y_pos = range(len(positions))
            bars = ax.barh(y_pos, counts, align='center',
                           color=SECONDARY_BG_COLOR, height=0.7)  # Чуть толще столбцы
            ax.set_yticks(y_pos)
            # Увеличен шрифт названий должностей
            ax.set_yticklabels(positions, fontsize=10)
            ax.invert_yaxis()
            # Увеличен шрифт оси X
            ax.set_xlabel('Количество сотрудников', fontsize=12)
            ax.set_title(f'Топ-{len(positions)} Должностей',
                         fontsize=14)  # Увеличен шрифт заголовка

            # Увеличим шрифт значений на столбцах
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.text(width + 0.15, bar.get_y() + bar.get_height()/2.,  # Чуть дальше от столбца
                            f'{int(width)}', va='center', ha='left', fontsize=9)

            ax.xaxis.set_major_locator(
                mticker.MaxNLocator(integer=True, nbins=5))
            ax.tick_params(axis='x', labelsize=10)  # Увеличим шрифт меток X
            ax.spines[['top', 'right']].set_visible(False)

            fig.tight_layout(pad=1.5)

            canvas = FigureCanvasTkAgg(fig, master=self.pos_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except Exception as e:
            log.exception("Ошибка при создании графика по должностям")
            self._display_error_in_frame(self.pos_chart_frame)

    def _create_age_histogram(self, birth_dates):
        """Создает гистограмму распределения по возрасту."""
        self._clear_frame(self.age_chart_frame)
        if not birth_dates:
            self._display_no_data_in_frame(self.age_chart_frame)
            return

        ages = []
        today = datetime.date.today()
        for date_str in birth_dates:
            try:
                birth_date = datetime.datetime.strptime(
                    date_str, "%Y-%m-%d").date()
                age = today.year - birth_date.year - \
                    ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age >= 18:
                    ages.append(age)
            except (ValueError, TypeError):
                log.warning(
                    f"Некорректная дата рождения '{date_str}' при расчете возраста.")
                continue

        if not ages:
            self._display_no_data_in_frame(self.age_chart_frame)
            return

        try:
            fig = Figure(figsize=(4.5, 4), dpi=100)
            ax = fig.add_subplot(111)

            max_age = max(ages) if ages else 70
            # Корзины по 7 лет для большего числа столбцов при необходимости
            bin_step = 7
            bins = list(range(18, max_age + bin_step + 1, bin_step))
            if bins[-1] <= max_age:
                bins.append(bins[-1]+bin_step)

            n, bins_ret, patches = ax.hist(
                ages, bins=bins, color=ACCENT_COLOR, edgecolor='white', rwidth=0.9)
            ax.set_xlabel('Возраст', fontsize=12)  # Увеличен шрифт
            ax.set_ylabel('Количество сотрудников',
                          fontsize=12)  # Увеличен шрифт
            ax.set_title('Возрастная структура', fontsize=14)  # Увеличен шрифт

            bin_centers = 0.5 * (bins_ret[1:] + bins_ret[:-1])
            ax.set_xticks(bin_centers)
            # Увеличим шрифт меток X
            ax.set_xticklabels(
                [f"{int(b - bin_step/2)}-{int(b + bin_step/2 -1)}" for b in bin_centers], rotation=45, ha='right', fontsize=9)

            ax.yaxis.set_major_locator(
                mticker.MaxNLocator(integer=True, nbins=5))
            ax.tick_params(axis='y', labelsize=10)  # Увеличим шрифт меток Y
            ax.spines[['top', 'right']].set_visible(False)

            # Увеличим шрифт значений над столбцами
            for count, patch in zip(n, patches):
                if count > 0:
                    height = patch.get_height()
                    ax.text(patch.get_x() + patch.get_width() / 2., height + 0.5,
                            f'{int(count)}', ha='center', va='bottom', fontsize=9)

            fig.tight_layout(pad=1.5)

            canvas = FigureCanvasTkAgg(fig, master=self.age_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except Exception as e:
            log.exception("Ошибка при создании гистограммы возраста")
            self._display_error_in_frame(self.age_chart_frame)

    def _create_gender_pie_chart(self, data):
        """Создает круговую диаграмму гендерного распределения."""
        self._clear_frame(self.gender_chart_frame)
        if not data:
            self._display_no_data_in_frame(self.gender_chart_frame)
            return

        labels = [item[0] for item in data]
        sizes = [item[1] for item in data]
        colors = ['#6495ED', '#FFB6C1']
        if len(labels) > len(colors):
            colors.extend(plt.cm.get_cmap(
                'Pastel1').colors[len(colors):len(labels)])

        try:
            fig = Figure(figsize=(4.5, 4), dpi=100)
            ax = fig.add_subplot(111)
            wedges, texts, autotexts = ax.pie(
                # Число и % в две строки
                sizes, labels=None, autopct=lambda p: '{:.0f}\n({:.1f}%)'.format(p * sum(sizes) / 100, p),
                startangle=90, colors=colors, pctdistance=0.7,
                wedgeprops=dict(edgecolor='w')
            )
            ax.axis('equal')
            ax.set_title("Гендерный состав", pad=20,
                         fontsize=14)  # Увеличен шрифт

            # Увеличим шрифт легенды
            ax.legend(wedges, labels, title="Пол", loc="center", bbox_to_anchor=(
                0.5, -0.15), ncol=len(labels), fontsize=10)

            # Увеличим шрифт текста на секторах
            plt.setp(autotexts, size=10, weight="bold", color="black")

            fig.tight_layout(pad=2.0)

            canvas = FigureCanvasTkAgg(fig, master=self.gender_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except Exception as e:
            log.exception("Ошибка при создании графика по полу")
            self._display_error_in_frame(self.gender_chart_frame)

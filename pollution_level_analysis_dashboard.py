import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import mysql.connector
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------------- DATABASE SETTINGS ----------------
# Change MYSQL_PASSWORD to your own MySQL password.
# Do not upload a file containing your real password to GitHub.

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "vedant123"
MYSQL_DATABASE = "pollution_analysis_db"


# ---------------- COLORS ----------------
NAVY = "#24476B"
BLUE = "#2878E8"
GREEN = "#2EAD59"
RED = "#F26470"
PURPLE = "#8257E5"
ORANGE = "#FF8A34"
BG = "#F3F7FC"
WHITE = "#FFFFFF"
TEXT = "#15365C"
BORDER = "#D7E4F5"


# Indian AQI category bands used for displaying the entered AQI value.
def get_aqi_category(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Satisfactory"
    elif aqi <= 200:
        return "Moderate"
    elif aqi <= 300:
        return "Poor"
    elif aqi <= 400:
        return "Very Poor"
    return "Severe"


def connect_database():
    """Create the database and pollution_readings table if they do not exist."""
    con = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cur = con.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`"
    )
    cur.close()
    con.close()

    con = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pollution_readings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reading_date DATE NOT NULL,
            city VARCHAR(60) NOT NULL,
            area VARCHAR(80),
            aqi INT NOT NULL,
            pm25 DECIMAL(10,2) DEFAULT 0,
            pm10 DECIMAL(10,2) DEFAULT 0,
            no2 DECIMAL(10,2) DEFAULT 0,
            so2 DECIMAL(10,2) DEFAULT 0,
            co DECIMAL(10,2) DEFAULT 0,
            o3 DECIMAL(10,2) DEFAULT 0,
            source VARCHAR(60) DEFAULT 'Manual Entry'
        )
    """)
    con.commit()
    cur.close()
    con.close()


def query_db(sql, values=None, fetch=False):
    con = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cur = con.cursor()
    try:
        cur.execute(sql, values or ())
        result = cur.fetchall() if fetch else None
        con.commit()
        return result
    finally:
        cur.close()
        con.close()


def number(value):
    return float(value or 0)


def money_or_value(value, suffix=""):
    return f"{value:,.2f}{suffix}"


# ---------------- MAIN DASHBOARD ----------------
class PollutionDashboard:

    def __init__(self, root):
        self.root = root
        self.root.title("Pollution Level Analysis Dashboard")
        self.root.configure(bg=BG)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry("1350x850")

        self.root.minsize(1050, 680)
        self.chart_canvases = []

        self.setup_style()
        self.build_header()
        self.build_main()
        self.refresh_data()

    # ---------------- STYLE ----------------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            font=("Segoe UI", 8),
            rowheight=23,
            background=WHITE,
            foreground=TEXT
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 8, "bold"),
            background="#E7F0FC",
            foreground=TEXT
        )
        style.configure("TCombobox", padding=3)

    # ---------------- HEADER ----------------
    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="◉  Pollution Level Analysis Dashboard",
            bg=NAVY,
            fg=WHITE,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w", padx=18, pady=(8, 0))

        tk.Label(
            header,
            text="Monitor  •  Compare  •  Understand Air Quality",
            bg=NAVY,
            fg="#D8E7FA",
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=22)

        self.date_label = tk.Label(
            header,
            text="DATE RANGE",
            bg=NAVY,
            fg=WHITE,
            font=("Segoe UI", 9),
            justify="right"
        )
        self.date_label.place(relx=0.98, rely=0.5, anchor="e")

    # ---------------- MAIN LAYOUT ----------------
    def build_main(self):
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=7, pady=7)

        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, minsize=205)
        self.body.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(
            self.body,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=8,
            pady=6
        )
        self.sidebar.grid(
            row=0, column=0, sticky="nsew", padx=(0, 5)
        )

        self.dashboard = tk.Frame(self.body, bg=BG)
        self.dashboard.grid(
            row=0, column=1, sticky="nsew", padx=(5, 0)
        )

        self.dashboard.grid_rowconfigure(0, weight=1)
        self.dashboard.grid_rowconfigure(1, weight=4)
        self.dashboard.grid_rowconfigure(2, weight=2)
        self.dashboard.grid_columnconfigure(0, weight=1)

        self.build_sidebar()
        self.build_dashboard()

    def button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=color,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
            pady=5
        )

    def entry(self, parent, label, default=""):
        tk.Label(
            parent,
            text=label,
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(3, 1))

        item = tk.Entry(
            parent,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1
        )
        item.pack(fill="x", ipady=2)

        if default:
            item.insert(0, default)
        return item

    # ---------------- SIDEBAR ----------------
    def build_sidebar(self):
        s = self.sidebar

        tk.Label(
            s, text="▦  FILTERS",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(s, text="Month", bg=WHITE, fg=TEXT).pack(anchor="w")
        self.month = tk.StringVar(value="All Months")
        self.month_box = ttk.Combobox(
            s, textvariable=self.month,
            values=["All Months"], state="readonly"
        )
        self.month_box.pack(fill="x", pady=(1, 4))
        self.month_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        tk.Label(s, text="City", bg=WHITE, fg=TEXT).pack(anchor="w")
        self.city = tk.StringVar(value="All")
        self.city_box = ttk.Combobox(
            s, textvariable=self.city,
            values=["All"], state="readonly"
        )
        self.city_box.pack(fill="x", pady=(1, 4))
        self.city_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        tk.Label(s, text="AQI Category", bg=WHITE, fg=TEXT).pack(anchor="w")
        self.category = tk.StringVar(value="All")
        self.category_box = ttk.Combobox(
            s, textvariable=self.category,
            values=["All"], state="readonly"
        )
        self.category_box.pack(fill="x", pady=(1, 4))
        self.category_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        self.button(
            s, "↻ Reset Filters", NAVY, self.reset_filters
        ).pack(fill="x", pady=3)

        ttk.Separator(s).pack(fill="x", pady=5)

        tk.Label(
            s, text="MANAGE READINGS",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=3)

        self.button(
            s, "+ Add Reading", GREEN, self.add_reading
        ).pack(fill="x", pady=2)
        self.button(
            s, "Update Selected", BLUE, self.update_reading
        ).pack(fill="x", pady=2)
        self.button(
            s, "Delete Selected", RED, self.delete_reading
        ).pack(fill="x", pady=2)
        self.button(
            s, "Refresh Data", PURPLE, self.refresh_data
        ).pack(fill="x", pady=2)

        ttk.Separator(s).pack(fill="x", pady=5)

        tk.Label(
            s, text="ADD / EDIT READING",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=2)

        self.date_entry = self.entry(
            s, "Date (YYYY-MM-DD)",
            datetime.today().strftime("%Y-%m-%d")
        )
        self.city_entry = self.entry(s, "City")
        self.area_entry = self.entry(s, "Area / Location")
        self.aqi_entry = self.entry(s, "AQI (0 - 500)")
        self.pm25_entry = self.entry(s, "PM2.5 (µg/m³)", "0")
        self.pm10_entry = self.entry(s, "PM10 (µg/m³)", "0")
        self.no2_entry = self.entry(s, "NO2 (µg/m³)", "0")
        self.so2_entry = self.entry(s, "SO2 (µg/m³)", "0")
        self.co_entry = self.entry(s, "CO (mg/m³)", "0")
        self.o3_entry = self.entry(s, "O3 (µg/m³)", "0")

        tk.Label(
            s, text="Data Source",
            bg=WHITE, fg=TEXT
        ).pack(anchor="w", pady=(3, 1))
        self.source_entry = tk.StringVar(value="Manual Entry")
        ttk.Combobox(
            s,
            textvariable=self.source_entry,
            values=["Manual Entry", "CPCB", "Open Data", "Other"],
            state="readonly"
        ).pack(fill="x")

        self.button(
            s, "Clear Form", "#6B7F95", self.clear_form
        ).pack(fill="x", pady=4)

    # ---------------- DASHBOARD CONTENT ----------------
    def build_dashboard(self):
        d = self.dashboard

        self.kpi_frame = tk.Frame(d, bg=BG)
        self.kpi_frame.grid(row=0, column=0, sticky="nsew")
        for i in range(4):
            self.kpi_frame.grid_columnconfigure(
                i, weight=1, uniform="cards"
            )

        self.kpis = []
        cards = [
            ("AVERAGE AQI", BLUE),
            ("HIGHEST AQI", RED),
            ("TOTAL READINGS", GREEN),
            ("MOST POLLUTED CITY", PURPLE)
        ]

        for i, (title, color) in enumerate(cards):
            card = tk.Frame(
                self.kpi_frame,
                bg=WHITE,
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=7, pady=5
            )
            card.grid(
                row=0, column=i,
                sticky="nsew", padx=3, pady=2
            )

            tk.Label(
                card, text=title,
                bg=WHITE, fg=TEXT,
                font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")

            value = tk.Label(
                card, text="—",
                bg=WHITE, fg=color,
                font=("Segoe UI", 12, "bold")
            )
            value.pack(anchor="w", pady=2)

            sub = tk.Label(
                card, text="",
                bg=WHITE, fg="#67809E",
                font=("Segoe UI", 7)
            )
            sub.pack(anchor="w")
            self.kpis.append((value, sub))

        # Four charts arranged in two columns.
        self.chart_area = tk.Frame(d, bg=BG)
        self.chart_area.grid(
            row=1, column=0, sticky="nsew", pady=3
        )
        self.chart_area.grid_rowconfigure(0, weight=1)
        self.chart_area.grid_rowconfigure(1, weight=1)
        self.chart_area.grid_columnconfigure(0, weight=1)
        self.chart_area.grid_columnconfigure(1, weight=1)

        titles = [
            "AQI Category Distribution",
            "Daily AQI Trend",
            "Average Pollutant Levels",
            "City-wise Average AQI"
        ]
        self.chart_frames = []

        for i, title in enumerate(titles):
            frame = tk.Frame(
                self.chart_area,
                bg=WHITE,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            frame.grid(
                row=i // 2, column=i % 2,
                sticky="nsew", padx=3, pady=3
            )
            tk.Label(
                frame, text=title,
                bg=WHITE, fg=TEXT,
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w", padx=7, pady=(4, 0))
            self.chart_frames.append(frame)

        bottom = tk.Frame(d, bg=BG)
        bottom.grid(row=2, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=7)
        bottom.grid_columnconfigure(1, weight=3)
        bottom.grid_rowconfigure(0, weight=1)

        table_frame = self.panel(bottom, "Recent Pollution Readings")
        table_frame.grid(
            row=0, column=0, sticky="nsew", padx=3, pady=2
        )

        holder = tk.Frame(table_frame, bg=WHITE)
        holder.pack(fill="both", expand=True, padx=3, pady=2)

        columns = (
            "id", "date", "city", "area", "aqi", "category"
        )
        self.tree = ttk.Treeview(
            holder, columns=columns,
            show="headings", height=4
        )

        headings = [
            ("id", "#", 35),
            ("date", "Date", 85),
            ("city", "City", 85),
            ("area", "Area", 100),
            ("aqi", "AQI", 55),
            ("category", "Category", 90)
        ]
        for key, label, width in headings:
            self.tree.heading(key, text=label)
            self.tree.column(
                key, width=width, minwidth=30,
                anchor="center", stretch=True
            )

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.load_selected)

        insight_frame = self.panel(bottom, "Air Quality Insights")
        insight_frame.grid(
            row=0, column=1, sticky="nsew", padx=3, pady=2
        )
        self.insights = tk.Label(
            insight_frame,
            text="Add readings to view insights.",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9),
            justify="left",
            anchor="nw",
            wraplength=230
        )
        self.insights.pack(
            fill="both", expand=True, padx=7, pady=7
        )

    def panel(self, parent, title):
        frame = tk.Frame(
            parent, bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        tk.Label(
            frame, text=title,
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=6, pady=3)
        return frame

    # ---------------- FORM FUNCTIONS ----------------
    def clear_form(self):
        for item in (
            self.date_entry, self.city_entry, self.area_entry,
            self.aqi_entry, self.pm25_entry, self.pm10_entry,
            self.no2_entry, self.so2_entry, self.co_entry,
            self.o3_entry
        ):
            item.delete(0, tk.END)

        self.date_entry.insert(
            0, datetime.today().strftime("%Y-%m-%d")
        )
        for item in (
            self.pm25_entry, self.pm10_entry, self.no2_entry,
            self.so2_entry, self.co_entry, self.o3_entry
        ):
            item.insert(0, "0")
        self.source_entry.set("Manual Entry")

    def get_form(self):
        date_text = self.date_entry.get().strip()
        city = self.city_entry.get().strip()
        area = self.area_entry.get().strip()
        aqi_text = self.aqi_entry.get().strip()
        pollutant_entries = (
            self.pm25_entry, self.pm10_entry, self.no2_entry,
            self.so2_entry, self.co_entry, self.o3_entry
        )
        pollutant_texts = [item.get().strip() or "0"
                           for item in pollutant_entries]

        if not date_text or not city or not aqi_text:
            messagebox.showwarning(
                "Missing Information",
                "Enter date, city and AQI."
            )
            return None

        try:
            reading_date = datetime.strptime(
                date_text, "%Y-%m-%d"
            ).date()
            aqi = int(aqi_text)
            pollutants = [float(value) for value in pollutant_texts]

            if not 0 <= aqi <= 500:
                raise ValueError
            if any(value < 0 for value in pollutants):
                raise ValueError

        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Enter a valid date, AQI from 0 to 500, and non-negative pollutant values."
            )
            return None

        return (
            reading_date, city, area, aqi,
            *pollutants, self.source_entry.get()
        )

    # ---------------- ADD / UPDATE / DELETE ----------------
    def add_reading(self):
        data = self.get_form()
        if not data:
            return
        try:
            query_db("""
                INSERT INTO pollution_readings
                (reading_date, city, area, aqi, pm25, pm10,
                 no2, so2, co, o3, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, data)
            self.clear_form()
            self.refresh_data()
            messagebox.showinfo(
                "Success", "Pollution reading added successfully."
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def update_reading(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select Reading", "Select a reading from the table."
            )
            return

        data = self.get_form()
        if not data:
            return

        reading_id = self.tree.item(
            selected[0], "values"
        )[0]
        try:
            query_db("""
                UPDATE pollution_readings
                SET reading_date=%s, city=%s, area=%s, aqi=%s,
                    pm25=%s, pm10=%s, no2=%s, so2=%s, co=%s,
                    o3=%s, source=%s
                WHERE id=%s
            """, data + (reading_id,))
            self.clear_form()
            self.refresh_data()
            messagebox.showinfo(
                "Success", "Pollution reading updated successfully."
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_reading(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select Reading", "Select a reading from the table."
            )
            return

        reading_id = self.tree.item(
            selected[0], "values"
        )[0]

        if messagebox.askyesno(
            "Confirm Delete", f"Delete reading #{reading_id}?"
        ):
            try:
                query_db(
                    "DELETE FROM pollution_readings WHERE id=%s",
                    (reading_id,)
                )
                self.clear_form()
                self.refresh_data()
            except mysql.connector.Error as error:
                messagebox.showerror("Database Error", str(error))

    def load_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        reading_id = self.tree.item(
            selected[0], "values"
        )[0]
        try:
            rows = query_db("""
                SELECT reading_date, city, area, aqi, pm25, pm10,
                       no2, so2, co, o3, source
                FROM pollution_readings
                WHERE id=%s
            """, (reading_id,), fetch=True)
            if not rows:
                return

            row = rows[0]
            self.clear_form()
            entries = [
                (self.date_entry, str(row[0])),
                (self.city_entry, row[1]),
                (self.area_entry, row[2] or ""),
                (self.aqi_entry, str(row[3])),
                (self.pm25_entry, str(row[4])),
                (self.pm10_entry, str(row[5])),
                (self.no2_entry, str(row[6])),
                (self.so2_entry, str(row[7])),
                (self.co_entry, str(row[8])),
                (self.o3_entry, str(row[9]))
            ]
            for entry, value in entries:
                entry.delete(0, tk.END)
                entry.insert(0, value)
            self.source_entry.set(row[10] or "Manual Entry")
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    # ---------------- FILTERS ----------------
    def reset_filters(self):
        self.month.set("All Months")
        self.city.set("All")
        self.category.set("All")
        self.refresh_data()

    # ---------------- REFRESH DATA ----------------
    def refresh_data(self):
        try:
            rows = query_db("""
                SELECT id, reading_date, city, area, aqi, pm25,
                       pm10, no2, so2, co, o3, source
                FROM pollution_readings
                ORDER BY reading_date DESC, id DESC
            """, fetch=True)
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Database Error",
                "Check MySQL and your database settings.\n\n" + str(error)
            )
            return

        months = sorted(
            {str(row[1])[:7] for row in rows},
            reverse=True
        )
        cities = sorted({row[2] for row in rows})
        categories = sorted(
            {get_aqi_category(row[4]) for row in rows}
        )

        self.month_box["values"] = ["All Months"] + months
        self.city_box["values"] = ["All"] + cities
        self.category_box["values"] = ["All"] + categories

        if self.month.get() not in self.month_box["values"]:
            self.month.set("All Months")
        if self.city.get() not in self.city_box["values"]:
            self.city.set("All")
        if self.category.get() not in self.category_box["values"]:
            self.category.set("All")

        filtered = []
        for row in rows:
            if (
                self.month.get() != "All Months"
                and str(row[1])[:7] != self.month.get()
            ):
                continue
            if self.city.get() != "All" and row[2] != self.city.get():
                continue
            if (
                self.category.get() != "All"
                and get_aqi_category(row[4]) != self.category.get()
            ):
                continue
            filtered.append(row)

        self.update_table(filtered)
        self.update_kpis(filtered)
        self.update_charts(filtered)
        self.update_insights(filtered)

        if filtered:
            dates = [str(row[1]) for row in filtered]
            self.date_label.config(
                text=f"DATE RANGE\n{min(dates)}  →  {max(dates)}"
            )
        else:
            self.date_label.config(text="DATE RANGE\nNo readings")

    # ---------------- TABLE ----------------
    def update_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows[:10]:
            self.tree.insert(
                "", "end",
                values=(
                    row[0], row[1], row[2], row[3] or "",
                    row[4], get_aqi_category(row[4])
                )
            )

    # ---------------- KPI CARDS ----------------
    def update_kpis(self, rows):
        count = len(rows)
        average = (
            sum(row[4] for row in rows) / count if count else 0
        )
        highest = max(rows, key=lambda row: row[4], default=None)

        city_totals = {}
        for row in rows:
            city_totals.setdefault(row[2], []).append(row[4])

        city_averages = {
            city: sum(values) / len(values)
            for city, values in city_totals.items()
        }
        most_polluted = (
            max(city_averages, key=city_averages.get)
            if city_averages else "—"
        )

        self.kpis[0][0].config(text=f"{average:.1f}")
        self.kpis[0][1].config(
            text=get_aqi_category(round(average)) if count else "No data"
        )
        self.kpis[1][0].config(
            text=str(highest[4]) if highest else "—"
        )
        self.kpis[1][1].config(
            text=get_aqi_category(highest[4]) if highest else "No data"
        )
        self.kpis[2][0].config(text=str(count))
        self.kpis[2][1].config(text="Available readings")
        self.kpis[3][0].config(text=most_polluted)
        self.kpis[3][1].config(
            text=f"Average AQI: {city_averages[most_polluted]:.1f}"
            if most_polluted != "—" else "No data"
        )

    # ---------------- CHART HELPERS ----------------
    def clear_charts(self):
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()
        self.chart_canvases = []

    def draw_chart(self, parent, fig):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=3, pady=2
        )
        self.chart_canvases.append(canvas)

    def make_figure(self):
        return Figure(
            figsize=(5.2, 2.2),
            dpi=90,
            facecolor=WHITE
        )

    # ---------------- CHARTS ----------------
    def update_charts(self, rows):
        self.clear_charts()

        # 1. AQI category distribution
        category_counts = {}
        for row in rows:
            category = get_aqi_category(row[4])
            category_counts[category] = category_counts.get(category, 0) + 1

        fig = self.make_figure()
        ax = fig.add_subplot(111)
        if category_counts:
            labels = list(category_counts.keys())
            values = list(category_counts.values())
            ax.pie(
                values, labels=labels, autopct="%1.0f%%",
                startangle=90, textprops={"fontsize": 8},
                wedgeprops={"edgecolor": WHITE, "linewidth": 1.5}
            )
        else:
            ax.text(0.5, 0.5, "No reading data",
                    ha="center", va="center")
        ax.set_aspect("equal")
        fig.tight_layout()
        self.draw_chart(self.chart_frames[0], fig)

        # 2. Daily average AQI trend
        daily_values = {}
        for row in rows:
            date = str(row[1])
            daily_values.setdefault(date, []).append(row[4])

        fig = self.make_figure()
        ax = fig.add_subplot(111)
        if daily_values:
            days = sorted(daily_values)
            averages = [
                sum(daily_values[day]) / len(daily_values[day])
                for day in days
            ]
            ax.plot(
                days, averages, marker="o",
                markersize=4, linewidth=2, color=BLUE
            )
            ax.set_ylabel("Average AQI", fontsize=8)
            ax.tick_params(axis="both", labelsize=7)
            ax.tick_params(axis="x", labelrotation=15)
            ax.grid(axis="y", alpha=0.25)
        else:
            ax.text(0.5, 0.5, "No reading data",
                    ha="center", va="center")
        fig.tight_layout()
        self.draw_chart(self.chart_frames[1], fig)

        # 3. Average pollutant concentration
        pollutant_columns = [
            ("PM2.5", 5), ("PM10", 6), ("NO2", 7),
            ("SO2", 8), ("CO", 9), ("O3", 10)
        ]
        pollutant_averages = []
        pollutant_names = []
        if rows:
            for name, index in pollutant_columns:
                pollutant_names.append(name)
                pollutant_averages.append(
                    sum(number(row[index]) for row in rows) / len(rows)
                )

        fig = self.make_figure()
        ax = fig.add_subplot(111)
        if pollutant_averages:
            ax.bar(
                pollutant_names, pollutant_averages,
                color=[BLUE, ORANGE, GREEN, PURPLE, RED, "#28A7A1"],
                width=0.65
            )
            ax.set_ylabel("Average concentration", fontsize=8)
            ax.tick_params(axis="both", labelsize=8)
            ax.grid(axis="y", alpha=0.25)
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, "No reading data",
                    ha="center", va="center")
        fig.tight_layout()
        self.draw_chart(self.chart_frames[2], fig)

        # 4. City-wise average AQI
        city_values = {}
        for row in rows:
            city_values.setdefault(row[2], []).append(row[4])

        city_names = list(city_values.keys())
        city_averages = [
            sum(values) / len(values) for values in city_values.values()
        ]

        fig = self.make_figure()
        ax = fig.add_subplot(111)
        if city_names:
            ax.bar(
                city_names, city_averages,
                color=PURPLE, width=0.65
            )
            ax.set_ylabel("Average AQI", fontsize=8)
            ax.tick_params(axis="both", labelsize=8)
            ax.tick_params(axis="x", labelrotation=15)
            ax.grid(axis="y", alpha=0.25)
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, "No reading data",
                    ha="center", va="center")
        fig.tight_layout()
        self.draw_chart(self.chart_frames[3], fig)

    # ---------------- INSIGHTS ----------------
    def update_insights(self, rows):
        if not rows:
            self.insights.config(
                text="No readings available.\n\nAdd pollution readings to view the analysis."
            )
            return

        average = sum(row[4] for row in rows) / len(rows)
        highest = max(rows, key=lambda row: row[4])
        category_counts = {}
        for row in rows:
            category = get_aqi_category(row[4])
            category_counts[category] = category_counts.get(category, 0) + 1

        common_category = max(
            category_counts, key=category_counts.get
        )

        self.insights.config(
            text=(
                f"Average AQI\n{average:.1f} "
                f"({get_aqi_category(round(average))})\n\n"
                f"Highest Reading\n{highest[4]} AQI - {highest[2]}\n\n"
                f"Most Common Category\n{common_category}\n\n"
                f"Total Readings\n{len(rows)}\n\n"
                "Note: Results depend on the readings entered."
            )
        )


# ---------------- START APPLICATION ----------------
if __name__ == "__main__":
    try:
        if MYSQL_PASSWORD == "YOUR_MYSQL_PASSWORD":
            raise ValueError(
                "Set MYSQL_PASSWORD in the code before starting the application."
            )
        connect_database()
    except (mysql.connector.Error, ValueError) as error:
        temp = tk.Tk()
        temp.withdraw()
        messagebox.showerror(
            "Setup Error",
            "Check MySQL settings and make sure MySQL Server is running.\n\n"
            + str(error),
            parent=temp
        )
        temp.destroy()
        raise SystemExit

    root = tk.Tk()
    app = PollutionDashboard(root)
    root.mainloop()

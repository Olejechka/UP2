import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLineEdit, QTableWidget, QTableWidgetItem, QSpinBox,
                             QComboBox, QMessageBox,
                             QTimeEdit, QWidget)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta
import json
from pathlib import Path

# Словарь для перевода дней недели на русский
days_translation = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Билетная касса театра")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Данные
        self.halls = []
        self.shows = {}
        self.sessions = load_sessions_from_file()

        self.main_screen()
        self.current_week_tab = None
        self.next_week_tab = None

    def main_screen(self):
        self.clear_window()

        layout = QVBoxLayout()

        sessions_button = QPushButton("Перейти к сеансам")
        sessions_button.setFont(QFont("Arial", 14))
        sessions_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 10px;")
        sessions_button.clicked.connect(self.open_view_schedule_screen)
        layout.addWidget(sessions_button, alignment=Qt.AlignCenter)

        edit_button = QPushButton("Редактировать")
        edit_button.setFont(QFont("Arial", 14))
        edit_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 10px;")
        edit_button.clicked.connect(self.open_edit_screen)
        layout.addWidget(edit_button, alignment=Qt.AlignCenter)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_view_schedule_screen(self):
        self.clear_window()

        layout = QVBoxLayout()
        label = QLabel("Экран сеансов: Выберите неделю")
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #333;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        back_button = QPushButton("Назад")
        back_button.setFont(QFont("Arial", 12))
        back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
        back_button.clicked.connect(self.main_screen)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        self.current_week_tab = ViewScheduleTab(self, "На тек. неделю", is_next_week=False)
        self.next_week_tab = ViewScheduleTab(self, "На след. неделю", is_next_week=True)

        tabs = QTabWidget()
        tabs.addTab(self.current_week_tab, "На тек. неделю")
        tabs.addTab(self.next_week_tab, "На след. неделю")
        tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #ccc; } QTabBar::tab { background: #0078d7; color: white; padding: 8px; border-radius: 5px; } QTabBar::tab:selected { background: #005bb5; }")
        layout.addWidget(tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_edit_screen(self):
        self.clear_window()

        layout = QVBoxLayout()
        label = QLabel("Экран запросов")
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #333;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        back_button = QPushButton("Назад")
        back_button.setFont(QFont("Arial", 12))
        back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
        back_button.clicked.connect(self.main_screen)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #ccc; } QTabBar::tab { background: #0078d7; color: white; padding: 8px; border-radius: 5px; } QTabBar::tab:selected { background: #005bb5; }")

        halls_tab = HallsTab(self)
        tabs.addTab(halls_tab, "Залы")

        shows_tab = ShowsTab(self)
        tabs.addTab(shows_tab, "Спектакли")

        current_week_tab = ScheduleTab(self, "На тек. неделю", is_next_week=False)
        tabs.addTab(current_week_tab, "На тек. неделю")

        next_week_tab = ScheduleTab(self, "На след. неделю", is_next_week=True)
        tabs.addTab(next_week_tab, "На след. неделю")

        layout.addWidget(tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_edit_screen(self):
        self.clear_window()

        layout = QVBoxLayout()
        label = QLabel("Экран запросов")
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #333;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        back_button = QPushButton("Назад")
        back_button.setFont(QFont("Arial", 12))
        back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
        back_button.clicked.connect(self.main_screen)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #ccc; } QTabBar::tab { background: #0078d7; color: white; padding: 8px; border-radius: 5px; } QTabBar::tab:selected { background: #005bb5; }")

        halls_tab = HallsTab(self)
        tabs.addTab(halls_tab, "Залы")

        shows_tab = ShowsTab(self)
        tabs.addTab(shows_tab, "Спектакли")

        current_week_tab = ScheduleTab(self, "На тек. неделю", is_next_week=False)
        tabs.addTab(current_week_tab, "На тек. неделю")

        next_week_tab = ScheduleTab(self, "На след. неделю", is_next_week=True)
        tabs.addTab(next_week_tab, "На след. неделю")

        layout.addWidget(tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def clear_window(self):
        for widget in self.findChildren(QWidget):
            widget.deleteLater()

class HallsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()

        add_hall_button = QPushButton("+")
        add_hall_button.setFont(QFont("Arial", 14))
        add_hall_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 10px;")
        add_hall_button.clicked.connect(lambda: EditHallScreen(self.main_window))
        layout.addWidget(add_hall_button, alignment=Qt.AlignCenter)

        self.halls_list = QVBoxLayout()
        layout.addLayout(self.halls_list)

        self.update_halls_list()

        container = QWidget()
        container.setLayout(layout)
        self.setLayout(layout)

    def update_halls_list(self):
        for i in reversed(range(self.halls_list.count())):
            self.halls_list.itemAt(i).widget().setParent(None)
        for hall in self.main_window.halls:
            hall_button = QPushButton(hall['name'])
            hall_button.setFont(QFont("Arial", 12))
            hall_button.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; padding: 8px;")
            hall_button.clicked.connect(lambda checked, h=hall: EditHallScreen(self.main_window, h))
            self.halls_list.addWidget(hall_button)

class ShowsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()

        add_show_button = QPushButton("+")
        add_show_button.setFont(QFont("Arial", 14))
        add_show_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 10px;")
        add_show_button.clicked.connect(lambda: EditShowScreen(self.main_window))
        layout.addWidget(add_show_button, alignment=Qt.AlignCenter)

        self.shows_list = QVBoxLayout()
        layout.addLayout(self.shows_list)

        self.update_shows_list()

        container = QWidget()
        container.setLayout(layout)
        self.setLayout(layout)

    def update_shows_list(self):
        for i in reversed(range(self.shows_list.count())):
            self.shows_list.itemAt(i).widget().setParent(None)
        for show in self.main_window.shows.values():
            show_button = QPushButton(show['name'])
            show_button.setFont(QFont("Arial", 12))
            show_button.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; padding: 8px;")
            show_button.clicked.connect(lambda checked, s=show: EditShowScreen(self.main_window, s))
            self.shows_list.addWidget(show_button)

class ScheduleTab(QWidget):
    def __init__(self, main_window, title, is_next_week):
        super().__init__()
        self.main_window = main_window
        self.is_next_week = is_next_week

        layout = QVBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #333;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        self.schedule_list = QVBoxLayout()

        start_date = datetime.now()
        if is_next_week:
            start_date += timedelta(weeks=1)
        start_of_week = start_date - timedelta(days=start_date.weekday())

        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            day_button = QPushButton(f"{days_translation[current_date.strftime('%A')]} {current_date.strftime('%d.%m.%Y')}")
            day_button.setFont(QFont("Arial", 12))
            day_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
            day_button.clicked.connect(lambda checked, d=current_date: AddSessionScreen(main_window, d))
            self.schedule_list.addWidget(day_button, alignment=Qt.AlignCenter)

            if current_date in self.main_window.sessions:
                for session in self.main_window.sessions[current_date]:
                    session_layout = QHBoxLayout()
                    session_button = QPushButton(f"{session['time']} - {session['show']} - {session['hall']}")
                    session_button.setFont(QFont("Arial", 12))
                    session_button.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; padding: 8px;")
                    session_button.clicked.connect(lambda checked, s=session, d=current_date: EditSessionScreen(main_window, d, s))
                    session_layout.addWidget(session_button)

                    edit_button = QPushButton("Редактировать")
                    edit_button.setFont(QFont("Arial", 12))
                    edit_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
                    edit_button.clicked.connect(lambda checked, s=session, d=current_date: EditSessionScreen(main_window, d, s))
                    session_layout.addWidget(edit_button)

                    self.schedule_list.addLayout(session_layout)

        layout.addLayout(self.schedule_list)

        self.setLayout(layout)

    def update_sessions_list(self):
        for i in reversed(range(self.schedule_list.count())):
            self.schedule_list.itemAt(i).widget().setParent(None)

        start_date = datetime.now()
        if self.is_next_week:
            start_date += timedelta(weeks=1)
        start_of_week = start_date - timedelta(days=start_date.weekday())

        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            day_button = QPushButton(f"{days_translation[current_date.strftime('%A')]} {current_date.strftime('%d.%m.%Y')}")
            day_button.setFont(QFont("Arial", 12))
            day_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
            day_button.clicked.connect(lambda checked, d=current_date: AddSessionScreen(self.main_window, d))
            self.schedule_list.addWidget(day_button, alignment=Qt.AlignCenter)

            if current_date in self.main_window.sessions:
                for session in self.main_window.sessions[current_date]:
                    session_layout = QHBoxLayout()
                    session_button = QPushButton(f"{session['time']} - {session['show']} - {session['hall']}")
                    session_button.setFont(QFont("Arial", 12))
                    session_button.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; padding: 8px;")
                    session_button.clicked.connect(lambda checked, s=session, d=current_date: EditSessionScreen(self.main_window, d, s))
                    session_layout.addWidget(session_button)

                    edit_button = QPushButton("Редактировать")
                    edit_button.setFont(QFont("Arial", 12))
                    edit_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
                    edit_button.clicked.connect(lambda checked, s=session, d=current_date: EditSessionScreen(self.main_window, d, s))
                    session_layout.addWidget(edit_button)

                    self.schedule_list.addLayout(session_layout)

class ViewScheduleTab(QWidget):
    def __init__(self, main_window, title, is_next_week):
        super().__init__()
        self.main_window = main_window
        self.is_next_week = is_next_week

        layout = QVBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #333;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        self.schedule_list = QVBoxLayout()

        start_date = datetime.now()
        if is_next_week:
            start_date += timedelta(weeks=1)
        start_of_week = start_date - timedelta(days=start_date.weekday())

        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            day_label = QLabel(f"{days_translation[current_date.strftime('%A')]} {current_date.strftime('%d.%m.%Y')}")
            day_label.setFont(QFont("Arial", 14))
            day_label.setStyleSheet("color: #0078d7;")
            self.schedule_list.addWidget(day_label, alignment=Qt.AlignCenter)

            if current_date in self.main_window.sessions:
                for session in self.main_window.sessions[current_date]:
                    session_label = QLabel(f"{session['time']} - {session['show']} - {session['hall']}")
                    session_label.setFont(QFont("Arial", 12))
                    session_label.setStyleSheet("color: #333;")
                    self.schedule_list.addWidget(session_label, alignment=Qt.AlignCenter)

        layout.addLayout(self.schedule_list)

        self.setLayout(layout)

def EditHallScreen(main_window, hall=None):
    main_window.clear_window()

    layout = QVBoxLayout()

    hall_name_layout = QHBoxLayout()
    hall_name_label = QLabel("Название зала:")
    hall_name_label.setFont(QFont("Arial", 12))
    hall_name_label.setStyleSheet("color: #333;")
    hall_name_input = QLineEdit()
    if hall:
        hall_name_input.setText(hall['name'])
    hall_name_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    hall_name_layout.addWidget(hall_name_label)
    hall_name_layout.addWidget(hall_name_input)
    layout.addLayout(hall_name_layout)

    rows_table = QTableWidget()
    rows_table.setColumnCount(2)
    rows_table.setHorizontalHeaderLabels(["Ряд", "Количество мест"])
    rows_table.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
    if hall:
        rows_table.setRowCount(len(hall['rows']))
        for row_idx, row in enumerate(hall['rows']):
            rows_table.setItem(row_idx, 0, QTableWidgetItem(str(row['row_number'])))
            rows_table.setItem(row_idx, 1, QTableWidgetItem(str(row['seats'])))
    layout.addWidget(rows_table)

    add_row_layout = QHBoxLayout()
    row_number_input = QSpinBox()
    row_number_input.setMinimum(1)
    row_number_input.setMaximum(100)
    row_number_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    seats_input = QSpinBox()
    seats_input.setMinimum(1)
    seats_input.setMaximum(500)
    seats_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    add_row_button = QPushButton("Добавить ряд")
    add_row_button.setFont(QFont("Arial", 12))
    add_row_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 8px;")
    add_row_button.clicked.connect(lambda: add_row(rows_table, row_number_input, seats_input))
    add_row_layout.addWidget(QLabel("Ряд:").setStyleSheet("color: #333;"))
    add_row_layout.addWidget(row_number_input)
    add_row_layout.addWidget(QLabel("Мест:").setStyleSheet("color: #333;"))
    add_row_layout.addWidget(seats_input)
    add_row_layout.addWidget(add_row_button)
    layout.addLayout(add_row_layout)

    save_button = QPushButton("Сохранить")
    save_button.setFont(QFont("Arial", 12))
    save_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 8px;")
    save_button.clicked.connect(lambda: save_hall(main_window, hall, hall_name_input, rows_table))
    layout.addWidget(save_button, alignment=Qt.AlignCenter)

    back_button = QPushButton("Назад")
    back_button.setFont(QFont("Arial", 12))
    back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
    back_button.clicked.connect(main_window.open_edit_screen)
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    container = QWidget()
    container.setLayout(layout)
    main_window.setCentralWidget(container)

def add_row(rows_table, row_number_input, seats_input):
    row_position = rows_table.rowCount()
    rows_table.insertRow(row_position)
    rows_table.setItem(row_position, 0, QTableWidgetItem(str(row_number_input.value())))
    rows_table.setItem(row_position, 1, QTableWidgetItem(str(seats_input.value())))

def save_hall(main_window, hall, hall_name_input, rows_table):
    hall_name = hall_name_input.text()
    rows = []
    for row in range(rows_table.rowCount()):
        row_number = int(rows_table.item(row, 0).text())
        seats = int(rows_table.item(row, 1).text())
        rows.append({'row_number': row_number, 'seats': seats})

    if hall:
        hall['name'] = hall_name
        hall['rows'] = rows
    else:
        main_window.halls.append({'name': hall_name, 'rows': rows})

    QMessageBox.information(main_window, "Сохранение", f"Зал {hall_name} сохранен")
    main_window.open_edit_screen()

def EditShowScreen(main_window, show=None):
    main_window.clear_window()

    layout = QVBoxLayout()

    show_name_layout = QHBoxLayout()
    show_name_label = QLabel("Название спектакля:")
    show_name_label.setFont(QFont("Arial", 12))
    show_name_label.setStyleSheet("color: #333;")
    show_name_input = QLineEdit()
    if show:
        show_name_input.setText(show['name'])
    show_name_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    show_name_layout.addWidget(show_name_label)
    show_name_layout.addWidget(show_name_input)
    layout.addLayout(show_name_layout)

    save_button = QPushButton("Сохранить")
    save_button.setFont(QFont("Arial", 12))
    save_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 8px;")
    save_button.clicked.connect(lambda: save_show(main_window, show, show_name_input))
    layout.addWidget(save_button, alignment=Qt.AlignCenter)

    back_button = QPushButton("Назад")
    back_button.setFont(QFont("Arial", 12))
    back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
    back_button.clicked.connect(main_window.open_edit_screen)
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    container = QWidget()
    container.setLayout(layout)
    main_window.setCentralWidget(container)

def save_show(main_window, show, show_name_input):
    show_name = show_name_input.text()

    if show:
        show['name'] = show_name
    else:
        show_id = len(main_window.shows) + 1
        main_window.shows[show_id] = {'name': show_name}

    QMessageBox.information(main_window, "Сохранение", f"Спектакль {show_name} сохранен")
    main_window.open_edit_screen()

def AddSessionScreen(main_window, date):
    main_window.clear_window()

    layout = QVBoxLayout()

    label = QLabel(f"Добавление сеанса на {days_translation[date.strftime('%A')]} {date.strftime('%d.%m.%Y')}")
    label.setFont(QFont("Arial", 16))
    label.setStyleSheet("color: #333;")
    layout.addWidget(label, alignment=Qt.AlignCenter)

    add_session_button = QPushButton("+")
    add_session_button.setFont(QFont("Arial", 14))
    add_session_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 10px;")
    add_session_button.clicked.connect(lambda: EditSessionScreen(main_window, date))
    layout.addWidget(add_session_button, alignment=Qt.AlignCenter)

    sessions_list = QVBoxLayout()
    layout.addLayout(sessions_list)

    update_sessions_list(main_window, date, sessions_list)

    back_button = QPushButton("Назад")
    back_button.setFont(QFont("Arial", 12))
    back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
    back_button.clicked.connect(lambda: main_window.open_edit_screen())
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    container = QWidget()
    container.setLayout(layout)
    main_window.setCentralWidget(container)

def update_sessions_list(main_window, date, sessions_list):
    for i in reversed(range(sessions_list.count())):
        sessions_list.itemAt(i).widget().setParent(None)
    if date in main_window.sessions:
        for session in main_window.sessions[date]:
            session_button = QPushButton(f"{session['time']} - {session['show']} - {session['hall']}")
            session_button.setFont(QFont("Arial", 12))
            session_button.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; padding: 8px;")
            session_button.clicked.connect(lambda checked, s=session: EditSessionScreen(main_window, date, s))
            sessions_list.addWidget(session_button)

def EditSessionScreen(main_window, date, session=None):
    main_window.clear_window()

    layout = QVBoxLayout()

    time_layout = QHBoxLayout()
    time_label = QLabel("Время:")
    time_label.setFont(QFont("Arial", 12))
    time_label.setStyleSheet("color: #333;")
    time_edit = QTimeEdit()
    if session:
        time_edit.setTime(QTime.fromString(session['time'], "hh:mm"))
    time_edit.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    time_layout.addWidget(time_label)
    time_layout.addWidget(time_edit)
    layout.addLayout(time_layout)

    show_layout = QHBoxLayout()
    show_label = QLabel("Спектакль:")
    show_label.setFont(QFont("Arial", 12))
    show_label.setStyleSheet("color: #333;")
    show_combo = QComboBox()
    for show in main_window.shows.values():
        show_combo.addItem(show['name'])
    if session:
        show_combo.setCurrentText(session['show'])
    show_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    show_layout.addWidget(show_label)
    show_layout.addWidget(show_combo)
    layout.addLayout(show_layout)

    hall_layout = QHBoxLayout()
    hall_label = QLabel("Зал:")
    hall_label.setFont(QFont("Arial", 12))
    hall_label.setStyleSheet("color: #333;")
    hall_combo = QComboBox()
    for hall in main_window.halls:
        hall_combo.addItem(hall['name'])
    if session:
        hall_combo.setCurrentText(session['hall'])
    hall_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    hall_layout.addWidget(hall_label)
    hall_layout.addWidget(hall_combo)
    layout.addLayout(hall_layout)

    price_layout = QHBoxLayout()
    price_label = QLabel("Цена:")
    price_label.setFont(QFont("Arial", 12))
    price_label.setStyleSheet("color: #333;")
    price_spin = QSpinBox()
    price_spin.setMinimum(0)
    price_spin.setMaximum(10000)
    if session:
        price_spin.setValue(session['price'])
    price_spin.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
    price_layout.addWidget(price_label)
    price_layout.addWidget(price_spin)
    layout.addLayout(price_layout)

    save_button = QPushButton("Сохранить")
    save_button.setFont(QFont("Arial", 12))
    save_button.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; padding: 8px;")
    save_button.clicked.connect(lambda: save_session(main_window, date, session, time_edit, show_combo, hall_combo, price_spin))
    layout.addWidget(save_button, alignment=Qt.AlignCenter)

    back_button = QPushButton("Назад")
    back_button.setFont(QFont("Arial", 12))
    back_button.setStyleSheet("background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;")
    back_button.clicked.connect(lambda: AddSessionScreen(main_window, date))
    layout.addWidget(back_button, alignment=Qt.AlignCenter)

    container = QWidget()
    container.setLayout(layout)
    main_window.setCentralWidget(container)


def save_session(main_window, date, session, time_edit, show_combo, hall_combo, price_spin):
    session_time = time_edit.time().toString("hh:mm")
    session_show = show_combo.currentText()
    session_hall = hall_combo.currentText()
    session_price = price_spin.value()

    session_data = {
        'time': session_time,
        'show': session_show,
        'hall': session_hall,
        'price': session_price
    }

    if session:
        if date in main_window.sessions:
            for i, s in enumerate(main_window.sessions[date]):
                if s == session:
                    main_window.sessions[date][i] = session_data
                    break
    else:
        if date not in main_window.sessions:
            main_window.sessions[date] = []
        main_window.sessions[date].append(session_data)

    save_sessions_to_file(main_window.sessions)  # Сохраняем сеансы на диск

    QMessageBox.information(main_window, "Сохранение",
                            f"Сеанс {session_time}, {session_show}, {session_hall}, {session_price} сохранен")

    if main_window.current_week_tab:
        main_window.current_week_tab.update_sessions_list()
    if main_window.next_week_tab:
        main_window.next_week_tab.update_sessions_list()

    AddSessionScreen(main_window, date)

def save_sessions_to_file(sessions, filename='sessions.json'):
    # Преобразуем ключи datetime в строки
    sessions_str_keys = {date.strftime('%Y-%m-%d'): sessions[date] for date in sessions}
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sessions_str_keys, f, ensure_ascii=False, indent=4)
    print(f"Сеансы сохранены в файл: {sessions_str_keys}")

def load_sessions_from_file(filename='sessions.json'):
    if not Path(filename).exists():
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sessions_str_keys = json.load(f)
            # Преобразуем ключи строки обратно в datetime
            sessions = {datetime.strptime(date_str, '%Y-%m-%d'): sessions_str_keys[date_str] for date_str in sessions_str_keys}
            print(f"Сеансы загружены из файла: {sessions}")
            return sessions
    except json.JSONDecodeError as e:
        print(f"Ошибка при загрузке файла {filename}: {e}")
        return {}

def load_sessions_from_file(filename='sessions.json'):
    if not Path(filename).exists():
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sessions_str_keys = json.load(f)
            # Преобразуем ключи строки обратно в datetime
            sessions = {datetime.strptime(date_str, '%Y-%m-%d'): sessions_str_keys[date_str] for date_str in sessions_str_keys}
            return sessions
    except json.JSONDecodeError as e:
        print(f"Ошибка при загрузке файла {filename}: {e}")
        return {}

if __name__ == "__main__":
    main()
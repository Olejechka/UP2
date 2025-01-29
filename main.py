from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QTabWidget, QScrollArea, QLineEdit, QComboBox, QDialog, QHBoxLayout, QMessageBox, QTimeEdit, QGridLayout
from PyQt5.QtCore import QDate, QTime
import psycopg2
from psycopg2 import sql

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Билетная касса театра")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)  # Запрещаем изменение размера окна

        self.conn = psycopg2.connect(
            dbname="theatre",
            user="postgres",
            password="2408",
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()

        self.halls = self.load_halls()
        self.performances = self.load_performances()
        self.sessions = self.load_sessions()
        self.hall_types = self.load_hall_types()
        self.hall_buttons = {}  # Инициализация словаря для хранения кнопок залов
        self.performance_buttons = {}  # Инициализация словаря для хранения кнопок спектаклей
        self.session_buttons = {}  # Инициализация словаря для хранения кнопок сеансов
        self.editable = False  # Флаг для режима редактирования

        self.show_main_menu()

    def load_halls(self):
        self.cur.execute("SELECT h.id, h.name, ht.id, ht.description, ht.rows, ht.seats FROM halls h JOIN hall_types ht ON h.hall_type_id = ht.id")
        return [dict(id=row[0], name=row[1], type=row[2], type_description=row[3], rows=row[4], seats=row[5]) for row in self.cur.fetchall()]

    def load_performances(self):
        self.cur.execute("SELECT * FROM performances")
        return [dict(id=row[0], name=row[1]) for row in self.cur.fetchall()]

    def load_sessions(self):
        self.cur.execute("SELECT s.id, s.date, s.hall_id, s.performance_id, s.time, s.price FROM sessions s")
        sessions = []
        for row in self.cur.fetchall():
            hall_id = row[2]
            performance_id = row[3]
            hall = next((hall for hall in self.halls if hall["id"] == hall_id), None)
            performance = next((performance for performance in self.performances if performance["id"] == performance_id), None)
            session = dict(
                id=row[0],
                date=QDate.fromString(row[1].strftime('%Y-%m-%d'), 'yyyy-MM-dd'),
                hall_id=hall_id,
                performance_id=performance_id,
                hall=hall,
                performance=performance,
                time=QTime.fromString(row[4].strftime('%H:%M:%S'), 'HH:mm:ss'),
                price=row[5],
                seats=set()
            )
            sessions.append(session)
        sessions_dict = {}
        for session in sessions:
            if session['date'] not in sessions_dict:
                sessions_dict[session['date']] = []
            sessions_dict[session['date']].append(session)
        return sessions_dict

    def load_hall_types(self):
        self.cur.execute("SELECT * FROM hall_types")
        return [dict(id=row[0], description=row[1], rows=row[2], seats=row[3]) for row in self.cur.fetchall()]

    def load_reserved_seats(self):
        self.cur.execute("SELECT session_id, row, seat FROM reserved_seats")
        reserved_seats = self.cur.fetchall()
        for session_id, row, seat in reserved_seats:
            for session in self.sessions.values():
                for s in session:
                    if s["id"] == session_id:
                        s["seats"].add((row, seat))
                        break

    def add_hall(self):
        name = f"Зал {len(self.halls) + 1}"
        hall_type_id = 1  # По умолчанию выбираем первый тип зала
        self.cur.execute("INSERT INTO halls (name, hall_type_id) VALUES (%s, %s) RETURNING id", (name, hall_type_id))
        hall_id = self.cur.fetchone()[0]
        self.conn.commit()
        hall = {"id": hall_id, "name": name, "type": hall_type_id, "type_description": self.hall_types[0]['description'], "rows": self.hall_types[0]['rows'], "seats": self.hall_types[0]['seats']}
        self.halls.append(hall)
        self.create_hall_button(hall)

    def save_hall_changes(self, hall, name_edit, type_combo, dialog, size_label):
        hall["name"] = name_edit.text()
        hall["type"] = self.hall_types[type_combo.currentIndex()]['id']
        hall["type_description"] = self.hall_types[type_combo.currentIndex()]['description']
        hall["rows"] = self.hall_types[type_combo.currentIndex()]['rows']
        hall["seats"] = self.hall_types[type_combo.currentIndex()]['seats']
        self.cur.execute("UPDATE halls SET name = %s, hall_type_id = %s WHERE id = %s", (hall["name"], hall["type"], hall["id"]))
        self.conn.commit()
        self.hall_buttons[hall["id"]].setText(hall["name"])
        dialog.accept()

    def delete_hall(self, hall, dialog):
        reply = QMessageBox.question(self, 'Удаление зала', f"Вы уверены, что хотите удалить зал {hall['name']}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Проверка наличия связанных сеансов
            self.cur.execute("SELECT COUNT(*) FROM sessions WHERE hall_id = %s", (hall["id"],))
            session_count = self.cur.fetchone()[0]
            if session_count > 0:
                QMessageBox.warning(self, "Ошибка", f"Невозможно удалить зал {hall['name']}, так как он используется в {session_count} сеансах.")
                return

            # Удаление зала
            self.cur.execute("DELETE FROM halls WHERE id = %s", (hall["id"],))
            self.conn.commit()
            self.halls.remove(hall)
            self.hall_buttons[hall["id"]].deleteLater()
            del self.hall_buttons[hall["id"]]
            dialog.accept()

    def add_performance(self):
        name = f"Спектакль {len(self.performances) + 1}"
        self.cur.execute("INSERT INTO performances (name) VALUES (%s) RETURNING id", (name,))
        performance_id = self.cur.fetchone()[0]
        self.conn.commit()
        performance = {"id": performance_id, "name": name}
        self.performances.append(performance)
        self.create_performance_button(performance)

    def save_performance_changes(self, performance, name_edit, dialog):
        performance["name"] = name_edit.text()
        self.cur.execute("UPDATE performances SET name = %s WHERE id = %s", (performance["name"], performance["id"]))
        self.conn.commit()
        self.performance_buttons[performance["id"]].setText(performance["name"])
        dialog.accept()

    def delete_performance(self, performance, dialog):
        reply = QMessageBox.question(self, 'Удаление спектакля', f"Вы уверены, что хотите удалить спектакль {performance['name']}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Проверка наличия связанных сеансов
            self.cur.execute("SELECT COUNT(*) FROM sessions WHERE performance_id = %s", (performance["id"],))
            session_count = self.cur.fetchone()[0]
            if session_count > 0:
                QMessageBox.warning(self, "Ошибка", f"Невозможно удалить спектакль {performance['name']}, так как он используется в {session_count} сеансах.")
                return

            # Удаление спектакля
            self.cur.execute("DELETE FROM performances WHERE id = %s", (performance["id"],))
            self.conn.commit()
            self.performances.remove(performance)
            self.performance_buttons[performance["id"]].deleteLater()
            del self.performance_buttons[performance["id"]]
            dialog.accept()

    def add_session(self, date):
        if not self.halls:
            QMessageBox.warning(self, "Ошибка", "Нет доступных залов. Пожалуйста, добавьте хотя бы один зал.")
            return

        if not self.performances:
            QMessageBox.warning(self, "Ошибка", "Нет доступных спектаклей. Пожалуйста, добавьте хотя бы один спектакль.")
            return

        hall = self.halls[0] if self.halls else None
        performance = self.performances[0] if self.performances else None
        date_str = date.toString('yyyy-MM-dd')  # Преобразуем QDate в строку формата YYYY-MM-DD
        time_str = QTime(19, 00).toString('HH:mm:ss')  # Преобразуем QTime в строку формата HH:MM:SS
        self.cur.execute("INSERT INTO sessions (date, hall_id, performance_id, time, price) VALUES (%s, %s, %s, %s, %s) RETURNING id", (date_str, hall["id"], performance["id"], time_str, 350))
        session_id = self.cur.fetchone()[0]
        self.conn.commit()
        session = {
            "id": session_id,
            "date": date,
            "hall_id": hall["id"],
            "performance_id": performance["id"],
            "hall": hall,
            "performance": performance,
            "time": QTime(19, 00),
            "price": 350,
            "seats": set()
        }
        if date not in self.sessions:
            self.sessions[date] = []
        self.sessions[date].append(session)
        self.create_session_button(session)

    def save_session_changes(self, session, hall_combo, performance_combo, time_edit, price_edit, dialog):
        session["hall"] = self.halls[hall_combo.currentIndex()]
        session["performance"] = self.performances[performance_combo.currentIndex()]
        session["time"] = time_edit.time()
        session["price"] = float(price_edit.text()) if price_edit.text() else 350
        time_str = session["time"].toString('HH:mm:ss')  # Преобразуем QTime в строку формата HH:MM:SS
        self.cur.execute("UPDATE sessions SET hall_id = %s, performance_id = %s, time = %s, price = %s WHERE id = %s", (session["hall"]["id"], session["performance"]["id"], time_str, session["price"], session["id"]))
        self.conn.commit()

        session_name = f"{session['hall']['name']} - {session['performance']['name']} - {session['time'].toString('HH:mm')}"
        self.session_buttons[session["id"]].setText(session_name)
        dialog.accept()

    def delete_session(self, session, dialog):
        reply = QMessageBox.question(self, 'Удаление сеанса', f"Вы уверены, что хотите удалить сеанс {session['id']}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Проверка наличия зарезервированных мест
            self.cur.execute("SELECT COUNT(*) FROM reserved_seats WHERE session_id = %s", (session["id"],))
            reserved_count = self.cur.fetchone()[0]
            if reserved_count > 0:
                QMessageBox.warning(self, "Внимание", f"Сеанс {session['id']} имеет {reserved_count} зарезервированных мест. Они будут автоматически удалены.")

            # Удаление сеанса
            try:
                self.cur.execute("DELETE FROM sessions WHERE id = %s", (session["id"],))
                self.conn.commit()
                if session["date"] in self.sessions:
                    self.sessions[session["date"]].remove(session)
                    if not self.sessions[session["date"]]:
                        del self.sessions[session["date"]]
                if session["id"] in self.session_buttons:
                    self.session_buttons[session["id"]].deleteLater()
                    del self.session_buttons[session["id"]]
                # Обновляем интерфейс
                self.update_day_sessions(session["date"])
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сеанс: {e}")
                self.conn.rollback()

    def reserve_seat(self, session, row, seat, seat_button):
        if (row, seat) in session["seats"]:
            session["seats"].remove((row, seat))
            seat_button.setStyleSheet('color: #555555; border: 1px solid #D3D3D3; background-color: #D3D3D3; font-size: 10px;')
            self.cur.execute("DELETE FROM reserved_seats WHERE session_id = %s AND row = %s AND seat = %s", (session["id"], row, seat))
            self.conn.commit()
        else:
            session["seats"].add((row, seat))
            seat_button.setStyleSheet('color: #FFFFFF; border: 1px solid #D3D3D3; background-color: #FF0000; font-size: 10px;')
            self.cur.execute("INSERT INTO reserved_seats (session_id, row, seat) VALUES (%s, %s, %s)", (session["id"], row, seat))
            self.conn.commit()

        # Обновляем интерфейс после изменения состояния мест
        self.update_seat_buttons(session)

    def update_seat_buttons(self, session):
        hall = session["hall"]
        if hall is None:
            QMessageBox.warning(self, "Ошибка", "Зал для сеанса не выбран.")
            return

        for row in range(hall["rows"]):
            for seat in range(hall["seats"]):
                seat_button = self.findChild(QPushButton, f"seat_{row}_{seat}_{session['id']}")
                if seat_button:
                    if (row, seat) in session["seats"]:
                        seat_button.setStyleSheet('color: #FFFFFF; border: 1px solid #D3D3D3; background-color: #FF0000; font-size: 10px;')
                    else:
                        seat_button.setStyleSheet('color: #555555; border: 1px solid #D3D3D3; background-color: #D3D3D3; font-size: 10px;')

    def show_main_menu(self):
        self.clear_window()
        self.editable = False  # Устанавливаем режим просмотра

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.create_label("Билетная касса театра", 250, 50, 400, 50, 24, 'black', 'bold')
        self.create_button("Перейти к сеансам", 250, 200, 300, 100, '#D3D3D3', self.show_sessions_menu)
        self.create_button("Редактировать", 250, 350, 300, 100, '#D3D3D3', self.show_edit_menu)

        central_widget.setLayout(layout)

    def show_sessions_menu(self):
        self.clear_window()
        self.editable = False  # Устанавливаем режим просмотра

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_current_week_tab(), "На тек. нед.")
        self.tabs.addTab(self.create_next_week_tab(), "На след. нед.")

        back_button = QPushButton("Назад", self)
        back_button.setGeometry(700, 10, 80, 40)
        back_button.setStyleSheet(
            'color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 16px; border-radius: 20px;')
        back_button.clicked.connect(self.show_main_menu)

        layout.addWidget(self.tabs)
        layout.addWidget(back_button)

        central_widget.setLayout(layout)

    def show_edit_menu(self):
        self.clear_window()
        self.editable = True  # Устанавливаем режим редактирования

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_halls_tab(), "Залы")
        self.tabs.addTab(self.create_performances_tab(), "Спектакли")
        self.tabs.addTab(self.create_current_week_tab(), "На тек. нед.")
        self.tabs.addTab(self.create_next_week_tab(), "На след. нед.")

        back_button = QPushButton("Назад", self)
        back_button.setGeometry(700, 10, 80, 40)
        back_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 16px; border-radius: 20px;')
        back_button.clicked.connect(self.show_main_menu)

        layout.addWidget(self.tabs)
        layout.addWidget(back_button)

        central_widget.setLayout(layout)

    def create_halls_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        add_hall_button = QPushButton("+", self)
        add_hall_button.setGeometry(350, 10, 50, 50)
        add_hall_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 24px; border-radius: 25px;')
        add_hall_button.clicked.connect(self.add_hall)

        self.hall_layout = QVBoxLayout()
        self.hall_layout.addWidget(add_hall_button)

        for hall in self.halls:
            self.create_hall_button(hall)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(self.hall_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        tab.setLayout(layout)

        return tab

    def create_hall_button(self, hall):
        hall_button = QPushButton(hall["name"], self)
        hall_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        hall_button.clicked.connect(lambda: self.edit_hall(hall))
        self.hall_layout.addWidget(hall_button)
        self.hall_buttons[hall["id"]] = hall_button

    def edit_hall(self, hall):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование зала {hall['name']}")
        dialog.setGeometry(100, 100, 400, 300)
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()

        name_label = QLabel("Название зала:", self)
        name_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(name_label)

        name_edit = QLineEdit(hall["name"], self)
        layout.addWidget(name_edit)

        type_label = QLabel("Тип зала:", self)
        type_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(type_label)

        type_combo = QComboBox(self)
        for hall_type in self.hall_types:
            type_combo.addItem(hall_type["description"])
        type_combo.currentIndexChanged.connect(lambda: self.update_hall_size(hall, type_combo, size_label))
        layout.addWidget(type_combo)

        size_label = QLabel("", self)
        size_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(size_label)

        type_combo.setCurrentIndex(hall["type"] - 1)
        self.update_hall_size(hall, type_combo, size_label)

        save_button = QPushButton("Сохранить", self)
        save_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        save_button.clicked.connect(lambda: self.save_hall_changes(hall, name_edit, type_combo, dialog, size_label))
        layout.addWidget(save_button)

        delete_button = QPushButton("Удалить", self)
        delete_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        delete_button.clicked.connect(lambda: self.delete_hall(hall, dialog))
        layout.addWidget(delete_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_hall_size(self, hall, type_combo, size_label):
        hall_type = self.hall_types[type_combo.currentIndex()]
        hall["type"] = hall_type["id"]
        hall["type_description"] = hall_type["description"]
        hall["rows"] = hall_type["rows"]
        hall["seats"] = hall_type["seats"]
        size_label.setText(f"Размер зала: {hall['rows']} рядов, {hall['seats']} мест")

    def create_performances_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        add_performance_button = QPushButton("+", self)
        add_performance_button.setGeometry(350, 10, 50, 50)
        add_performance_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 24px; border-radius: 25px;')
        add_performance_button.clicked.connect(self.add_performance)

        self.performance_layout = QVBoxLayout()
        self.performance_layout.addWidget(add_performance_button)

        for performance in self.performances:
            self.create_performance_button(performance)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(self.performance_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        tab.setLayout(layout)

        return tab

    def create_performance_button(self, performance):
        performance_button = QPushButton(performance["name"], self)
        performance_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        performance_button.clicked.connect(lambda: self.edit_performance(performance))
        self.performance_layout.addWidget(performance_button)
        self.performance_buttons[performance["id"]] = performance_button

    def edit_performance(self, performance):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование спектакля {performance['name']}")
        dialog.setGeometry(100, 100, 400, 300)
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()

        name_label = QLabel("Название спектакля:", self)
        name_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(name_label)

        name_edit = QLineEdit(performance["name"], self)
        layout.addWidget(name_edit)

        save_button = QPushButton("Сохранить", self)
        save_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        save_button.clicked.connect(lambda: self.save_performance_changes(performance, name_edit, dialog))
        layout.addWidget(save_button)

        delete_button = QPushButton("Удалить", self)
        delete_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        delete_button.clicked.connect(lambda: self.delete_performance(performance, dialog))
        layout.addWidget(delete_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def create_session_button(self, session):
        if session["hall"] and session["performance"] and session["time"]:
            session_name = f"{session['hall']['name']} - {session['performance']['name']} - {session['time'].toString('HH:mm')}"
        else:
            session_name = f"Сеанс {session['id']}"

        session_button = QPushButton(session_name, self)
        session_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        if self.editable:
            session_button.clicked.connect(lambda: self.edit_session(session))
        else:
            session_button.clicked.connect(lambda: self.show_seat_selection_dialog(session))
        self.session_layout.addWidget(session_button)
        self.session_buttons[session["id"]] = session_button

    def edit_session(self, session):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование сеанса {session['id']}")
        dialog.setGeometry(100, 100, 400, 300)
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()

        hall_label = QLabel("Зал:", self)
        hall_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(hall_label)

        hall_combo = QComboBox(self)
        for hall in self.halls:
            hall_combo.addItem(hall["name"])
        hall_combo.setCurrentIndex(next(i for i, hall in enumerate(self.halls) if hall["id"] == session["hall"]["id"]))
        layout.addWidget(hall_combo)

        performance_label = QLabel("Спектакль:", self)
        performance_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(performance_label)

        performance_combo = QComboBox(self)
        for performance in self.performances:
            performance_combo.addItem(performance["name"])
        performance_combo.setCurrentIndex(next(i for i, performance in enumerate(self.performances) if performance["id"] == session["performance"]["id"]))
        layout.addWidget(performance_combo)

        time_label = QLabel("Время:", self)
        time_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(time_label)

        time_edit = QTimeEdit(self)
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(session["time"])
        layout.addWidget(time_edit)

        price_label = QLabel("Стоимость:", self)
        price_label.setStyleSheet('font-size: 16px;')
        layout.addWidget(price_label)

        price_edit = QLineEdit(self)
        price_edit.setText(str(session["price"]))
        layout.addWidget(price_edit)

        save_button = QPushButton("Сохранить", self)
        save_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        save_button.clicked.connect(lambda: self.save_session_changes(session, hall_combo, performance_combo, time_edit, price_edit, dialog))
        layout.addWidget(save_button)

        delete_button = QPushButton("Удалить", self)
        delete_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        delete_button.clicked.connect(lambda: self.delete_session(session, dialog))
        layout.addWidget(delete_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def create_current_week_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        current_date = QDate.currentDate()
        start_of_week = current_date.addDays(-(current_date.dayOfWeek() - 1))
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

        for i in range(6):
            day_date = start_of_week.addDays(i)
            day_button = QPushButton(f"{days[i]} {day_date.toString('dd.MM.yyyy')}", self)
            day_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 16px; border-radius: 20px;')
            day_button.clicked.connect(lambda checked, date=day_date: self.show_day_sessions(date))
            layout.addWidget(day_button)

        tab.setLayout(layout)
        return tab

    def create_next_week_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        current_date = QDate.currentDate()
        start_of_week = current_date.addDays(-(current_date.dayOfWeek() - 1))
        start_of_next_week = start_of_week.addDays(7)
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

        for i in range(6):
            day_date = start_of_next_week.addDays(i)
            day_button = QPushButton(f"{days[i]} {day_date.toString('dd.MM.yyyy')}", self)
            day_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 16px; border-radius: 20px;')
            day_button.clicked.connect(lambda checked, date=day_date: self.show_day_sessions(date))
            layout.addWidget(day_button)

        tab.setLayout(layout)
        return tab

    def show_day_sessions(self, date):
        self.load_reserved_seats()  # Обновляем забронированные места
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Сеансы на {date.toString('dd.MM.yyyy')}")
        dialog.setGeometry(100, 100, 600, 400)
        dialog.setFixedSize(600, 400)

        layout = QVBoxLayout()

        if self.editable:
            add_session_button = QPushButton("+", self)
            add_session_button.setStyleSheet(
                'color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 24px; border-radius: 25px;')
            add_session_button.clicked.connect(lambda: self.add_session(date))
            layout.addWidget(add_session_button)

        self.session_layout = QVBoxLayout()

        # Обновляем интерфейс сеансов
        self.update_day_sessions(date)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(self.session_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        dialog.setLayout(layout)
        dialog.exec_()

    def update_day_sessions(self, date):
        self.load_reserved_seats()  # Обновляем забронированные места
        # Очищаем текущий список сеансов для данной даты
        for i in reversed(range(self.session_layout.count())):
            widget = self.session_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Загружаем актуальные сеансы из базы данных
        self.sessions = self.load_sessions()

        # Создаем новые кнопки для сеансов
        if date in self.sessions:
            for session in self.sessions[date]:
                self.create_session_button(session)

    def show_seat_selection_dialog(self, session):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Выбор мест для сеанса {session['id']}")
        dialog.setFixedSize(600, 400)

        layout = QVBoxLayout()

        hall = session["hall"]
        if hall is None:
            QMessageBox.warning(self, "Ошибка", "Зал для сеанса не выбран.")
            dialog.reject()
            return

        seats_layout = QGridLayout()
        for row in range(hall["rows"]):
            for seat in range(hall["seats"]):
                seat_button = QPushButton(f"{row+1}-{seat+1}", self)
                seat_button.setFixedSize(30, 30)
                seat_button.setObjectName(f"seat_{row}_{seat}_{session['id']}")
                if (row, seat) in session["seats"]:
                    seat_button.setStyleSheet('color: #FFFFFF; border: 1px solid #D3D3D3; background-color: #FF0000; font-size: 10px;')
                else:
                    seat_button.setStyleSheet('color: #555555; border: 1px solid #D3D3D3; background-color: #D3D3D3; font-size: 10px;')
                seat_button.clicked.connect(lambda checked, r=row, s=seat, b=seat_button: self.reserve_seat(session, r, s, b))
                seats_layout.addWidget(seat_button, row, seat)

        dialog_width = (hall["seats"] * 30) + 40
        dialog_height = (hall["rows"] * 30) + 80
        dialog.setFixedSize(dialog_width, dialog_height)

        layout.addLayout(seats_layout)

        save_button = QPushButton("Сохранить", self)
        save_button.setStyleSheet('color: #555555; border: 3px solid #D3D3D3; background-color: #D3D3D3; font-size: 20px; border-radius: 30px;')
        save_button.clicked.connect(dialog.accept)
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def clear_window(self):
        for widget in self.findChildren(QWidget):
            widget.deleteLater()

    def create_label(self, text, sx, sy, x, y, size, color, weight):
        label = QLabel(text, self)
        label.setGeometry(sx, sy, x, y)
        label.setStyleSheet(
            f'color: {color}; font-size: {size}px; background-color: rgba(255,255,255,0); font-weight: {weight}')
        label.show()

    def create_button(self, text, sx, sy, x, y, color, action, inv_cal=False):
        button = QPushButton(text, self)
        button.setGeometry(sx, sy, x, y)
        text_color = '#555555' if not inv_cal else color
        bg_color = color if not inv_cal else 'white'
        border_color = color if not inv_cal else 'white'
        button.setStyleSheet(
            f'color: {text_color}; border: 3px solid {border_color}; background-color: {bg_color}; font-size: 20px; border-radius: 30px;')
        button.clicked.connect(action)
        button.show()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
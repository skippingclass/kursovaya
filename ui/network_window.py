"""Qt screens for the HTTP demonstration of the college system."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGridLayout, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from config import ROLE_ADMIN, ROLE_OPERATOR
from ui.api_client import ApiError

COLUMNS = {
    "teachers": (("full_name", "ФИО"), ("department", "Кафедра"), ("experience", "Стаж"),
                 ("status", "Статус"), ("hours", "Часы")),
    "pools": (("academic_year", "Учебный год"), ("semester", "Семестр"), ("group_name", "Группа"),
              ("discipline", "Дисциплина"), ("hours_lecture", "Теория"), ("hours_practice", "Практика"),
              ("available_lecture", "Свободно теории"), ("available_practice", "Свободно практики")),
    "assignments": (("academic_year", "Учебный год"), ("semester", "Семестр"), ("group_name", "Группа"),
                    ("teacher", "Преподаватель"), ("discipline", "Дисциплина"),
                    ("hours_lecture", "Теория"), ("hours_practice", "Практика"),
                    ("total_hours", "Всего"), ("hours_per_week", "В неделю")),
}


def combo(items, selected=None):
    widget = QComboBox()
    for label, value in items:
        widget.addItem(label, value)
    index = widget.findData(selected)
    if index >= 0:
        widget.setCurrentIndex(index)
    return widget


def spin(limit, value, minimum=0):
    widget = QSpinBox()
    widget.setRange(minimum, limit)
    widget.setValue(value)
    return widget


class NetworkLogin(QDialog):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.user = None
        self.setWindowTitle("Вход в клиент")
        self.setMinimumWidth(380)
        form = QFormLayout(self)
        self.username = QLineEdit()
        self.password = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.password.setMaxLength(256)
        form.addRow("Логин", self.username)
        form.addRow("Пароль", self.password)
        form.addRow(QLabel(client.url.rsplit("/api/v1", 1)[0]))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Войти")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self):
        try:
            self.user = self.client.login(self.username.text().strip(), self.password.text())
        except ApiError as exc:
            QMessageBox.warning(self, "Вход", str(exc))
            return
        super().accept()


class EditForm(QDialog):
    def __init__(self, parent, title, fields, save):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 10)
        self.fields = fields
        self.save = save
        form = QFormLayout(self)
        for _, (label, field) in fields.items():
            form.addRow(label, field)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self):
        values = {}
        for key, (_, widget) in self.fields.items():
            if isinstance(widget, QComboBox):
                values[key] = widget.currentData()
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            else:
                values[key] = widget.text().strip()
        try:
            self.save(values)
        except ApiError as exc:
            QMessageBox.warning(self, "Проверьте данные", str(exc))
            return
        super().accept()


class NetworkWindow(QMainWindow):
    def __init__(self, client, user):
        super().__init__()
        self.client = client
        self.user = user
        self.tables = {}
        self.setWindowTitle("Учет преподавателей и учебной нагрузки")
        self.resize(1180, 660)
        self.setMinimumSize(750, 460)
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout(self.centralWidget())
        header = QHBoxLayout()
        header.addWidget(QLabel("Учет преподавателей и учебной нагрузки"))
        header.addStretch()
        header.addWidget(QLabel(user["username"] + "  ·  " + user["role_name"]))
        header.addWidget(self.button("Выйти", self.close))
        layout.addLayout(header)

        filters = QGridLayout()
        self.search = QLineEdit(placeholderText="Поиск преподавателя")
        self.year = combo([("Все годы", None)] + [(year, year) for year in client.request("/years")])
        self.semester = combo([("Все семестры", None), ("Семестр 1", 1), ("Семестр 2", 2), ("Архив", 0)])
        self.teacher = combo([("Все преподаватели", None)])
        self.department = combo([("Все кафедры", None)] +
                                [(row["name"], row["id"]) for row in client.request("/departments")])
        self.search.returnPressed.connect(self.refresh)
        filters.addWidget(self.year, 0, 0)
        filters.addWidget(self.semester, 0, 1)
        filters.addWidget(self.department, 0, 2)
        filters.addWidget(self.teacher, 1, 0, 1, 2)
        filters.addWidget(self.search, 1, 2)
        filters.addWidget(self.button("Применить", self.refresh), 0, 3, 2, 1)
        layout.addLayout(filters)

        self.tabs = QTabWidget()
        for resource, label in [("teachers", "Преподаватели"), ("pools", "Общий план"),
                                ("assignments", "Назначения и ведомость")]:
            self.tabs.addTab(self.make_tab(resource), label)
        layout.addWidget(self.tabs, 1)
        self.applied_filters = {}
        self.refresh(raise_errors=True)

    def button(self, text, action):
        button = QPushButton(text)
        button.clicked.connect(action)
        return button

    def make_tab(self, resource):
        page = QWidget()
        layout = QVBoxLayout(page)
        table = QTableWidget(0, len(COLUMNS[resource]))
        table.setHorizontalHeaderLabels([label for _, label in COLUMNS[resource]])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setDefaultSectionSize(104)
        table.horizontalHeader().setStretchLastSection(True)
        widths = {"full_name": 245, "teacher": 245, "department": 245, "discipline": 278,
                  "semester": 90, "group_name": 115, "hours_lecture": 87, "hours_practice": 87,
                  "available_lecture": 150, "available_practice": 150}
        for index, (key, _) in enumerate(COLUMNS[resource]):
            if key in widths:
                table.setColumnWidth(index, widths[key])
        self.tables[resource] = table
        layout.addWidget(table, 1)
        actions = QHBoxLayout()
        if resource != "teachers" and self.user["role_name"] in (ROLE_ADMIN, ROLE_OPERATOR):
            actions.addWidget(self.button("Добавить", lambda: self.edit(resource)))
            actions.addWidget(self.button("Изменить", lambda: self.edit(resource, existing=True)))
            actions.addWidget(self.button("Удалить", lambda: self.delete(resource)))
        actions.addStretch()
        if resource == "assignments":
            for fmt in ("xlsx", "pdf"):
                actions.addWidget(self.button(fmt.upper(), lambda checked=False, fmt=fmt: self.export(fmt)))
        layout.addLayout(actions)
        return page

    def filters(self):
        return {"academic_year": self.year.currentData(), "semester": self.semester.currentData(),
                "department_id": self.department.currentData(), "teacher_id": self.teacher.currentData()}

    def refresh_teachers(self):
        current = self.teacher.currentData()
        self.teacher.clear()
        self.teacher.addItem("Все преподаватели", None)
        for row in self.client.request("/teachers"):
            self.teacher.addItem(row["full_name"], row["id"])
        self.teacher.setCurrentIndex(max(0, self.teacher.findData(current)))

    def refresh(self, *, raise_errors=False):
        try:
            self.refresh_teachers()
            filters = self.filters()
            parameters = {
                "teachers": {"search": self.search.text(), "academic_year": filters["academic_year"],
                             "department_id": filters["department_id"]},
                "pools": {key: value for key, value in filters.items() if key != "teacher_id"},
                "assignments": filters,
            }
            rows = {key: self.client.request("/" + key, params=query) for key, query in parameters.items()}
        except ApiError as exc:
            if raise_errors:
                raise
            self.show_error(exc)
            return
        for resource, values in rows.items():
            self.set_rows(resource, values)
        self.applied_filters = filters
        self.statusBar().showMessage(f"Строк в ведомости: {len(rows['assignments'])}")

    def set_rows(self, resource, rows):
        table = self.tables[resource]
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            for column, (key, _) in enumerate(COLUMNS[resource]):
                item = QTableWidgetItem()
                if key == "semester" and row[key] == 0:
                    item.setText("Не указан")
                else:
                    item.setData(Qt.ItemDataRole.DisplayRole, row[key])
                    if isinstance(row[key], str):
                        item.setToolTip(row[key])
                item.setData(Qt.ItemDataRole.UserRole, row)
                table.setItem(index, column, item)
        table.setSortingEnabled(True)

    def selected(self, resource):
        table = self.tables[resource]
        item = table.item(table.currentRow(), 0)
        if item is None:
            raise ApiError("Выберите строку в таблице.")
        return item.data(Qt.ItemDataRole.UserRole)

    def pool_fields(self, row):
        disciplines = self.client.request("/disciplines")
        year = row.get("academic_year", self.year.currentData() or self.year.itemData(1) or "")
        return {
            "academic_year": ("Учебный год", QLineEdit(year)),
            "semester": ("Семестр", combo([("1", 1), ("2", 2)], row.get("semester") or 1)),
            "group_name": ("Группа", QLineEdit(row.get("group_name", ""))),
            "discipline_id": ("Дисциплина", combo([(d["code"] + " · " + d["name"], d["id"]) for d in disciplines],
                                                 row.get("discipline_id"))),
            "weeks": ("Учебные недели", spin(52, row.get("weeks", 18), 1)),
        }

    def assignment_fields(self, row):
        pools = self.client.request("/pools")
        teachers = self.client.request("/teachers")
        return {
            "pool_id": ("Строка плана", combo(
                [(f"{p['academic_year']} · {p['semester']} · {p['group_name']} · {p['discipline']} "
                  f"({p['available_lecture']}/{p['available_practice']} ч.)", p["id"]) for p in pools],
                row.get("pool_id"))),
            "teacher_id": ("Преподаватель", combo([(t["full_name"], t["id"]) for t in teachers
                                                    if t["status"] != "уволен"], row.get("teacher_id"))),
        }

    def edit(self, resource, existing=False):
        try:
            row = self.selected(resource) if existing else {}
            fields = self.pool_fields(row) if resource == "pools" else self.assignment_fields(row)
        except ApiError as exc:
            self.show_error(exc)
            return
        fields["hours_lecture"] = ("Часы теории", spin(1000000, row.get("hours_lecture", 0)))
        fields["hours_practice"] = ("Часы практики", spin(1000000, row.get("hours_practice", 0)))
        path = f"/{resource}/{row['id']}" if existing else f"/{resource}"
        method = "PUT" if existing else "POST"
        form = EditForm(self, "Общий план" if resource == "pools" else "Назначение", fields,
                        lambda values: self.client.request(path, method=method, data=values))
        if form.exec():
            self.refresh()
        elif not self.client.token:
            self.close()

    def delete(self, resource):
        try:
            row = self.selected(resource)
            if QMessageBox.question(self, "Удаление", "Удалить выбранную строку?") != QMessageBox.StandardButton.Yes:
                return
            self.client.request(f"/{resource}/{row['id']}", method="DELETE")
        except ApiError as exc:
            self.show_error(exc)
            return
        self.refresh()

    def export(self, fmt):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить ведомость", f"Ведомость.{fmt}", f"*.{fmt}")
        if not path:
            return
        try:
            report = self.client.request(f"/reports/workload/{fmt}", params=self.applied_filters, binary=True)
            destination = Path(path)
            if not destination.suffix:
                destination = destination.with_suffix(f".{fmt}")
            destination.write_bytes(report)
        except (ApiError, OSError) as exc:
            self.show_error(exc)
            return
        self.statusBar().showMessage("Ведомость сохранена", 4500)

    def show_error(self, exc):
        QMessageBox.warning(self, "Работа с сервером", str(exc))
        if not self.client.token:
            self.close()

    def closeEvent(self, event):
        if self.client.token:
            try:
                self.client.request("/auth/session", method="DELETE")
            except ApiError:
                pass
            self.client.token = None
        super().closeEvent(event)

"""
Топ-монохромный дизайн в стиле TuneCloud (TuneCloud / Vercel / Linear dark aesthetic).
Глубокий матовый черный, чистые серые границы, высококонтрастная типографика и плавные акценты.
"""

APP_STYLE = """
QTableWidget {
    alternate-background-color: #141419;
}
/* Базовые стили окон */
QMainWindow, QDialog {
    background-color: #09090b;
    color: #f4f4f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #f4f4f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    background-color: transparent;
}

QMainWindow, QDialog {
    background-color: #09090b;
}

/* Верхнее меню */
QMenuBar {
    background-color: #09090b;
    color: #a1a1aa;
    border-bottom: 1px solid #1f1f23;
    padding: 4px 8px;
    font-weight: 500;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
    color: #d4d4d8;
}

QMenuBar::item:selected {
    background-color: #18181b;
    color: #ffffff;
}

QMenu {
    background-color: #111114;
    color: #f4f4f5;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #27272a;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #27272a;
    margin: 4px 6px;
}

/* Статус-бар */
QStatusBar {
    background-color: #09090b;
    border-top: 1px solid #1f1f23;
    color: #71717a;
    font-size: 12px;
    padding: 4px 10px;
}

/* Вкладки (QTabWidget) */
QTabWidget::pane {
    border: 1px solid #27272a;
    background-color: #0c0c10;
    border-radius: 10px;
    top: -1px;
}

QTabBar {
    background-color: transparent;
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: #141418;
    color: #82828e;
    padding: 10px 22px;
    margin-right: 6px;
    border: 1px solid #222227;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    min-width: 110px;
}

QTabBar::tab:selected {
    background-color: #0c0c10;
    color: #ffffff;
    border: 1px solid #27272a;
    border-bottom: 1px solid #0c0c10;
    border-top: 2px solid #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #1a1a22;
    color: #d4d4d8;
    border-color: #2e2e36;
}

/* Кнопки (QPushButton) */
QPushButton {
    background-color: #18181c;
    color: #f4f4f5;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #24242b;
    border-color: #3f3f46;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #141417;
}

QPushButton:disabled {
    background-color: #121215;
    border-color: #1c1c20;
    color: #52525b;
}

/* Монохромные акцентные кнопки (TuneCloud style) */
QPushButton#btnPrimary, QPushButton#btnSuccess {
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #ffffff;
    font-weight: 700;
}

QPushButton#btnPrimary:hover, QPushButton#btnSuccess:hover {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
    color: #000000;
}

QPushButton#btnPrimary:pressed, QPushButton#btnSuccess:pressed {
    background-color: #d4d4d8;
}

QPushButton#btnDanger {
    background-color: #1c1214;
    color: #f87171;
    border: 1px solid #3e1b20;
}

QPushButton#btnDanger:hover {
    background-color: #2e1619;
    border-color: #59222a;
    color: #fca5a5;
}

QPushButton#btnDanger:pressed {
    background-color: #180e10;
}

QPushButton#btnSecondary {
    background-color: #141418;
    color: #a1a1aa;
    border: 1px solid #27272a;
}

QPushButton#btnSecondary:hover {
    background-color: #202026;
    border-color: #383842;
    color: #ffffff;
}

/* Поля ввода (QLineEdit, QTextEdit, QPlainTextEdit) */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #121216;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 7px 12px;
    color: #f4f4f5;
    selection-background-color: #3f3f46;
}

QLineEdit:hover, QTextEdit:hover {
    border-color: #383840;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #ffffff;
    background-color: #15151b;
}

QLineEdit::placeholder {
    color: #52525b;
}

/* Выпадающие списки (QComboBox) */
QComboBox {
    background-color: #121216;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 7px 12px;
    color: #f4f4f5;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #383840;
}

QComboBox:focus {
    border: 1px solid #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a1a1aa;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #121216;
    border: 1px solid #27272a;
    border-radius: 8px;
    selection-background-color: #24242c;
    selection-color: #ffffff;
    padding: 6px;
    outline: none;
}

/* Счетчики (QSpinBox, QDateEdit) */
QSpinBox, QDateEdit {
    background-color: #121216;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 7px 10px;
    color: #f4f4f5;
    selection-background-color: #3f3f46;
}

QSpinBox:hover, QDateEdit:hover {
    border-color: #383840;
}

QSpinBox:focus, QDateEdit:focus {
    border: 1px solid #ffffff;
}

QSpinBox::up-button, QSpinBox::down-button, QDateEdit::up-button, QDateEdit::down-button {
    background: transparent;
    border: none;
    width: 18px;
}

/* Таблицы (QTableWidget, QTableView) */
QTableWidget, QTableView {
    background-color: #0c0c10;
    border: 1px solid #222227;
    border-radius: 8px;
    gridline-color: #191920;
    color: #f4f4f5;
    selection-background-color: #202028;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item, QTableView::item {
    padding: 8px 10px;
    border-bottom: 1px solid #16161c;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #22222b;
    color: #ffffff;
}

QTableWidget::item:hover:!selected, QTableView::item:hover:!selected {
    background-color: #141419;
}

QHeaderView::section {
    background-color: #141419;
    color: #8e8e99;
    font-weight: 700;
    font-size: 12px;
    padding: 9px 10px;
    border: none;
    border-bottom: 1px solid #27272a;
    border-right: 1px solid #1a1a20;
}

/* Радиокнопки (QRadioButton) */
QRadioButton {
    color: #d4d4d8;
    spacing: 10px;
    font-weight: 500;
}

QRadioButton:hover {
    color: #ffffff;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #3f3f46;
    background-color: #121216;
}

QRadioButton::indicator:hover {
    border-color: #71717a;
}

QRadioButton::indicator:checked {
    border: 5px solid #ffffff;
    background-color: #09090b;
}

/* Флажки (QCheckBox) */
QCheckBox {
    color: #d4d4d8;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #3f3f46;
    background-color: #121216;
}

QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
}

/* Группировочные рамки (QGroupBox) */
QGroupBox {
    background-color: #101014;
    border: 1px solid #24242a;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0px 8px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}

/* Карточки (QFrame панелей) */
QFrame#panelCard {
    background-color: #101014;
    border: 1px solid #222228;
    border-radius: 10px;
}

/* Скроллбары (QScrollBar) */
QScrollBar:vertical {
    border: none;
    background: #0c0c10;
    width: 7px;
    margin: 0px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #27272a;
    border-radius: 3px;
    min-height: 25px;
}

QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}

QScrollBar::horizontal {
    border: none;
    background: #0c0c10;
    height: 7px;
    margin: 0px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: #27272a;
    border-radius: 3px;
    min-width: 25px;
}

QScrollBar::handle:horizontal:hover {
    background: #3f3f46;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}

/* Подсказки (QToolTip) */
QToolTip {
    background-color: #18181b;
    color: #ffffff;
    border: 1px solid #3f3f46;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}

/* Диалоговые окна сообщений (QMessageBox) */
QMessageBox {
    background-color: #101014;
}

QMessageBox QLabel {
    color: #f4f4f5;
    font-size: 13px;
}
"""
